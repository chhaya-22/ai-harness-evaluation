from __future__ import annotations

import typer

from . import reporter
from .dataset import load_dataset
from .harness import MockHarness
from .runner import Runner
from .scorer import score_run
from .store import list_runs, load_run, save_run
from .harness import MockHarness, FlawedHarness

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


@app.command("list")
def list_cmd():
    """List all stored evaluation runs."""
    runs = list_runs()
    if not runs:
        typer.echo("No runs stored yet.")
        return
    for r in runs:
        typer.echo(f"{r['run_id']:<28} {r['harness']:<8} score={r['overall_score']}")


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