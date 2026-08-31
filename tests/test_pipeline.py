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