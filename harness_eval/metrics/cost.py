from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class CostMetric(Metric):
    """Average USD cost per call, normalised against a budget.

    Cost isn't inherently good or bad, so we score it relative to a target
    budget: at/under budget -> 1.0, at/over the ceiling -> 0.0.
    """

    name = "cost"
    category = "efficiency"
    higher_is_better = False

    budget_usd = 0.002    # per call, scores 1.0 at or under
    ceiling_usd = 0.02    # per call, scores 0.0 at or over

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        ok = [r for r in responses if r.ok]
        if not ok:
            return MetricResult(metric=self.name, score=0.0, details={"note": "no successful runs"})

        avg = sum(r.cost_usd for r in ok) / len(ok)
        norm = 1 - (avg - self.budget_usd) / (self.ceiling_usd - self.budget_usd)
        norm = max(0.0, min(1.0, norm))
        avg_tokens = sum(r.input_tokens + r.output_tokens for r in ok) / len(ok)
        return MetricResult(
            metric=self.name,
            score=norm,
            value=round(avg, 6),
            details={"avg_cost_usd": round(avg, 6), "avg_tokens": round(avg_tokens, 1)},
        )