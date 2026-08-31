import numpy as np

from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class LatencyMetric(Metric):
    name = "latency"
    category = "performance"
    higher_is_better = False

    good_s = 1.0   # at or under this -> score 1.0
    bad_s = 10.0   # at or over this  -> score 0.0

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        lat = [r.latency_s for r in responses if r.ok]
        if not lat:
            return MetricResult(metric=self.name, score=0.0, details={"note": "no successful runs"})
        p50, p95 = (float(np.percentile(lat, q)) for q in (50, 95))
        norm = 1 - (p95 - self.good_s) / (self.bad_s - self.good_s)
        norm = max(0.0, min(1.0, norm))
        return MetricResult(
            metric=self.name,
            score=norm,
            value=round(p95, 3),
            details={"p50_s": round(p50, 3), "p95_s": round(p95, 3)},
        )