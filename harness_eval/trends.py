from __future__ import annotations

from dataclasses import dataclass

from .store import list_runs, load_run


@dataclass
class TrendPoint:
    run_id: str
    overall_score: float
    metrics: dict[str, float]


@dataclass
class TrendReport:
    harness: str
    points: list[TrendPoint]

    @property
    def direction(self) -> str:
        """Overall movement from the first recorded run to the latest."""
        if len(self.points) < 2:
            return "insufficient data"
        delta = self.points[-1].overall_score - self.points[0].overall_score
        if delta > 0.01:
            return "improving"
        if delta < -0.01:
            return "declining"
        return "stable"


def build_trend(harness: str) -> TrendReport:
    """Collect every stored run for one harness, oldest to newest.

    Runs are stored with a timestamped id, so sorting by id gives chronological
    order. This turns the run history into a trend line without any extra
    bookkeeping — the storage layer already keeps everything we need.
    """
    runs = [r for r in list_runs() if r["harness"] == harness]
    runs.sort(key=lambda r: r["run_id"])  # timestamp prefix => chronological

    points: list[TrendPoint] = []
    for r in runs:
        full = load_run(r["run_id"])
        points.append(TrendPoint(
            run_id=full["run_id"],
            overall_score=full["overall_score"],
            metrics=full["metrics"],
        ))
    return TrendReport(harness=harness, points=points)