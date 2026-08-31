from harness_eval.dataset import load_dataset
from harness_eval.harness import MockHarness
from harness_eval.runner import Runner
from harness_eval.scorer import score_run


def test_end_to_end_run(tmp_path):
    """Dataset -> runner -> scorer produces a valid overall score."""
    dataset_file = tmp_path / "d.json"
    dataset_file.write_text(
        '[{"id": "t1", "prompt": "hi", "expected": "hi"}]', encoding="utf-8"
    )

    cases = load_dataset(dataset_file)
    result = Runner(MockHarness(seed=1, fail_rate=0.0), repeats=3).run(cases)
    report = score_run(result)

    assert 0.0 <= report.overall_score <= 1.0
    assert len(result.case_results) == 1
    assert result.case_results[0].responses  # got responses back


def test_dataset_loader_rejects_non_list(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "a list"}', encoding="utf-8")
    try:
        load_dataset(bad)
        assert False, "should have raised"
    except ValueError:
        pass

def test_regression_detected_on_score_drop():
    from harness_eval.regression import detect_regression
    baseline = {"run_id": "b", "overall_score": 0.9,
                "metrics": {"correctness": 1.0, "latency": 0.9}}
    candidate = {"run_id": "c", "overall_score": 0.6,
                 "metrics": {"correctness": 0.5, "latency": 0.9}}
    report = detect_regression(baseline, candidate)
    assert report.has_regression
    assert report.verdict == "REGRESSION"


def test_no_regression_when_stable():
    from harness_eval.regression import detect_regression
    baseline = {"run_id": "b", "overall_score": 0.9,
                "metrics": {"correctness": 1.0, "latency": 0.9}}
    candidate = {"run_id": "c", "overall_score": 0.91,
                 "metrics": {"correctness": 1.0, "latency": 0.92}}
    report = detect_regression(baseline, candidate)
    assert not report.has_regression
    assert report.verdict == "OK"        