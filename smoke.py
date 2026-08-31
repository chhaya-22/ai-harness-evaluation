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