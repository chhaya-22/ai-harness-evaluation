from harness_eval.dataset import load_dataset
from harness_eval.harness import MockHarness
from harness_eval.runner import Runner

dataset = load_dataset("datasets/sample.json")
print(f"loaded {len(dataset)} cases")

runner = Runner(MockHarness(seed=7), repeats=5)
result = runner.run(dataset)

for cr in result.case_results:
    print(f"\n[{cr.case.id}]  ({cr.case.category})")
    for m in cr.metrics:
        print(f"   {m.metric:<18} {m.score:.3f}")

from harness_eval.scorer import score_run, recommend

report = score_run(result)
print(f"\nOVERALL: {report.overall_score}")
for s in report.metric_summaries:
    print(f"   {s.metric:<18} mean={s.mean_score:.3f}  weight={s.weight}")
print("\nRecommendations:")
for t in recommend(report):
    print("  -", t)

from harness_eval import reporter

reporter.to_json(report, "reports/sample_report.json")
reporter.to_markdown(report, "reports/sample_report.md")
reporter.to_html(report, "reports/sample_report.html")
print("\nReports written to reports/")    