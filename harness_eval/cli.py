from __future__ import annotations

import typer

from . import reporter
from .dataset import load_dataset
from .harness import MockHarness
from .runner import Runner
from .scorer import score_run
from .store import list_runs, load_run, save_run
from .harness import MockHarness, FlawedHarness
from .regression import detect_regression
from .trends import build_trend
from .metrics.base import all_metrics, metric_info

app = typer.Typer(help="Evaluate and benchmark an AI harness.")

# Registry of harnesses the CLI knows how to build. Add real harnesses here.
HARNESSES = {
    "mock": lambda: MockHarness(seed=7),
    "flawed": lambda: FlawedHarness(seed=7),
}


@app.command()
def run(
    dataset: str = typer.Option(..., help="Path to a JSON dataset."),
    harness: str = typer.Option("mock", help="Harness name to evaluate."),
    repeats: int = typer.Option(5, help="Runs per case (for consistency/latency)."),
):
    """Run an evaluation and store the result."""
    if harness not in HARNESSES:
        typer.echo(f"Unknown harness '{harness}'. Available: {list(HARNESSES)}")
        raise typer.Exit(1)

    cases = load_dataset(dataset)
    result = Runner(HARNESSES[harness](), repeats=repeats).run(cases)
    report = score_run(result)
    path = save_run(report)

    typer.echo(f"Harness:  {report.harness_name}")
    typer.echo(f"Overall:  {report.overall_score}")
    typer.echo(f"Saved:    {path}")

@app.command()
def trend(harness: str = typer.Option("mock", help="Harness to show history for.")):
    """Show how a harness's overall score has changed across stored runs."""
    report = build_trend(harness)
    if not report.points:
        typer.echo(f"No stored runs for harness '{harness}'.")
        raise typer.Exit()

    typer.echo(f"Trend for '{report.harness}'  ({len(report.points)} runs) — {report.direction}\n")

    # Simple text sparkline: each run's score as a proportional bar.
    for p in report.points:
        bar = "█" * int(p.overall_score * 40)
        typer.echo(f"  {p.run_id:<26} {p.overall_score:.4f}  {bar}")

@app.command("list")
def list_cmd():
    """List all stored evaluation runs."""
    runs = list_runs()
    if not runs:
        typer.echo("No runs stored yet.")
        return
    for r in runs:
        typer.echo(f"{r['run_id']:<28} {r['harness']:<8} score={r['overall_score']}")


@app.command("list-metrics")
def list_metrics():
    """List every metric currently registered in the framework."""
    typer.echo(f"{len(all_metrics())} metrics registered:\n")
    for m in metric_info():
        direction = "higher is better" if m["higher_is_better"] else "lower is better"
        typer.echo(f"  {m['name']:<20} [{m['category']}]  ({direction})")


@app.command("register-metric")
def register_metric():
    """Explain how to add a custom metric to the framework.

    Metrics are auto-registered via a decorator, so 'registering' a metric
    means dropping a file into harness_eval/metrics/. This command shows how,
    and confirms what's currently loaded.
    """
    typer.echo("To register a new metric, add a file in harness_eval/metrics/ like:\n")
    typer.echo("    from .base import Metric, register\n")
    typer.echo("    @register")
    typer.echo("    class MyMetric(Metric):")
    typer.echo("        name = 'my_metric'")
    typer.echo("        category = 'quality'")
    typer.echo("        def score(self, case, responses):")
    typer.echo("            return MetricResult(metric=self.name, score=...)\n")
    typer.echo("Then import it in harness_eval/metrics/__init__.py.")
    typer.echo("The runner picks it up automatically — no other changes needed.\n")
    typer.echo(f"Currently registered: {', '.join(all_metrics())}")


@app.command()
def compare(run_a: str, run_b: str):
    """Compare two stored runs metric by metric."""
    a, b = load_run(run_a), load_run(run_b)
    typer.echo(f"{'metric':<18} {run_a:<20} {run_b:<20} delta")
    typer.echo(f"{'overall':<18} {a['overall_score']:<20} {b['overall_score']:<20} "
               f"{b['overall_score'] - a['overall_score']:+.4f}")
    for metric in a["metrics"]:
        av, bv = a["metrics"][metric], b["metrics"].get(metric, 0.0)
        typer.echo(f"{metric:<18} {av:<20} {bv:<20} {bv - av:+.4f}")


@app.command()
def regression(
    baseline: str,
    candidate: str,
    threshold: float = typer.Option(0.05, help="Max allowed score drop before flagging."),
):
    """Check whether a candidate run regressed against a baseline."""
    report = detect_regression(load_run(baseline), load_run(candidate), threshold)

    typer.echo(f"Baseline:  {report.baseline_id}")
    typer.echo(f"Candidate: {report.candidate_id}")
    typer.echo(f"Overall delta: {report.overall_delta:+.4f}")
    typer.echo(f"Verdict:   {report.verdict}\n")

    for d in report.deltas:
        flag = "  <-- REGRESSION" if d.is_regression else ""
        typer.echo(f"  {d.metric:<18} {d.baseline:.3f} -> {d.candidate:.3f}  ({d.delta:+.4f}){flag}")

    if report.has_regression:
        raise typer.Exit(1)  # non-zero exit so CI can catch regressions

@app.command()
def report(
    dataset: str = typer.Option(..., help="Path to a JSON dataset."),
    harness: str = typer.Option("mock", help="Harness name to evaluate."),
    out: str = typer.Option("reports/report", help="Output path prefix (no extension)."),
):
    """Run an evaluation and write JSON + Markdown + HTML reports."""
    cases = load_dataset(dataset)
    result = Runner(HARNESSES[harness](), repeats=5).run(cases)
    rep = score_run(result)
    reporter.to_json(rep, f"{out}.json")
    reporter.to_markdown(rep, f"{out}.md")
    reporter.to_html(rep, f"{out}.html")
    typer.echo(f"Reports written: {out}.json / .md / .html")


if __name__ == "__main__":
    app()