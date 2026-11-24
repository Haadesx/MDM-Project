"""Render the full accepted Cooperalink report with self-contained Plotly charts."""

import argparse
import os
import re
import sys
from base64 import b64encode
from datetime import date, timedelta
from html import escape
from math import floor
from pathlib import Path

from plotly.io import to_html
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cooperalink.artifacts import atomic_path, file_hash, read_json
from cooperalink.reporting import AUTHORS, TITLE, _read_csv, _report_blocks, _text
from research_report_charts import build_charts

RUN = ROOT / "outputs/research_top30_final"
PRESENTATION = ROOT / "outputs/research_top30_presentation/report.html"
FIGURES = {
    "observed_activity": "activity",
    "timeline": "timeline",
    "performance_by_origin": "performance",
    "ablation_by_origin": "paired",
    "reliability": "reliability",
}
ORDER = (
    "Abstract", "Results", "Paired average precision", "Prior activity strata", "Problem definition",
    "Data and coverage", "Methods and temporal protocol", "Baselines and metrics",
    "Diagnostics and limitations", "Reproducibility", "Response to TA feedback", "References",
)
NAV = {
    "Results": "Results",
    "Paired average precision": "Paired comparisons",
    "Data and coverage": "Data",
    "Methods and temporal protocol": "Methods",
    "Reproducibility": "Reproduce",
}


def sections_from(blocks):
    sections = {}
    for kind, *content in blocks:
        if kind == "heading":
            heading = content[0]
            sections[heading] = []
        elif sections:
            sections[heading].append((kind, *content))
    if set(sections) != set(ORDER):
        raise ValueError("The completed report sections changed. Review the presentation order.")
    return sections


def anchor(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def metric_ap(tables, window=False):
    name = "metrics_by_origin" if window else "metrics_summary"
    return [row for row in tables[name] if row["slice"] == "all_pairs"
            and row["metric"] == "average_precision" and row["value"]]


def cover(tables, manifest, completion):
    scores = {row["model_id"]: float(row["value"]) for row in metric_ap(tables)}
    graph, baseline, count_only = (scores[key] for key in
                                  ("timestral_graph", "persistence_binary", "timestral_count_only"))
    country_pairs = int(manifest["candidate_count"])
    origins = manifest["planned_test_origins"]
    score_count = country_pairs * len(origins) * len(manifest["models"])
    series = (
        ("arima", "ARIMA"), ("timestral_count_only", "Timestral count-only"),
        ("timestral_graph", "Timestral + graph"), ("persistence_binary", "Binary persistence"),
    )
    rows = {(row["model_id"], row["origin"]): float(row["value"])
            for row in metric_ap(tables, window=True)}
    bottom = floor(min(rows[model, col] for model, _ in series for col in origins) * 10) / 10
    matrix_rows = []
    for model, label in series:
        cells = []
        for origin in origins:
            number = rows[model, origin]
            shade = 21 + 57 * (number - bottom) / (1 - bottom)
            edge = 27 + 60 * (number - bottom) / (1 - bottom)
            tooltip = f"{label} · cutoff {origin} · AP {number:.4f}"
            cells.append(f'<span class="cell" style="--shade:{shade:.1f}%;--edge:{edge:.1f}%"'
                         f' title="{escape(tooltip)}"></span>')
        matrix_rows.append(f'<div class="matrix-row"><span>{escape(label)}</span>'
                           f'<div class="matrix-cells">{"".join(cells)}</div></div>')
    nav = "".join(f'<a href="#{anchor(name)}">{escape(label)}</a>' for name, label in NAV.items())
    start = date.fromisoformat(manifest["source_coverage"]["start"])
    end = date.fromisoformat(manifest["source_coverage"]["end_exclusive"]) - timedelta(days=1)
    headline, subtitle = TITLE.split(" in Temporal Event Networks ", 1)
    lower = f"{bottom:.1f}"
    return f"""
    <a class="skip" href="#abstract">Skip to report</a>
    <header class="cover">
      <div class="cover-inner">
        <div class="mast"><span>Cooperalink</span><span>Research report · {start.year}–{end.year}</span></div>
        <div class="cover-content">
          <div class="cover-copy">
            <p class="eyebrow">Rutgers course project · GDELT 2.0</p>
            <h1>{escape(headline)}
              <span class="title-subline">in Temporal Event Networks {escape(subtitle)}</span>
            </h1>
            <p class="byline">{escape(AUTHORS)}</p>
            <p class="framing">Forecasting whether a country pair has at least one new
              economic cooperation record in the next 30 days.</p>
          </div>
          <aside class="result-panel" aria-label="Held-out performance at a glance">
            <div class="panel-heading"><span>2024 held-out performance</span><span>Average precision</span></div>
            <div class="headline-score"><strong>{graph:.4f}</strong><span>Timestral + graph<br>macro average precision</span></div>
            <div class="deltas">
              <div><strong>{(graph - baseline) * 100:+.2f} pp</strong><span>vs binary persistence</span></div>
              <div><strong>{(graph - count_only) * 100:+.2f} pp</strong><span>vs count-only Timestral</span></div>
            </div>
            <div class="matrix" aria-hidden="true">
              {"".join(matrix_rows)}
              <div class="matrix-key"><span>Window order →</span><span>{lower}<i></i>1.0 AP</span></div>
            </div>
            <p class="panel-note">Each cell is one test window. Lighter cells indicate higher AP.</p>
          </aside>
        </div>
        <dl class="study-scope">
          <div><dt>Country pairs</dt><dd>{country_pairs:,}</dd></div>
          <div><dt>Held-out windows</dt><dd>{completion["completed_test_origins"]}</dd></div>
          <div><dt>Verified predictions</dt><dd>{score_count:,}</dd></div>
        </dl>
      </div>
    </header>
    <nav class="report-nav" aria-label="Report sections"><div>{nav}</div></nav>
    """


def protocol_timeline():
    roles = (
        ("2020", "Cohort", "Freeze the 30-country roster"),
        ("2021", "Fit", "Train topology candidates"),
        ("2022", "Select", "Choose regularization and refit"),
        ("2023", "Calibrate", "Fit four probability mappings"),
        ("2024", "Evaluate", "Score 12 held-out windows"),
    )
    steps = "".join(f'<li><span>{year}</span><strong>{role}</strong><p>{purpose}</p></li>'
                    for year, role, purpose in roles)
    return (
        '<figure class="viz timeline" aria-label="Registered research year roles">'
        '<div class="viz-heading"><h3>Each year has a separate role</h3>'
        '<p>The cohort and global fitted models stay fixed for the 2024 evaluation.</p></div>'
        f'<ol>{steps}</ol><figcaption>Registered research year roles from the fixed configuration.</figcaption>'
        '</figure>'
    )


def chart_block(key, charts, fallback=None):
    chart = charts[key]
    rendered = to_html(
        chart.figure, include_plotlyjs=False, full_html=False, div_id=f"chart-{key}",
        config={"responsive": True, "displayModeBar": False, "scrollZoom": False},
    )
    noscript = ""
    if fallback:
        encoded = b64encode(fallback.read_bytes()).decode("ascii")
        noscript = f'<noscript><img src="data:image/svg+xml;base64,{encoded}" alt="{escape(chart.title)}"></noscript>'
    return (
        f'<figure class="viz" aria-labelledby="title-{key}">'
        f'<div class="viz-heading"><h3 id="title-{key}">{escape(chart.title)}</h3>'
        f'<p>{escape(chart.subtitle)}</p></div><div class="plot">{rendered}</div>'
        f'{noscript}<figcaption>{escape(chart.caption)}</figcaption></figure>'
    )


def table_block(columns, rows):
    heading = "".join(f'<th scope="col">{escape(_text(value))}</th>' for value in columns)
    body = []
    for row in rows:
        label, *values = row
        cells = "".join(f"<td>{escape(_text(value))}</td>" for value in values)
        row_class = {
            "timestral_graph": ' class="model-graph"',
            "persistence_binary": ' class="model-persistence"',
            "arima": ' class="model-arima"',
        }.get(label, "")
        body.append(f'<tr{row_class}><th scope="row">{escape(_text(label))}</th>{cells}</tr>')
    table = (f'<div class="table-wrap" tabindex="0" role="region" aria-label="{escape(str(columns[0]))} table">'
             f'<table><thead><tr>{heading}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')
    labels = {"country_code": "Cohort selection table", "Cleaning audit": "Source cleaning audit",
              "model_id": "Model backend provenance", "Input identity": "Input fingerprints",
              "Environment": "Recorded hardware and software", "Completion": "Acceptance flags"}
    label = labels.get(columns[0])
    if columns[0] == "Origin":
        label = "Window-level values"
    if columns[:2] == ("Model", "Stratum"):
        label = "Stratum metrics and support counts"
    if label:
        return f'<details class="deferred-table"><summary>{label}<span>{len(rows)} rows</span></summary>{table}</details>'
    return table


def render_block(block, charts):
    kind, *content = block
    if kind == "table":
        return table_block(*content)
    if kind == "figure":
        _, path = content
        key = FIGURES[path.stem]
        return protocol_timeline() if key == "timeline" else chart_block(key, charts, path)
    if kind == "link":
        label, url = content
        return f'<p class="reference"><a href="{escape(url)}">{escape(label)}</a></p>'
    if kind == "code":
        return f'<pre><code>{escape(content[0])}</code></pre>'
    return f'<p>{escape(content[0])}</p>'


def render_report(run, destination):
    if destination.resolve().is_relative_to(run.resolve()):
        raise ValueError("Store the presentation outside the accepted run directory.")
    completion = read_json(run / "completion.json")
    manifest = read_json(run / "run_manifest.json")
    if completion["research_complete"] is not True or manifest["synthetic"]:
        raise ValueError("This presentation expects the completed research run.")
    for artifact in manifest["artifact_index"]:
        if file_hash(run / artifact["path"]) != artifact["sha256"]:
            raise ValueError(f"Run fingerprint mismatch for {artifact['path']}.")
    exports = read_json(run / "metric_exports_manifest.json")["files"]
    tables = {Path(name).stem: _read_csv(run / name) for name in exports}
    charts = build_charts(tables)
    figures = {stem: run / "figures" / f"{stem}.svg" for stem in FIGURES}
    blocks = _report_blocks(read_json(run / "resolved_config.json"), manifest, completion,
                            read_json(run / "environment.json"), tables, figures, manifest["run_id"], run)
    sections = sections_from(blocks)
    # Present the original data tables after their corresponding charts.
    for title in ("Data and coverage", "Paired average precision"):
        items = sections[title]
        position = next(i for i, block in enumerate(items) if block[0] == "table")
        items.insert(position, items.pop(next(i for i, block in enumerate(items) if block[0] == "figure")))
    sections["Results"].insert(0, ("plotly", "ranking"))
    sections["Prior activity strata"].insert(0, ("plotly", "strata"))
    article = []
    for title in ORDER:
        content = "".join(chart_block(block[1], charts) if block[0] == "plotly" else render_block(block, charts)
                          for block in sections[title])
        article.append(f'<section class="report-section" id="{anchor(title)}"><h2>{escape(title)}</h2>{content}</section>')
    css = (ROOT / "scripts/research_report.css").read_text()
    source_path = os.path.relpath(run / "metrics_summary.csv", destination.parent)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(TITLE)}</title><link rel="icon" href="data:,"><style>{css}</style><script>{get_plotlyjs()}</script></head>
<body>{cover(tables, manifest, completion)}
<main id="content" class="report-content">{"".join(article)}</main>
<footer><div><a href="#abstract">Back to report</a>
<a href="{escape(source_path)}">Download metrics summary CSV</a>
<span>Run {escape(manifest["run_id"])} · {escape(manifest["created_at"][:10])}</span>
<span>Figures rendered with <a href="https://plotly.com/python/">Plotly</a></span></div></footer>
</body></html>
"""
    with atomic_path(destination) as path:
        path.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PRESENTATION)
    args = parser.parse_args()
    render_report(RUN, args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
