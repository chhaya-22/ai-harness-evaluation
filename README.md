# AI Harness Evaluation Framework

A framework for measuring and benchmarking the effectiveness of an AI harness —
the orchestration layer around prompts, models, tools, and retries. The goal is
not to build a harness, but to answer a harder question: *is a given harness any
good, and where does it break?*

The framework runs a harness against a dataset of test cases, scores each
response across seven dimensions, and produces an overall score plus a report
with failed cases and actionable recommendations.

## Why these metrics

A harness can fail in more than one way, so a single "accuracy" number hides too
much. I evaluate across seven dimensions, grouped by what they tell you:

- **Correctness** — does the output match the expected answer? Uses fuzzy string
  matching rather than exact equality, because LLM text varies in casing and
  whitespace even when it's right. For open-ended tasks this is the metric I'd
  extend first (semantic similarity or LLM-as-judge).
- **Consistency** — run the same input `k` times and measure how often the
  output agrees with itself. LLMs are stochastic; a harness that's right once
  but different every time isn't reliable. This is the metric most naive
  evaluations skip, and often the most revealing.
- **Failure rate** — fraction of runs that error, time out, or return empty. A
  fast, cheap harness that fails 20% of the time is not usable.
- **Latency** — reported as p95, not mean. Tail latency is what real users feel;
  the mean hides the slow requests.
- **Cost & token usage** — average cost per call, scored against a budget. Cost
  isn't good or bad on its own, so it's scored relative to a target.
- **Structured output** — for cases that must return JSON, checks the output
  parses and contains the required keys.
- **Tool calling** — for cases that should trigger tools, checks the harness
  called the ones it was supposed to.

Each metric normalises to a 0–1 score (higher is better) so they can combine
into one weighted overall score, while keeping the raw measured value for
transparency. The weights (in `scorer.py`) prioritise correctness and
reliability over cost and latency — a harness that's cheap but wrong scores
worse than one that's correct but slow. Weights are configurable per use case.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

Run an evaluation on a dataset:

```powershell
python -m harness_eval.cli run --dataset datasets/sample.json
```

List past runs:

```powershell
python -m harness_eval.cli list
```

Compare two runs metric by metric:

```powershell
python -m harness_eval.cli compare <run_id_1> <run_id_2>
```

Generate JSON + Markdown + HTML reports:

```powershell
python -m harness_eval.cli report --dataset datasets/sample.json --out reports/report
```

## Adding your own harness

The framework evaluates anything that implements the `Harness` interface.
Subclass it, wrap your real system inside `run()`, and register it in the CLI:

```python
class MyHarness(Harness):
    name = "my_harness"

    def run(self, case: TestCase) -> HarnessResponse:
        # call your real prompt/model/tool stack here
        ...
        return HarnessResponse(output=..., latency_s=..., ...)
```

## Adding your own metric

Drop a new file in `metrics/`, subclass `Metric`, and decorate it with
`@register`. The runner picks it up automatically — no other file changes.

```python
@register
class MyMetric(Metric):
    name = "my_metric"
    category = "quality"

    def score(self, case, responses):
        return MetricResult(metric=self.name, score=...)
```

## Adding your own dataset

Datasets are plain JSON lists of test cases — no code changes needed. Each case
supports an expected answer, an output schema, and expected tool calls, all
optional:

```json
[
  {
    "id": "example",
    "prompt": "What is the capital of France?",
    "category": "factual_qa",
    "expected": "Paris"
  }
]
```

## Running the tests

```powershell
pytest
```

## Project structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design, component flow, and
trade-offs.

## Deliverables map

- **Source code** — `harness_eval/`
- **Sample dataset** — `datasets/sample.json`
- **Sample reports** — `reports/`
- **Architecture docs** — `ARCHITECTURE.md`
- **Tests** — `tests/`