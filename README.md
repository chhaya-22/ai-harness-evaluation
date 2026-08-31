# AI Harness Evaluation Framework

An AI harness is the layer that ties together prompts, models, tools, and
retries. This framework doesn't build a harness — it measures how good one
actually is, and shows where it falls short.

It runs a harness against a set of test cases, scores each response across seven
dimensions, and produces a report with an overall score, the cases that failed,
confidence intervals, and suggestions on what to fix.

## Why these metrics

An AI harness can go wrong in many different ways, so putting everything into
one "accuracy" score hides too much. I picked seven dimensions, each answering a
different question about the harness:

- **Correctness** — is the answer actually right? I compare the output to the
  expected answer, but I don't check for an exact match, because an LLM can be
  correct while still differing in casing or spacing. So I use fuzzy string
  matching instead. For open-ended answers this is the first thing I'd improve,
  probably with semantic similarity or an LLM acting as a judge.
- **Consistency** — does the harness give the same answer if I ask the same
  thing again? LLMs are random by nature, so I run each prompt several times and
  measure how often the outputs agree. A harness that's right once but different
  every time isn't something you can depend on. Most simple evaluations skip
  this, but I found it's often the most telling metric.
- **Failure rate** — how often does a run break, time out, or come back empty? A
  harness can be fast and cheap and still be useless if it fails one out of
  every five times.
- **Latency** — I report the p95 (95th percentile), not the average. The average
  hides the slow requests, and it's the slow ones that users actually notice.
- **Cost and tokens** — the average cost per call. Cost isn't good or bad on its
  own, so I score it against a target budget instead of in absolute terms.
- **Structured output** — for cases that are supposed to return JSON, I check
  that the output actually parses and has the keys it's meant to have.
- **Tool calling** — for cases that should trigger a tool, I check whether the
  harness actually called the right one.

Every metric is scaled to a 0–1 score where higher is better, so they can be
combined into a single overall score but I keep the raw number too, so nothing
is hidden. The weights live in `scorer.py` and lean towards correctness and
reliability over cost and speed, because a harness that's cheap but wrong is worse than one that's correct but a bit slow. The weights can be changed for a different use case.

Since each case is run several times, every metric also comes with a 95% confidence interval that way you can tell whether a score is solid or just noisy.

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

Run against the deliberately weaker harness (useful for demos):

```powershell
python -m harness_eval.cli run --dataset datasets/hard_cases.json --harness flawed
```

List past runs:

```powershell
python -m harness_eval.cli list
```

Compare two runs metric by metric:

```powershell
python -m harness_eval.cli compare <run_id_1> <run_id_2>
```

Check whether a candidate run regressed against a baseline:

```powershell
python -m harness_eval.cli regression <baseline_id> <candidate_id>
```

Show how a harness's score has changed over time:

```powershell
python -m harness_eval.cli trend --harness mock
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

You can see all registered metrics with `python -m harness_eval.cli list-metrics`,
and `python -m harness_eval.cli register-metric` explains how to add one.
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

Tests also run automatically on every push via GitHub Actions (see
`.github/workflows/ci.yml`).

## Beyond the core requirements

Alongside the required metrics and reporting, the framework includes:

- **Parallel execution** — cases run through a thread pool, since harness calls
  are I/O-bound.
- **Regression detection** — flags any metric that drops beyond a threshold
  between two runs, and exits non-zero so it can gate a CI pipeline.
- **Historical trend analysis** — tracks a harness's score across all stored
  runs and reports whether it's improving, stable, or declining.
- **Statistical significance** — 95% confidence intervals on every metric, so a
  stable score can be told apart from a noisy one.
- **CI integration** — GitHub Actions runs the test suite and a CLI smoke test
  on every push.

## Project structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design, component flow, and
trade-offs.

## Deliverables map

- **Source code** — `harness_eval/`
- **Sample datasets** — `datasets/sample.json`, `datasets/hard_cases.json`
- **Sample reports** — `reports/`
- **Architecture docs** — `ARCHITECTURE.md`
- **Tests** — `tests/`