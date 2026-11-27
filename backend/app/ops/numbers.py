"""Numbers as `Decimal`, never float (P7.5): `1,234.50`, `1.234,50`, `١٢٣`, `(100)`.

When both `,` and `.` appear, the last one is the decimal mark. A lone `,` is a thousands mark
only in the `1,234` pattern; otherwise it's the decimal mark (`12,5`). Arabic-Indic and Persian
digits and the Arabic separators are read too. Empty and `NaN` are missing (None).
"""

import re
from decimal import Decimal

DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬", "01234567890123456789.,")
NUMBER = re.compile(r"-?\d+(\.\d+)?")


def _plain(text: str) -> str:
    if "," in text and "." in text:
        thousands = "," if text.rindex(".") > text.rindex(",") else "."
        return text.replace(thousands, "").replace(",", ".")
    if "," in text:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", text):
            return text.replace(",", "")
        return text.replace(",", ".") if text.count(",") == 1 else text
    if text.count(".") > 1 and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", text):
        return text.replace(".", "")
    return text


def read_decimal(text: str) -> Decimal | None:
    """The number, None when missing, or `ValueError` when it isn't a number."""
    value = text.strip().translate(DIGITS)
    if value == "" or value.lower() == "nan":
        return None
    negative = value.startswith("(") and value.endswith(")")
    plain = _plain(value[1:-1] if negative else value)
    if not NUMBER.fullmatch(plain):
        raise ValueError(f"not a number: {text!r}")
    return -Decimal(plain) if negative else Decimal(plain)
