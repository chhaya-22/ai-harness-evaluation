from __future__ import annotations

import math


def mean_and_ci(values: list[float], confidence: float = 0.95) -> tuple[float, float]:
    """Return (mean, half-width of the confidence interval).

    Uses the standard error of the mean with a normal approximation
    (z = 1.96 for 95%). With few samples this is a rough guide, not a rigorous
    t-test — but it's enough to show whether a score is stable or noisy, which
    is the decision we actually care about.
    """
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    if n == 1:
        return mean, 0.0

    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    std_err = math.sqrt(variance) / math.sqrt(n)
    z = 1.96 if confidence == 0.95 else 1.64  # 95% or 90%
    return mean, z * std_err