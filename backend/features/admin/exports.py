"""CSV helpers for the admin exports."""

import csv
import io
from collections.abc import Iterable, Sequence

# A cell starting with one of these can run as a formula when the CSV is opened in
# Excel ("CSV injection"), so we put a quote in front of it.
_DANGEROUS_START = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_DANGEROUS_START) else text


def to_csv(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([csv_safe(cell) for cell in row])
    return buffer.getvalue()
