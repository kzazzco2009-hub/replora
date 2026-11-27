"""Dates (P7.5): ISO, or day/month/year with the order read from the column, never guessed.

`25/04/2026` proves day-first and `04/25/2026` month-first. If every value in a column could be
either (`03/04/2026`), the column is ambiguous: the run asks which (DMY or MDY) instead of
guessing. Values are returned as ISO `YYYY-MM-DD`.
"""

import re
from datetime import date

ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
NUMERIC = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})")
ORDERS = ["DMY", "MDY"]


def _iso(year: str, month: str, day: str) -> str:
    return date(int(year), int(month), int(day)).isoformat()


def read_dates(values: list[str], order: str | None = None) -> tuple[list[str] | None, list | None]:
    """`(ISO values, None)`, or `(None, the orders to choose from)`; `ValueError` if unreadable."""
    numeric = [NUMERIC.fullmatch(v.strip()) for v in values if v.strip() and not ISO.fullmatch(v)]
    if None in numeric:
        raise ValueError("not a date")
    if order is None and numeric:
        firsts = any(int(m[1]) > 12 for m in numeric)
        seconds = any(int(m[2]) > 12 for m in numeric)
        if firsts and seconds:
            raise ValueError("mixed date orders")
        if not (firsts or seconds):
            return None, ORDERS
        order = "DMY" if firsts else "MDY"
    out = []
    for value in values:
        text = value.strip()
        if not text:
            out.append("")
        elif iso := ISO.fullmatch(text):
            out.append(_iso(*iso.groups()))
        else:
            first, second, year = NUMERIC.fullmatch(text).groups()
            day, month = (first, second) if order == "DMY" else (second, first)
            out.append(_iso(year, month, day))
    return out, None
