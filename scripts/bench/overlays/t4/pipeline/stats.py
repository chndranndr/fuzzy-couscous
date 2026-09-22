"""Weighted statistics."""


def weighted_mean(values, weights):
    """Weighted arithmetic mean of *values* with *weights*.

    Weights must be non-negative. A weight set that sums to zero is
    rejected. Values and weights must have the same length.
    """
    if len(values) != len(weights):
        raise ValueError("values and weights must have the same length")
    total = sum(v * w for v, w in zip(values, weights))
    return total / sum(weights)
