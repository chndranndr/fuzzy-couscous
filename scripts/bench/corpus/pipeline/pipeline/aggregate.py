"""Aggregations over parsed values."""


def mean(values):
    """Arithmetic mean; raises ValueError for an empty sequence."""
    if not values:
        raise ValueError("mean of an empty sequence is undefined")
    return sum(values) / len(values)
