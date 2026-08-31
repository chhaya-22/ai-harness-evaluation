from __future__ import annotations

from dataclasses import dataclass

# A metric that drops by more than this counts as a regression. Small dips are
# noise (harnesses are stochastic); we only flag drops big enough to matter.
DEFAULT_THRESHOLD = 0.05


@dataclass
class MetricDelta:
    metric: str
    baseline: float
    candidate: float
    delta: float
    is_regression: bool


@dataclass
class RegressionReport:
    baseline_id: str
    candidate_id: str
    overall_delta: float
    deltas: list[MetricDelta]
    threshold: float

    @property
    def has_regression(self) -> bool:
        return any(d.is_regression for d in self.deltas)

    @property
    def verdict(self) -> str:
        return "REGRESSION" if self.has_regression else "OK"


def detect_regression(
    baseline: dict,
    candidate: dict,
    threshold: float = DEFAULT_THRESHOLD,
) -> RegressionReport:
    """Compare a candidate run against a baseline and flag metric regressions.

    baseline and candidate are the stored run dicts (from store.load_run).
    A metric is a regression if its score dropped by more than `threshold`.
    """
    deltas: list[MetricDelta] = []
    for metric, base_score in baseline["metrics"].items():
        cand_score = candidate["metrics"].get(metric, 0.0)
        delta = cand_score - base_score
        deltas.append(MetricDelta(
            metric=metric,
            baseline=base_score,
            candidate=cand_score,
            delta=round(delta, 4),
            is_regression=delta < -threshold,
        ))

    deltas.sort(key=lambda d: d.delta)  # worst drops first
    overall_delta = candidate["overall_score"] - baseline["overall_score"]
    return RegressionReport(
        baseline_id=baseline["run_id"],
        candidate_id=candidate["run_id"],
        overall_delta=round(overall_delta, 4),
        deltas=deltas,
        threshold=threshold,
    )