from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .scorer import ScoreReport, recommend


def _report_dict(report: ScoreReport) -> dict:
    """Single source of truth: every format is built from this dict."""
    return {
        "harness": report.harness_name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_score": report.overall_score,
                "metrics": [
            {
                "metric": s.metric,
                "mean_score": round(s.mean_score, 4),
                "ci_half_width": round(s.ci_half_width, 4),
                "weight": s.weight,
            }
            for s in report.metric_summaries
        ],
        "failed_cases": report.failed_cases,
        "recommendations": recommend(report),
    }


def to_json(report: ScoreReport, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(_report_dict(report), indent=2), encoding="utf-8")
    return path


def to_markdown(report: ScoreReport, path: str | Path) -> Path:
    d = _report_dict(report)
    lines = [
        f"# Harness Evaluation Report — `{d['harness']}`",
        "",
        f"**Generated:** {d['generated_at']}  ",
        f"**Overall score:** {d['overall_score']:.4f}",
        "",
        "## Metric breakdown",
        "",
               "| Metric | Mean score | 95% CI | Weight |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {m['metric']} | {m['mean_score']:.3f} | ±{m['ci_half_width']:.3f} | {m['weight']} |"
        for m in d["metrics"]
    ]

    lines += ["", "## Failed cases", ""]
    if d["failed_cases"]:
        for f in d["failed_cases"]:
            weak = ", ".join(f"{k}={v}" for k, v in f["weak_metrics"].items())
            lines.append(f"- **{f['case_id']}** ({f['category']}): {weak}")
    else:
        lines.append("_None — no case scored below 0.5 on any metric._")

    lines += ["", "## Recommendations", ""]
    lines += [f"- {t}" for t in d["recommendations"]]

    text = "\n".join(lines) + "\n"
    path = Path(path)
    path.write_text(text, encoding="utf-8")
    return path


def to_html(report: ScoreReport, path: str | Path) -> Path:
    d = _report_dict(report)
    rows = "\n".join(
        f"<tr><td>{m['metric']}</td><td>{m['mean_score']:.3f}</td>"
        f"<td>&plusmn;{m['ci_half_width']:.3f}</td><td>{m['weight']}</td></tr>"
        for m in d["metrics"]
    )
    if d["failed_cases"]:
        failed = "<ul>" + "".join(
            f"<li><b>{f['case_id']}</b> ({f['category']}): "
            + ", ".join(f"{k}={v}" for k, v in f["weak_metrics"].items())
            + "</li>"
            for f in d["failed_cases"]
        ) + "</ul>"
    else:
        failed = "<p><em>None — no case scored below 0.5 on any metric.</em></p>"
    recs = "".join(f"<li>{t}</li>" for t in d["recommendations"])
    score_pct = d["overall_score"] * 100

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Harness Evaluation — {d['harness']}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 780px; margin: 2rem auto; color: #1a1a1a; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .meta {{ color: #666; font-size: 0.9rem; }}
  .score {{ font-size: 2.4rem; font-weight: 700; margin: 1rem 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #f4f4f4; }}
  .bar {{ background: #eee; border-radius: 4px; height: 12px; overflow: hidden; }}
  .bar > span {{ display: block; height: 100%; background: #3b82f6; width: {score_pct:.1f}%; }}
</style>
</head>
<body>
  <h1>Harness Evaluation Report</h1>
  <p class="meta">Harness: <b>{d['harness']}</b> &middot; Generated {d['generated_at']}</p>
  <div class="score">{d['overall_score']:.4f}</div>
  <div class="bar"><span></span></div>
  <h2>Metric breakdown</h2>
  <table>
    <tr><th>Metric</th><th>Mean score</th><th>95% CI</th><th>Weight</th></tr>
    {rows}
  </table>
  <h2>Failed cases</h2>
  {failed}
  <h2>Recommendations</h2>
  <ul>{recs}</ul>
</body>
</html>
"""
    path = Path(path)
    path.write_text(html, encoding="utf-8")
    return path