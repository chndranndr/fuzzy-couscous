"""CSV ingestion for the pipeline corpus."""

import csv


def read_records(path):
    """Read *path* and return ``(header, rows)``.

    ``rows`` is a list of raw string lists, one per data row, aligned with
    ``header``. The header row itself is not included in ``rows``; blank
    lines are skipped.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = [row for row in reader if row]
    return header, rows


def column_index(header, name):
    """Return the index of *name* in *header*; ValueError when absent."""
    return header.index(name)
