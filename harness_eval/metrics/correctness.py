from difflib import SequenceMatcher

from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class CorrectnessMetric(Metric):
    """Compares output against the expected answer.

    Exact match is too brittle for LLM text (whitespace, casing, minor
    wording), so we fall back to a fuzzy string ratio. Cases without an
    expected answer are skipped, not penalised.
    """

    name = "correctness"
    category = "quality"

    threshold = 0.85  # ratio at/above this counts as "correct"

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        if case.expected is None:
            return MetricResult(metric=self.name, score=1.0, details={"note": "no expected answer"})

        ok = [r for r in responses if r.ok]
        if not ok:
            return MetricResult(metric=self.name, score=0.0, details={"note": "no successful runs"})

        expected = case.expected.strip().lower()
        ratios = [
            SequenceMatcher(None, expected, r.output.strip().lower()).ratio()
            for r in ok
        ]
        passed = sum(1 for x in ratios if x >= self.threshold)
        return MetricResult(
            metric=self.name,
            score=passed / len(ratios),
            value=round(sum(ratios) / len(ratios), 3),
            details={"pass_rate": round(passed / len(ratios), 3), "threshold": self.threshold},
        )