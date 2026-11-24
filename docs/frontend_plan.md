# Replora — Frontend Track (Developer B)

The agreed frontend plan is the frontend package in **`docs/frontend/`**:

| File | Contents |
|---|---|
| `frontend/README.md` | Overview and how we work together |
| `frontend/plan.md` | Phases F0–F11 plus shared phases, steps, gates |
| `frontend/testing.md` | Frontend tests per phase (incl. T0.F1, T9.U1, T10.U1/U2, T12.U1) |
| `frontend/security.md` | Frontend security controls per phase |

`contracts/openapi.json` is generated from the FastAPI route stubs (handlers return 501) from B0, never hand-written (api_contract.md §0). Regenerate the types whenever it changes.
