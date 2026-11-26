"""P2.4 limits, checked before anything runs (T2.5, S-12). Boundaries are tested on both sides."""

from time import perf_counter

import pytest
from validator_samples import REGISTRY, codes, definition, edge, file_input, node

from app.core.limits import MAX_DEPTH, MAX_FAN_IN, MAX_FAN_OUT, MAX_NODES
from app.core.validator import validate
from app.core.workflow import ResourcePolicy

MiB = 1024 * 1024


def errors(defn, **kwargs):
    return validate(defn, REGISTRY, **kwargs).errors


def chain(length: int):
    names = [f"n{k}" for k in range(length)]
    edges = [edge(a, b) for a, b in zip(names, names[1:], strict=False)]
    return definition(map(node, names), edges)


def test_the_limits_are_the_planned_ones():
    assert (MAX_NODES, MAX_DEPTH, MAX_FAN_IN, MAX_FAN_OUT) == (30, 10, 10, 10)


@pytest.mark.parametrize(("count", "expected"), [(30, []), (31, ["LIMIT_NODES"])])
def test_node_count(count, expected):
    found = errors(definition(node(f"n{k}") for k in range(count)))
    assert [i.code for i in found] == expected
    if found:
        assert (found[0].path, found[0].params) == ("nodes", {"limit": 30, "actual": 31})


@pytest.mark.parametrize(("length", "expected"), [(10, []), (11, ["LIMIT_DEPTH"])])
def test_depth(length, expected):
    found = errors(chain(length))
    assert [i.code for i in found] == expected
    if found:
        assert found[0].params == {"limit": 10, "actual": 11}


def test_depth_is_not_measured_on_a_cycle():
    looped = chain(11)
    looped = looped.model_copy(update={"edges": [*looped.edges, edge("n10", "n0", "out", "in_1")]})
    assert codes(validate(looped, REGISTRY)) == ["DAG_CYCLE"]


@pytest.mark.parametrize(("sources", "expected"), [(10, []), (11, ["LIMIT_FAN_IN"])])
def test_fan_in(sources, expected):
    names = [f"s{k}" for k in range(sources)]
    edges = [edge(name, "sink", "out", f"in_{k}") for k, name in enumerate(names)]
    defn = definition([*map(node, names), node("sink")], edges)
    found = errors(defn)
    assert [i.code for i in found] == expected
    if found:
        assert (found[0].path, found[0].node_id) == (f"nodes/{sources}", "sink")
        assert found[0].params == {"limit": 10, "actual": 11}


@pytest.mark.parametrize(("targets", "expected"), [(10, []), (11, ["LIMIT_FAN_OUT"])])
def test_fan_out(targets, expected):
    names = [f"t{k}" for k in range(targets)]
    defn = definition([node("source"), *map(node, names)], [edge("source", n) for n in names])
    found = errors(defn)
    assert [i.code for i in found] == expected
    if found:
        assert (found[0].path, found[0].node_id) == ("nodes/0", "source")


def _inputs(count: int, max_files: int = 10):
    nodes = [node(f"p{k}", "parse_csv") for k in range(count)]
    inputs = [file_input(f"f{k}", f"p{k}") for k in range(count)]
    return definition(nodes, [], inputs, resource_policy=ResourcePolicy(max_files=max_files))


@pytest.mark.parametrize(("count", "expected"), [(2, []), (3, ["LIMIT_FILES"])])
def test_workflow_inputs_count_against_the_policy(count, expected):
    found = errors(_inputs(count, max_files=2))
    assert [i.code for i in found] == expected
    if found:
        assert (found[0].path, found[0].params) == ("inputs", {"limit": 2, "actual": 3})


@pytest.mark.parametrize(("files", "expected"), [(10, []), (11, ["LIMIT_FILES"])])
def test_bound_files_count_against_the_policy(files, expected):
    found = errors(_inputs(1), file_sizes=[1] * files)
    assert [i.code for i in found] == expected
    if found:
        assert found[0].path == "files"


@pytest.mark.parametrize(
    ("size", "expected"), [(50 * MiB, []), (50 * MiB + 1, ["LIMIT_FILE_SIZE"])]
)
def test_file_size_against_the_policy(size, expected):
    found = errors(_inputs(1), file_sizes=[1, size])
    assert [i.code for i in found] == expected
    if found:
        assert (found[0].path, found[0].params) == ("files/1", {"limit": 50 * MiB, "actual": size})


def test_a_stricter_policy_lowers_the_size_limit():
    defn = _inputs(1).model_copy(update={"resource_policy": ResourcePolicy(max_file_size=MiB)})
    assert [i.code for i in errors(defn, file_sizes=[MiB + 1])] == ["LIMIT_FILE_SIZE"]


def test_a_huge_definition_is_reported_quickly_and_never_raises():
    big = chain(5000)
    start = perf_counter()
    found = [i.code for i in errors(big)]
    assert perf_counter() - start < 2  # linear checks; about 0.2 s here
    assert found[:2] == ["LIMIT_NODES", "LIMIT_DEPTH"]
