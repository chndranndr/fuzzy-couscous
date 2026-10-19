"""Value parsing and normalization."""


def to_float(value):
    """Parse *value* into a float; blank cells become None."""
    text = str(value).strip()
    if text == "":
        return None
    return float(text)


def normalize_range(rows, index, lo=None, hi=None):
    """Return column *index* of *rows* as floats, optionally clipped.

    Blank cells are dropped (they are missing data, not zeros). Values are
    clipped into ``[lo, hi]`` when the bounds are given.
    """
    values = []
    for row in rows:
        parsed = to_float(row[index])
        if parsed is not None:
            values.append(parsed)
    if lo is not None:
        values = [max(lo, v) for v in values]
    if hi is not None:
        values = [min(hi, v) for v in values]
    return values
