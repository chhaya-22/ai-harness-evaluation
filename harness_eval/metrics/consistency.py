from collections import Counter

from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class ConsistencyMetric(Metric):
    name = "consistency"
    category = "reliability"

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        outs = [r.output.strip() for r in responses if r.ok]
        if len(outs) < 2:
            return MetricResult(metric=self.name, score=1.0, details={"note": "need >=2 runs"})
        _, count = Counter(outs).most_common(1)[0]
        agreement = count / len(outs)
        return MetricResult(
            metric=self.name,
            score=agreement,
            value=round(agreement, 3),
            details={"unique_outputs": len(set(outs)), "runs": len(outs)},
        )