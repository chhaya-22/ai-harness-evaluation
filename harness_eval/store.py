from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .scorer import ScoreReport, recommend

DEFAULT_DIR = Path("results")


def save_run(report: ScoreReport, results_dir: str | Path = DEFAULT_DIR) -> Path:
    """Persist one evaluation as a timestamped JSON file.

    Simple file-per-run storage: easy to inspect, diff and version. A real
    deployment might swap this for a database, but the interface (save/list/
    load) would stay the same.
    """
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_id = f"{ts}_{report.harness_name}"
    payload = {
        "run_id": run_id,
        "harness": report.harness_name,
        "overall_score": report.overall_score,
        "metrics": {s.metric: round(s.mean_score, 4) for s in report.metric_summaries},
        "failed_cases": report.failed_cases,
        "recommendations": recommend(report),
    }
    path = results_dir / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def list_runs(results_dir: str | Path = DEFAULT_DIR) -> list[dict]:
    """Return a summary of every stored run, newest first."""
    results_dir = Path(results_dir)
    if not results_dir.exists():
        return []
    runs = []
    for f in sorted(results_dir.glob("*.json"), reverse=True):
        data = json.loads(f.read_text(encoding="utf-8"))
        runs.append({
            "run_id": data["run_id"],
            "harness": data["harness"],
            "overall_score": data["overall_score"],
        })
    return runs


def load_run(run_id: str, results_dir: str | Path = DEFAULT_DIR) -> dict:
    path = Path(results_dir) / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"run not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))