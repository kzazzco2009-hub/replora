"""The codes operations give (P7.2): a failure's `params.error` in `NODE_FAILED`, or a warning.

Each one is listed in `contracts/error-codes.json` → `operation_codes`, and the frontend translates
it. A test checks that every code raised or reported under `app/ops` is listed here.
"""

from enum import StrEnum


class OperationCode(StrEnum):
    CSV_EMPTY = "CSV_EMPTY"
    CSV_DUPLICATE_HEADER = "CSV_DUPLICATE_HEADER"
    CSV_ROW_RAGGED = "CSV_ROW_RAGGED"
    JSON_INVALID = "JSON_INVALID"
    JSON_NOT_ARRAY = "JSON_NOT_ARRAY"
    JSON_EMPTY = "JSON_EMPTY"
    JSON_DUPLICATE_KEY = "JSON_DUPLICATE_KEY"
    JSON_TOO_DEEP = "JSON_TOO_DEEP"
    JSON_KEYS_MIXED = "JSON_KEYS_MIXED"
    ZIP_MEMBER_MISSING = "ZIP_MEMBER_MISSING"
    COLUMN_MISSING = "COLUMN_MISSING"
    COLUMN_CLASH = "COLUMN_CLASH"
    COLUMNS_DIFFER = "COLUMNS_DIFFER"
    NUMBER_INVALID = "NUMBER_INVALID"
    DATE_INVALID = "DATE_INVALID"
    DATE_AMBIGUOUS = "DATE_AMBIGUOUS"
    KEY_DUPLICATED = "KEY_DUPLICATED"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
