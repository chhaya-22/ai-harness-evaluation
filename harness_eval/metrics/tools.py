from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class ToolCallMetric(Metric):
    """Did the harness call the tools the case expected?

    Set-based comparison of expected vs actual tool names, averaged over
    runs. Cases with no expected tools are skipped.
    """

    name = "tool_calling"
    category = "quality"

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        if not case.expected_tools:
            return MetricResult(metric=self.name, score=1.0, details={"note": "no tools expected"})

        expected = set(case.expected_tools)
        ok = [r for r in responses if r.ok]
        if not ok:
            return MetricResult(metric=self.name, score=0.0, details={"note": "no successful runs"})

        scores = []
        for r in ok:
            actual = {t.name for t in r.tool_calls}
            scores.append(len(expected & actual) / len(expected))
        return MetricResult(
            metric=self.name,
            score=sum(scores) / len(scores),
            value=round(sum(scores) / len(scores), 3),
            details={"expected_tools": sorted(expected)},
        )