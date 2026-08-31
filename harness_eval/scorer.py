from __future__ import annotations

from dataclasses import dataclass, field

from .metrics.base import get_metric
from .runner import RunResult

# Weights reflect what matters most for a production harness. Correctness and
# reliability dominate; cost/latency matter but shouldn't outweigh a harness
# that returns wrong answers cheaply. Tune these per use case.
DEFAULT_WEIGHTS: dict[str, float] = {
    "correctness": 0.30,
    "failure_rate": 0.20,
    "consistency": 0.15,
    "structured_output": 0.10,
    "tool_calling": 0.10,
    "latency": 0.08,
    "cost": 0.07,
}


@dataclass
class MetricSummary:
    metric: str
    mean_score: float
    weight: float


@dataclass
class ScoreReport:
    harness_name: str
    overall_score: float
    metric_summaries: list[MetricSummary]
    failed_cases: list[dict] = field(default_factory=list)


def score_run(run: RunResult, weights: dict[str, float] | None = None) -> ScoreReport:
    """Collapse per-case metric results into one weighted overall score.

    Each metric is averaged across all cases, then combined using the weight
    table. Weights are renormalised so they always sum to 1, which keeps the
    overall score in 0..1 even if a metric is missing.
    """
    weights = weights or DEFAULT_WEIGHTS

    # Gather every metric's scores across all cases.
    by_metric: dict[str, list[float]] = {}
    for cr in run.case_results:
        for m in cr.metrics:
            by_metric.setdefault(m.metric, []).append(m.score)

    summaries: list[MetricSummary] = []
    weighted_sum = 0.0
    weight_total = 0.0
    for metric, scores in by_metric.items():
        mean = sum(scores) / len(scores)
        w = weights.get(metric, 0.0)
        summaries.append(MetricSummary(metric=metric, mean_score=mean, weight=w))
        weighted_sum += mean * w
        weight_total += w

    overall = weighted_sum / weight_total if weight_total else 0.0

    # Collect cases that failed any metric badly, for the report's failure list.
    failed: list[dict] = []
    for cr in run.case_results:
        weak = [m for m in cr.metrics if m.score < 0.5]
        if weak:
            failed.append({
                "case_id": cr.case.id,
                "category": cr.case.category,
                "weak_metrics": {m.metric: round(m.score, 3) for m in weak},
            })

    summaries.sort(key=lambda s: s.weight, reverse=True)
    return ScoreReport(
        harness_name=run.harness_name,
        overall_score=round(overall, 4),
        metric_summaries=summaries,
        failed_cases=failed,
    )


def recommend(report: ScoreReport) -> list[str]:
    """Turn low-scoring metrics into plain-language, actionable advice."""
    tips: list[str] = []
    for s in report.metric_summaries:
        if s.mean_score >= 0.8:
            continue
        meta = get_metric(s.metric)
        if s.metric == "latency":
            tips.append("High p95 latency: consider a faster model tier, caching, or shorter prompts.")
        elif s.metric == "cost":
            tips.append("Cost above budget: trim prompt tokens or route simple cases to a cheaper model.")
        elif s.metric == "consistency":
            tips.append("Low consistency: lower temperature or constrain outputs for deterministic tasks.")
        elif s.metric == "correctness":
            tips.append("Low correctness: revisit prompts/few-shot examples for the failing categories.")
        elif s.metric == "failure_rate":
            tips.append("Elevated failure rate: add retries/timeouts and inspect the error cases.")
        elif s.metric == "structured_output":
            tips.append("Schema violations: enforce JSON mode or validate-and-retry on parse failure.")
        elif s.metric == "tool_calling":
            tips.append("Missed tool calls: clarify tool descriptions or add examples of when to call them.")
        else:
            tips.append(f"Low {s.metric} ({s.mean_score:.2f}): investigate {meta.category} behaviour.")
    if not tips:
        tips.append("All metrics healthy (>=0.8 mean). No action needed.")
    return tips