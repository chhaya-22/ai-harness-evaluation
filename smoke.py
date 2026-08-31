from harness_eval.harness import MockHarness
from harness_eval.metrics.base import all_metrics, get_metric
from harness_eval.models import TestCase

case = TestCase(id="t1", prompt="capital of France?", expected="Paris")
h = MockHarness(seed=1)
responses = [h.run(case) for _ in range(5)]

print("metrics found:", all_metrics())
for name in all_metrics():
    print(get_metric(name).score(case, responses))