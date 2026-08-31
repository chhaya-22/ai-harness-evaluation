from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class FailureRateMetric(Metric):
    """Fraction of runs that errored (timeout, exception, empty).

    Score is the success rate: 1.0 means every run returned cleanly.
    """

    name = "failure_rate"
    category = "reliability"

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        total = len(responses)
        if total == 0:
            return MetricResult(metric=self.name, score=0.0)
        failures = sum(1 for r in responses if not r.ok)
        success_rate = 1 - failures / total
        return MetricResult(
            metric=self.name,
            score=success_rate,
            value=round(failures / total, 3),
            details={"failures": failures, "total": total},
        )