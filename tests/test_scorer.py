from harness_eval.models import HarnessResponse, TestCase
from harness_eval.runner import CaseResult, RunResult
from harness_eval.scorer import recommend, score_run


def make_run(metric_scores: dict[str, float]) -> RunResult:
    """Build a RunResult with one case whose metrics have the given scores."""
    from harness_eval.models import MetricResult
    case = TestCase(id="c", prompt="p")
    metrics = [MetricResult(metric=m, score=s) for m, s in metric_scores.items()]
    responses = [HarnessResponse(output="ok", latency_s=1.0)]
    cr = CaseResult(case=case, responses=responses, metrics=metrics)
    return RunResult(harness_name="test", repeats=1, case_results=[cr])


def test_overall_score_is_weighted_average():
    run = make_run({"correctness": 1.0, "failure_rate": 1.0, "consistency": 1.0,
                    "structured_output": 1.0, "tool_calling": 1.0,
                    "latency": 1.0, "cost": 1.0})
    report = score_run(run)
    assert report.overall_score == 1.0


def test_low_correctness_pulls_score_down():
    perfect = make_run({"correctness": 1.0, "latency": 1.0})
    broken = make_run({"correctness": 0.0, "latency": 1.0})
    assert score_run(broken).overall_score < score_run(perfect).overall_score


def test_failed_cases_are_collected():
    run = make_run({"correctness": 0.2, "latency": 1.0})
    report = score_run(run)
    assert len(report.failed_cases) == 1
    assert "correctness" in report.failed_cases[0]["weak_metrics"]


def test_recommendations_flag_weak_metric():
    run = make_run({"correctness": 0.3, "latency": 1.0})
    tips = recommend(score_run(run))
    assert any("correctness" in t.lower() for t in tips)


def test_recommendations_healthy_when_all_good():
    run = make_run({"correctness": 1.0, "latency": 1.0})
    tips = recommend(score_run(run))
    assert any("healthy" in t.lower() for t in tips)