from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .harness import Harness
from .metrics.base import all_metrics, get_metric
from .models import HarnessResponse, MetricResult, TestCase


@dataclass
class CaseResult:
    case: TestCase
    responses: list[HarnessResponse]
    metrics: list[MetricResult] = field(default_factory=list)


@dataclass
class RunResult:
    harness_name: str
    repeats: int
    case_results: list[CaseResult]


class Runner:
    """Executes a dataset against a harness and scores every metric.

    Each case is run `repeats` times so consistency and latency percentiles
    have a sample to work with. Runs are dispatched through a thread pool
    because harness calls are I/O-bound (network), so parallelism cuts wall
    time without touching the scoring logic.
    """

    def __init__(self, harness: Harness, repeats: int = 5, workers: int = 4):
        self.harness = harness
        self.repeats = repeats
        self.workers = workers

    def _run_case(self, case: TestCase) -> CaseResult:
        responses = [self.harness.run(case) for _ in range(self.repeats)]
        metrics = [get_metric(name).score(case, responses) for name in all_metrics()]
        return CaseResult(case=case, responses=responses, metrics=metrics)

    def run(self, dataset: list[TestCase]) -> RunResult:
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            case_results = list(pool.map(self._run_case, dataset))
        return RunResult(
            harness_name=self.harness.name,
            repeats=self.repeats,
            case_results=case_results,
        )