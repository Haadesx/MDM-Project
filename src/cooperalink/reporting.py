"""Render reports and figures from the persisted metric exports."""

from base64 import b64encode
import csv
from datetime import date, timedelta
from html import escape
from math import fsum
from pathlib import Path
from shlex import quote

from .artifacts import atomic_path, file_hash, read_json, write_csv, write_json
from .domain import DataContractError

TITLE = "Forecasting International Economic Cooperation Links in Temporal Event Networks Using GDELT and Timestral"
AUTHORS = "Urvi Desai, Sinchana Arun, and Varesh Patel"
SYNTHETIC_BANNER = "SYNTHETIC SOFTWARE DEMONSTRATION - NOT RESEARCH RESULTS"
PERSISTENCE = "persistence_binary"
GRAPH = "timestral_graph"
COUNT_ONLY = "timestral_count_only"
EXPORT_INDEX = "metric_exports_manifest.json"
ROOT = Path(__file__).resolve().parents[2]


def write_evaluation(output, tables, config, manifest=None, completion=None):
    output = Path(output)
    activity = _observed_activity(output, tables["origin_activity"], config["temporal"]["horizon_days"])
    tables = {**tables, "origin_activity": activity}
    files = {}
    for name, rows in tables.items():
        path = output / f"{name}.csv"
        write_csv(path, rows)
        files[path.name] = file_hash(path)
    write_json(output / EXPORT_INDEX, {
        "synthetic": config["synthetic"],
        "banner": SYNTHETIC_BANNER if config["synthetic"] else None,
        "run_id": tables["metrics_by_origin"][0]["run_id"],
        "files": files,
    })
    render_report(output, config, manifest, completion)


def render_report(output, config, manifest=None, completion=None):
    """Regenerate presentation artifacts without fitting or recomputing metrics."""
    output = Path(output)
    manifest = manifest or _optional_json(output / "run_manifest.json")
    if completion is None:
        completion = _optional_json(output / "completion.json")
    environment = _optional_json(output / "environment.json")
    synthetic = config["synthetic"]
    index = _optional_json(output / EXPORT_INDEX)
    tables = {}
    if index:
        if index["synthetic"] is not synthetic or manifest.get("run_id", index["run_id"]) != index["run_id"]:
            raise DataContractError("Metric export provenance does not match this report")
        for name, expected_hash in index["files"].items():
            path = output / name
            if not path.is_file() or file_hash(path) != expected_hash:
                raise DataContractError(f"Could not verify metric export {name} hash")
            tables[path.stem] = _read_csv(path)
    run_id = index.get("run_id", manifest.get("run_id", output.name))
    figures = _figures(output, run_id, synthetic, tables) if tables else {}
    blocks = _report_blocks(config, manifest, completion, environment, tables, figures, run_id, output)
    markdown = _markdown(blocks, output)
    html = _html(blocks)
    for path, body in ((output / "report.md", markdown), (output / "report.html", html)):
        with atomic_path(path) as temp:
            temp.write_text(body, encoding="utf-8")


def _optional_json(path):
    return read_json(path) if path.is_file() else {}


def _read_csv(path):
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _observed_activity(output, activity, horizon):
    counts = {}
    if (output / "daily_counts.parquet").is_file():
        import pyarrow.parquet as pq

        daily = pq.read_table(output / "daily_counts.parquet", columns=["day", "count"])
        counts = {row["day"]: row["count_sum"] for row in daily.group_by("day").aggregate(
            [("count", "sum")]
        ).to_pylist()}
    coverage = {
        row["origin"]: row for row in _read_csv(output / "origins.csv") if row["role"] == "test"
    }
    export = []
    for row in activity:
        origin = date.fromisoformat(row["origin"])
        days = [(origin + timedelta(days=index)).isoformat() for index in range(1, horizon + 1)]
        fold = coverage.get(row["origin"], {})
        checked = (fold.get("history_complete", ""), fold.get("label_complete", ""))
        status = "unknown" if "" in checked else "complete" if checked == ("True", "True") else "incomplete"
        export.append({
            **row,
            "eligible_cohort_records": sum(counts[day] for day in days) if all(day in counts for day in days) else None,
            "coverage_status": status,
        })
    return export


def _report_blocks(config, manifest, completion, environment, tables, figures, run_id, output):
    synthetic = config["synthetic"]
    full_research = not synthetic and completion.get("research_complete") is True
    blocks = [("title", TITLE)]
    if synthetic:
        blocks.append(("banner", SYNTHETIC_BANNER))
    elif not full_research:
        blocks.append(("banner", "RESEARCH RUN INCOMPLETE"))

    blocks.append(("text", AUTHORS))
    recorded_at = manifest.get("created_at", "")[:10]
    date_text = f"Recorded {recorded_at}. " if recorded_at else ""
    blocks.append(("text", f"Rutgers course project. {date_text}Run {run_id}."))
    blocks.append(("heading", "Abstract"))
    blocks.append(("text", _abstract(synthetic, tables, completion)))
    blocks.extend([
        ("heading", "Problem definition"),
        ("text", "An economic-cooperation link is at least one distinct GDELT 2.0 event ID with "
         "exact CAMEO 061 for an unordered pair during UTC days T+1 through T+30. "
         "The endpoints are actor-country affiliations. Observations enter the history on their "
         "UTC DATEADDED day, with SQLDATE retained for audit."),
        ("text", "A negative is a candidate pair with zero qualifying records in a fully covered "
         "target window. Every selected pair is retained, including pairs with no previous record. "
         "Missing extraction coverage invalidates the affected origin."),
        ("heading", "Data and coverage"),
    ])

    if synthetic:
        pairs = config["cohort"].get("expected_pairs")
        blocks.append(("text", f"The offline fixture exercises {pairs} synthetic candidate pairs."))
    else:
        scope = manifest.get("source_coverage", {})
        if scope:
            blocks.append(("text", f"Extraction interval {scope['start']} through "
                           f"{scope['end_exclusive']} (exclusive). Coverage complete: "
                           f"{scope['complete']}. Evidence kind: {scope['evidence_kind']}."))
        blocks.append(("text", "The fixed cohort contains the top 30 countries by 2020 eligible "
                       "endpoint incidence, with ties resolved by code. Its 435 unordered pairs "
                       "appear at every test origin. Coverage describes the extraction from the "
                       "recorded source snapshot. News access and selection can still vary."))

    cohort = _read_csv(output / "cohort.csv")
    if cohort:
        columns = tuple(cohort[0])
        blocks.append(("table", columns, [tuple(row[field] for field in columns) for row in cohort]))
    audit = (manifest.get("cleaning_audit") or _optional_json(output / "cleaning_audit.json")
             or _optional_json(output / "source_audit.json"))
    if audit:
        blocks.append(("table", ("Cleaning audit", "Observed value"), sorted(audit.items())))
    if tables:
        blocks.append(("table", (
            "Origin", "Candidates", "Positives", "Negatives", "Positive prevalence",
            "Active last 30 days", "Eligible cohort records", "Extraction coverage",
        ), [(
            row["origin"], row["candidate_count"], row["positive_count"], row["negative_count"],
            _display(row["positive_prevalence"]), _display(row["activity_rate"]),
            row["eligible_cohort_records"], row["coverage_status"],
        ) for row in tables["origin_activity"]]))
        blocks.append(("figure", "Observed link prevalence and activity", figures["observed_activity"]))

    blocks.extend([
        ("heading", "Methods and temporal protocol"),
        ("text", "A rolling 30-day graph includes an edge for any recorded pair activity by each "
         "day's cutoff. Timestral-209M uses 90 daily count rows and, for the graph variant, "
         "historical Jaccard and preferential attachment. Graph aggregation extends raw input "
         "support to 119 days. The count-only variant uses 90 days of counts. Its comparison with "
         "the enriched variant reflects both topology and the larger effective raw history."),
        ("text", "2020 establishes the cohort. The topology logistic scaler and classifier train "
         "on 2021, select regularization by 2022 macro AP, and refit on both years. Four separate "
         "forecast-to-link logistic heads train on 2023 only. Pretrained Timestral inference is "
         "zero-shot and its forecast-to-link mapping is supervised. Frozen global artifacts score "
         "2024. ARIMA and Prophet may fit local rolling histories under their fixed specifications."),
        ("text", "The fixed calendar uses 12 full 30-day blocks starting January 1 of each evaluated "
         "year. The final five days of non-leap years and six days of leap years remain available "
         "as history after their observations mature."),
        ("heading", "Baselines and metrics"),
        ("text", "Binary persistence is 1 when the pair has a record from T−29 through T and 0 "
         "otherwise. Recent count and the graph scores use that same cutoff. ARIMA and Prophet "
         "repeat an observed constant history with an explicit constant-series status."),
        ("text", "Each metric is calculated by origin. Macro averages weight defined windows "
         "equally. Equal scores receive half credit in ROC-AUC and enter AP as a single threshold "
         "group. Precision uses expected hits across cutoff ties. Filtered MRR keeps each positive "
         "target and every negative, removes other same-origin positive targets, and averages "
         "reciprocal mean ranks across both endpoints."),
    ])
    if "timeline" in figures:
        blocks.append(("figure", "Registered research year roles", figures["timeline"]))
    provenance = manifest.get("models", [])
    if provenance:
        columns = ("model_id", "backend_kind", "status", "library", "version", "source_revision",
                   "weights_revision", "device", "dtype")
        blocks.append(("table", columns, [tuple(row.get(field) for field in columns) for row in provenance]))
    _append_results(blocks, tables, figures)

    blocks.extend([
        ("heading", "Diagnostics and limitations"),
        ("text", "Repeated records can describe the same real-world incident. New recorded "
         "activity can include old events and repeat interactions. An inactive pair may have "
         "interacted before the last 30 days. The top-30 cohort favors well-observed countries."),
        ("text", "Timestral was released in 2026, after the evaluation period. The study is "
         "retrospective and the extent of pretraining overlap is unknown. The numerical median "
         "forecast is a feature for supervised mapping. Empirical probability quality is assessed "
         "with Brier error and fixed reliability bins when probability outputs are available."),
        ("text", "The 12 planned test windows share countries and news conditions. The paired "
         "differences are descriptive measures from those windows."),
        ("heading", "Reproducibility"),
    ])
    _append_reproducibility(blocks, config, manifest, completion, environment, output)
    blocks.extend([
        ("heading", "Response to TA feedback"),
        ("table", ("Feedback", "Implemented definition", "Evidence"), [
            ("Define a link", "One exact-061 record per pair suffices in the next 30 recorded days.",
             "Target boundary and temporal contract tests."),
            ("Specify candidates", "Frozen 2020 top-30 roster and every unordered pair for the main experiment.",
             "Cohort and candidate artifacts, complete panel validation."),
            ("Explain negatives", "Zero qualifying records in a verified window. Retain the full panel.",
             "Coverage checks and origin-level positive and negative counts."),
            ("Include persistence", "Binary recent activity over T−29 through T.",
             "Persistence boundary tests, metric row and paired comparisons."),
        ]),
        ("heading", "References"),
        ("link", "GDELT Event Database v2.0 codebook", "https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf"),
        ("link", "CAMEO manual, version 1.1b3", "https://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf"),
        ("link", "Timestral-209M model card", "https://huggingface.co/mistralai/Timestral-209M"),
        ("link", "Official Timestral source", "https://github.com/mistralai/timestral"),
    ])
    return blocks


def _abstract(synthetic, tables, completion):
    if synthetic:
        return "This offline report verifies the data-to-metrics workflow with synthetic inputs."
    if not tables:
        blockers = completion.get("blockers", [])
        return "The fixed run is awaiting accepted scores." + (f" See {len(blockers)} recorded blockers below." if blockers else "")
    paired = [
        row for row in tables["paired_comparisons"]
        if row["model_id"] == GRAPH and row["reference_model_id"] == PERSISTENCE
        and row["metric"] == "average_precision" and row["difference"]
    ]
    if not paired:
        return "Average precision was undefined in every paired test window."
    differences = [float(row["difference"]) for row in paired]
    mean = fsum(differences) / len(differences)
    return (f"Timestral with graph covariates had a mean paired AP difference of {mean:+.4f} "
            f"against binary persistence over {len(differences)} defined windows. "
            f"Window differences ranged from {min(differences):+.4f} to {max(differences):+.4f}.")


def _append_results(blocks, tables, figures):
    blocks.append(("heading", "Results"))
    if not tables:
        blocks.append(("text", "No metric exports are available for this run."))
        return
    summaries = {
        (row["model_id"], row["slice"], row["metric"], row["requested_k"]): row
        for row in tables["metrics_summary"]
    }
    full_rows = [row for row in tables["metrics_summary"] if row["slice"] == "all_pairs"]
    k_values = dict.fromkeys(row["requested_k"] for row in full_rows if row["metric"] == "precision_at_k")
    metrics = [
        ("average_precision", "", "Macro AP"), ("roc_auc", "", "Macro ROC-AUC"),
        *(("precision_at_k", k, f"P@{k}") for k in k_values),
        ("filtered_mrr", "", "Filtered MRR"), ("brier_score", "", "Brier error"),
    ]
    table = []
    slice_table = []
    for info in tables["model_diagnostics"]:
        model = info["model_id"]
        results = [summaries.get((model, "all_pairs", name, k), {}) for name, k, _ in metrics]
        table.append((
            model, *(_display(row.get("value")) for row in results),
            f"{results[0]['valid_windows']}/{results[0]['evaluated_windows']}",
            f"{results[1]['valid_windows']}/{results[1]['evaluated_windows']}",
            info["candidate_rows"], info["failed_rows"], info["constant_shortcut_rows"],
            _display(info["runtime_seconds"], 2),
        ))
        for stratum in ("active_last_30", "inactive_last_30"):
            result = summaries[model, stratum, "average_precision", ""]
            slice_table.append((
                model, stratum, _display(result["value"]), result["valid_windows"],
                result["positive_rows"], result["candidate_rows"], result["undefined_reasons"],
            ))
    blocks.append(("table", (
        "Model", *(name for _, _, name in metrics), "AP windows", "AUC windows", "Scored rows",
        "Failures", "Constant shortcuts", "Runtime (s)",
    ), table))
    blocks.append(("text", "An em dash marks an undefined or unavailable value. Null reasons "
                   "and query supports are recorded by origin in metrics_by_origin.csv."))
    blocks.append(("figure", "Average precision by origin", figures["performance_by_origin"]))

    paired_ap = [row for row in tables["paired_comparisons"] if row["metric"] == "average_precision"]
    paired_main = [row for row in paired_ap if row["model_id"] == GRAPH]
    blocks.append(("heading", "Paired average precision"))
    blocks.append(("table", ("Origin", "Model", "Reference", "AP", "Reference AP", "Difference", "Sign"), [
        (row["origin"], row["model_id"], row["reference_model_id"], _display(row["value"]),
         _display(row["reference_value"]), _display(row["difference"]), row["sign"])
        for row in (paired_main or paired_ap)
    ]))
    if "ablation_by_origin" in figures:
        blocks.append(("figure", "Graph versus count-only paired AP", figures["ablation_by_origin"]))
    blocks.append(("heading", "Prior activity strata"))
    blocks.append(("table", ("Model", "Stratum", "Macro AP", "Valid windows", "Positives", "Scored rows", "Null reasons"), slice_table))
    if "reliability" in figures:
        blocks.append(("figure", "Reliability of scored link probabilities", figures["reliability"]))
        blocks.append(("text", "Fixed bins have width 0.1. Bin frequencies and observed link rates are in reliability.csv."))


def _append_reproducibility(blocks, config, manifest, completion, environment, output):
    identity_fields = (
        "config_sha256", "data_sha256", "country_registry_sha256", "cohort_sha256",
        "environment_lock_sha256",
    )
    identities = [(field, manifest[field]) for field in identity_fields if field in manifest]
    if identities:
        blocks.append(("table", ("Input identity", "SHA-256"), identities))
    if environment:
        blocks.append(("table", ("Environment", "Recorded value"), sorted(environment.items())))
    if completion:
        flags = ("engineering_complete", "demo_complete", "research_complete")
        blocks.append(("table", ("Completion", "Result"), [(name, completion.get(name)) for name in flags]))
        blockers = completion.get("blockers", [])
        if blockers:
            columns = ("stage", "code", "detail")
            blocks.append(("table", columns, [tuple(blocker[field] for field in columns) for blocker in blockers]))
    if config["synthetic"]:
        commands = "cooperalink demo --config config/demo.json" + (" --multiyear" if config.get("multi_year") else "")
    else:
        source = _optional_json(output / "run_request.json").get("input")
        input_arg = "data/input"
        if isinstance(source, str) and Path(source).is_absolute() and source.isprintable() and "://" not in source:
            input_arg = _shell_path(Path(source))
        # The CLI treats a single-component run selector as a name under outputs/.
        output_arg = _shell_path(output, require_parent=True)
        commands = "\n".join((
            f"cooperalink run --config config/research.json --input {input_arg} --output {output_arg}",
            f"cooperalink resume --run-id {output_arg}",
            f"cooperalink report --run-id {output_arg}",
        ))
    blocks.append(("code", commands))


def _shell_path(path, require_parent=False):
    absolute = path.resolve()
    if absolute.is_relative_to(ROOT):
        relative = absolute.relative_to(ROOT)
        if not require_parent or len(relative.parts) > 1:
            value = str(relative)
            return quote(f"./{value}" if value.startswith("-") else value)
    return quote(str(absolute))


def _display(value, digits=4):
    return f"{float(value):.{digits}f}" if value not in (None, "") else "—"


def _figures(output, run_id, synthetic, tables):
    from matplotlib import rc_context
    from matplotlib.backends.backend_svg import FigureCanvasSVG
    from matplotlib.figure import Figure

    figures = {}
    with rc_context({"svg.hashsalt": run_id, "svg.fonttype": "none", "font.size": 10}):
        def plot(name, title, panels=1):
            figure = Figure(figsize=(8.4, 4.0 * panels), layout="constrained")
            FigureCanvasSVG(figure)
            axes = figure.subplots(panels)
            figure.suptitle(title)
            footer = SYNTHETIC_BANNER if synthetic else f"Cooperalink | {run_id}"
            figure.supxlabel(footer, fontsize=8, color="#905300" if synthetic else "#444444")
            path = output / "figures" / f"{name}.svg"
            figures[name] = path
            return figure, axes, path

        def save(figure, path, title):
            with atomic_path(path) as temp:
                figure.savefig(temp, format="svg", metadata={"Date": None, "Title": f"{title} | {run_id}"})

        activity = tables["origin_activity"]
        origins = [row["origin"] for row in activity]
        x = list(range(len(origins)))
        counts_available = any(row["eligible_cohort_records"] for row in activity)
        figure, axes, path = plot("observed_activity", "Observed link prevalence and recent activity",
                                  panels=2 if counts_available else 1)
        axis = axes[0] if counts_available else axes
        axis.plot(x, [float(row["positive_prevalence"]) for row in activity], "o-", label="Next 30 days")
        axis.plot(x, [float(row["activity_rate"]) for row in activity], "s--", label="Prior 30 days")
        _origin_axis(axis, x, origins, "Share of candidate pairs")
        axis.set_ylim(bottom=0)
        axis.legend()
        if counts_available:
            counts = [float(row["eligible_cohort_records"]) if row["eligible_cohort_records"] else float("nan")
                      for row in activity]
            axes[1].bar(x, counts, color="#677886", label="Next 30 days")
            _origin_axis(axes[1], x, origins, "Eligible cohort records")
            axes[1].legend()
        save(figure, path, "Observed activity")

        figure, axis, path = plot("performance_by_origin", "Average precision by origin")
        ap = {
            (row["model_id"], row["origin"]): float(row["value"]) if row["value"] else float("nan")
            for row in tables["metrics_by_origin"] if row["metric"] == "average_precision"
        }
        selected = _performance_models(tables)
        styles = ("o-", "s--", "D:", "^-.", "v:")
        for index, model in enumerate(selected):
            axis.plot(x, [ap[model, origin] for origin in origins], styles[index], label=model)
        _origin_axis(axis, x, origins, "Average precision")
        axis.set_ylim(0, 1.02)
        axis.legend()
        save(figure, path, "Average precision by origin")

        if not synthetic:
            figure, axis, path = plot("timeline", "Registered year roles")
            for i, role in enumerate(("Cohort", "Fit", "Selection", "Probability mapping", "Final test")):
                year = 2020 + i
                axis.barh(i, 360 if i else 366, color="#366A9F" if i == 4 else "#677886")
                if i:
                    axis.text(361, i, "6 days" if i == 4 else "5 days", va="center", fontsize=9)
            axis.set_yticks(range(5), [f"{2020 + i}  {role}" for i, role in enumerate(
                ("Cohort", "Fit", "Selection", "Probability mapping", "Final test")
            )])
            axis.invert_yaxis()
            axis.set_xlim(0, 405)
            axis.set_xlabel("Days from January 1, followed by omitted target days")
            save(figure, path, "Registered year roles")

        ablation = [
            row for row in tables["paired_comparisons"]
            if row["model_id"] == GRAPH and row["reference_model_id"] == COUNT_ONLY
            and row["metric"] == "average_precision"
        ]
        if ablation:
            figure, axis, path = plot("ablation_by_origin", "Paired difference in average precision")
            differences = [float(row["difference"]) if row["difference"] else float("nan") for row in ablation]
            axis.axhline(0, color="#444444", linewidth=1)
            axis.plot(x, differences, "o-", color="#366A9F")
            _origin_axis(axis, x, origins, "Graph AP minus count-only AP")
            save(figure, path, "Paired ablation")

        reliability = tables["reliability"]
        if reliability:
            figure, axis, path = plot("reliability", "Observed rate by probability bin")
            axis.plot([0, 1], [0, 1], "--", color="#666666", label="Equal rates")
            for model in dict.fromkeys(row["model_id"] for row in reliability):
                rows = [row for row in reliability if row["model_id"] == model and int(row["sample_count"])]
                axis.plot(
                    [float(row["mean_probability"]) for row in rows],
                    [float(row["observed_rate"]) for row in rows],
                    "o-", label=model,
                )
            axis.set(xlim=(0, 1.02), ylim=(0, 1.02), xlabel="Mean link probability", ylabel="Observed link rate")
            axis.legend()
            save(figure, path, "Probability reliability")
    return figures


def _origin_axis(axis, x, origins, ylabel):
    axis.set_xticks(x, origins, rotation=35, ha="right")
    axis.set(xlabel="UTC cutoff date", ylabel=ylabel)
    axis.grid(axis="y", alpha=0.25)


def _performance_models(tables):
    available = list(dict.fromkeys(row["model_id"] for row in tables["model_diagnostics"]))
    selection = [model for model in (GRAPH, COUNT_ONLY, PERSISTENCE) if model in available]
    simple = {"recent_count30", "jaccard", "common_neighbors", "preferential_attachment"}
    ranked = [
        (float(row["value"]), row["model_id"]) for row in tables["metrics_summary"]
        if row["slice"] == "all_pairs" and row["metric"] == "average_precision"
        and row["model_id"] in simple and row["value"]
    ]
    if ranked:
        selection.append(max(ranked)[1])
    selection.extend(model for model in available if model.startswith("demo_forecast_stub"))
    return selection


def _text(cell):
    return "—" if cell is None or cell == "" else str(cell)


def _markdown(blocks, output):
    lines = []
    for kind, *content in blocks:
        if kind == "table":
            columns, rows = content
            def line(cells):
                return "| " + " | ".join(_text(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |"
            lines.append("\n".join([line(columns), line(["---"] * len(columns)), *(line(row) for row in rows)]))
        elif kind == "figure":
            caption, path = content
            lines.append(f"![{caption}]({path.relative_to(output)})")
        elif kind == "link":
            lines.append(f"[{content[0]}]({content[1]})")
        elif kind == "code":
            lines.append(f"```sh\n{content[0]}\n```")
        elif kind == "banner":
            lines.append(f"**{content[0]}**")
        else:
            prefix = {"title": "# ", "heading": "## ", "text": ""}[kind]
            lines.append(prefix + content[0])
    return "\n\n".join(lines) + "\n"


def _html(blocks):
    body = []
    for kind, *content in blocks:
        if kind == "table":
            columns, rows = content
            header = "".join(f'<th scope="col">{escape(_text(cell))}</th>' for cell in columns)
            entries = (
                "<tr>" + "".join(f"<td>{escape(_text(cell))}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            body.append(f'<div class="table"><table><thead><tr>{header}</tr></thead><tbody>'
                        + "".join(entries) + "</tbody></table></div>")
        elif kind == "figure":
            caption, path = content
            svg = b64encode(path.read_bytes()).decode("ascii")
            body.append(f'<figure><img src="data:image/svg+xml;base64,{svg}" alt="{escape(caption)}">'
                        f"<figcaption>{escape(caption)}</figcaption></figure>")
        elif kind == "link":
            body.append(f'<p><a href="{escape(content[1])}">{escape(content[0])}</a></p>')
        elif kind == "code":
            body.append(f"<pre><code>{escape(content[0])}</code></pre>")
        elif kind == "banner":
            body.append(f'<p class="banner">{escape(content[0])}</p>')
        else:
            tag = {"title": "h1", "heading": "h2", "text": "p"}[kind]
            body.append(f"<{tag}>{escape(content[0])}</{tag}>")
    styles = (
        "body{max-width:72rem;margin:2rem auto;padding:0 1rem;color:#18212b;background:#fff;"
        "font:16px/1.55 system-ui,sans-serif}h1,h2{line-height:1.2}.banner{background:#fff1ca;"
        "color:#733f00;padding:1rem;font-weight:700}.table{overflow:auto}table{border-collapse:collapse;"
        "width:100%}td,th{padding:.4rem;border-bottom:1px solid #d7dde2;text-align:left;"
        "overflow-wrap:anywhere}th{background:#edf3f7}img{display:block;width:100%}figure{margin:1.5rem 0}"
        "figcaption{font-size:.9rem}pre{overflow:auto;background:#edf3f7;padding:1rem}"
    )
    return (
        '<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" '
        f'content="width=device-width, initial-scale=1"><title>{escape(TITLE)}</title>'
        f"<style>{styles}</style><main>\n" + "\n".join(body) + "\n</main></html>\n"
    )
