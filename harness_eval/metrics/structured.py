import json

from ..models import HarnessResponse, MetricResult, TestCase
from .base import Metric, register


@register
class StructuredOutputMetric(Metric):
    """Checks that output is valid JSON with the required top-level keys.

    Only applies to cases that declare an output_schema; others are skipped.
    A lightweight check on purpose — full JSON-Schema validation would be
    the next step, but key-presence catches the common failures.
    """

    name = "structured_output"
    category = "quality"

    def score(self, case: TestCase, responses: list[HarnessResponse]) -> MetricResult:
        if not case.output_schema:
            return MetricResult(metric=self.name, score=1.0, details={"note": "no schema declared"})

        required = case.output_schema.get("required", [])
        ok = [r for r in responses if r.ok]
        if not ok:
            return MetricResult(metric=self.name, score=0.0, details={"note": "no successful runs"})

        valid = 0
        for r in ok:
            try:
                parsed = json.loads(r.output)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(parsed, dict) and all(k in parsed for k in required):
                valid += 1
        return MetricResult(
            metric=self.name,
            score=valid / len(ok),
            value=round(valid / len(ok), 3),
            details={"valid": valid, "checked": len(ok), "required_keys": required},
        )