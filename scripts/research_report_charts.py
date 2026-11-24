"""Plotly figures built directly from the verified research CSV exports."""

from dataclasses import dataclass

import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class Chart:
    figure: go.Figure
    title: str
    subtitle: str
    caption: str


INK = "#142632"
SLATE = "#657383"
TEAL = "#007B76"
AMBER = "#A85B2B"
INDIGO = "#5260A3"
GRID = "#E0E7E8"
MODELS = {
    "arima": ("ARIMA", INDIGO, "solid", "triangle-up"),
    "prophet": ("Prophet", "#914F74", "dashdot", "star"),
    "recent_count30": ("Recent count", "#647548", "solid", "circle"),
    "static_logistic_topology": ("Logistic topology", "#426C89", "dot", "cross"),
    "timestral_count_only": ("Timestral count-only", AMBER, "dash", "square"),
    "timestral_graph": ("Timestral graph", TEAL, "solid", "diamond"),
    "preferential_attachment": ("Preferential attachment", SLATE, "solid", "circle"),
    "common_neighbors": ("Common neighbors", SLATE, "solid", "circle"),
    "jaccard": ("Jaccard", SLATE, "solid", "circle"),
    "persistence_binary": ("Binary persistence", SLATE, "dot", "circle"),
}
CORE = ("arima", "timestral_graph", "timestral_count_only", "persistence_binary")
AP = "average_precision"


def _finish(figure, height=400, left=58):
    figure.update_layout(
        template="none", autosize=True, height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Avenir Next, Aptos, system-ui, sans-serif", size=13, color=INK),
        margin=dict(l=left, r=20, t=18, b=54),
        hoverlabel=dict(bgcolor=INK, font_color="white"),
        legend=dict(orientation="h", yanchor="top", y=-0.23, x=0, font_size=12),
    )
    figure.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    figure.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)


def _cutoffs(figure, **axis):
    figure.update_xaxes(
        type="date", tickformat="%b %d", hoverformat="%Y-%m-%d", nticks=6,
        title_text="Forecast cutoff", showgrid=False, **axis,
    )


def _line(name, color, dash, symbol, x, y, hover, **kwargs):
    return go.Scatter(
        name=name, x=x, y=y, mode="lines+markers",
        line=dict(color=color, width=2.4, dash=dash),
        marker=dict(symbol=symbol, size=8, line=dict(color="#F5F7F7", width=0.8)),
        hovertemplate=hover + "<extra>%{fullData.name}</extra>", **kwargs,
    )


def _ranking(table):
    rows = sorted(
        (row for row in table if row["slice"] == "all_pairs" and row["metric"] == AP),
        key=lambda row: float(row["value"]), reverse=True,
    )
    names = [MODELS[row["model_id"]][0] for row in rows]
    values = [float(row["value"]) for row in rows]
    reference = next(float(row["value"]) for row in rows if row["model_id"] == "persistence_binary")
    figure = go.Figure(go.Scatter(
        x=values, y=names, mode="markers+text", text=[f"{value:.1%}" for value in values],
        textposition="middle right", textfont_size=12, cliponaxis=False,
        marker=dict(size=10, color=[MODELS[row["model_id"]][1] for row in rows],
                    symbol=[MODELS[row["model_id"]][3] for row in rows]),
        customdata=[row["valid_windows"] for row in rows],
        hovertemplate="%{y}<br>Macro AP %{x:.2%}<br>Valid windows %{customdata}<extra></extra>",
    ))
    figure.add_vline(x=reference, line_color=SLATE, line_dash="dot", line_width=1.5)
    _finish(figure, height=396, left=8)
    figure.update_yaxes(categoryorder="array", categoryarray=names, autorange="reversed",
                        showgrid=True, tickfont_size=12)
    figure.update_xaxes(title_text="Macro average precision", tickformat=".0%", nticks=5,
                        range=[min(values) - 0.025, max(values) + 0.055])
    return Chart(
        figure, "Average precision by model",
        "Ten models ranked by mean average precision (AP) across final-year windows.",
        "The dotted vertical line marks the binary persistence score. Higher AP indicates better ranking of observed links.",
    )


def _performance(table):
    figure = go.Figure()
    for model in CORE:
        rows = sorted(
            (row for row in table if row["model_id"] == model and row["metric"] == AP and row["slice"] == "all_pairs"),
            key=lambda row: row["origin"],
        )
        figure.add_trace(_line(
            *MODELS[model], [row["origin"] for row in rows], [float(row["value"]) for row in rows],
            "Cutoff %{x}<br>AP %{y:.2%}",
        ))
    _finish(figure)
    _cutoffs(figure)
    figure.update_yaxes(title_text="Average precision", tickformat=".0%")
    return Chart(
        figure, "Average precision by forecast window",
        "Four core models evaluated on the same candidate pairs within each 30-day label window.",
        "The date on the horizontal axis is the forecast cutoff. Each label window starts the following UTC day.",
    )


def _paired(table):
    figure = go.Figure()
    for reference, name, color, dash, symbol in (
        ("persistence_binary", "vs. binary persistence", TEAL, "solid", "diamond"),
        ("timestral_count_only", "vs. Timestral count-only", AMBER, "dash", "square"),
    ):
        rows = sorted(
            (row for row in table if row["model_id"] == "timestral_graph" and row["reference_model_id"] == reference and row["metric"] == AP),
            key=lambda row: row["origin"],
        )
        figure.add_trace(_line(
            name, color, dash, symbol, [row["origin"] for row in rows],
            [100 * float(row["difference"]) for row in rows],
            "Cutoff %{x}<br>AP difference %{y:+.2f} pp",
        ))
    figure.add_hline(y=0, line_color=SLATE, line_dash="dot", line_width=1.8)
    _finish(figure, height=350)
    _cutoffs(figure)
    figure.update_yaxes(title_text="AP difference (pp)", ticksuffix=" pp")
    return Chart(
        figure, "Timestral graph’s paired differences",
        "Within each cutoff, subtract the reference model’s average precision from the graph model’s average precision.",
        "Above zero favors Timestral graph. Below zero favors the reference model. Differences are in percentage points.",
    )


def _activity(table):
    rows = sorted(table, key=lambda row: row["origin"])
    origins = [row["origin"] for row in rows]
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.64, 0.36], vertical_spacing=0.12)
    for field, name, color, dash, symbol in (
        ("positive_prevalence", "Observed prevalence", TEAL, "solid", "diamond"),
        ("activity_rate", "Prior 30-day activity", AMBER, "dash", "square"),
    ):
        figure.add_trace(_line(
            name, color, dash, symbol, origins, [float(row[field]) for row in rows],
            "Cutoff %{x}<br>Candidate pairs %{y:.2%}",
        ), row=1, col=1)
    figure.add_trace(go.Bar(
        x=origins, y=[int(row["eligible_cohort_records"]) if row["eligible_cohort_records"] else None for row in rows],
        marker_color=INDIGO, showlegend=False, name="Eligible records",
        hovertemplate="Cutoff %{x}<br>Eligible records %{y:,d}<extra></extra>",
    ), row=2, col=1)
    _finish(figure, height=433)
    _cutoffs(figure, row=2, col=1)
    figure.update_xaxes(hoverformat="%Y-%m-%d", row=1, col=1)
    figure.update_yaxes(title_text="Pair share", tickformat=".0%", row=1, col=1)
    figure.update_yaxes(title_text="Records", tickformat="~s", nticks=3, row=2, col=1)
    return Chart(
        figure, "Observed links and historical activity",
        "Pair shares and eligible cohort records across the evaluation cutoffs.",
        "Observed prevalence and record counts describe the label window. Historical activity counts pairs with an event in the 30-day lookback.",
    )


def _reliability(table):
    figure = go.Figure(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration",
        line=dict(color=SLATE, width=1.5, dash="dot"), hoverinfo="skip",
    ))
    for model in ("arima", "prophet", "static_logistic_topology", "timestral_count_only", "timestral_graph"):
        rows = sorted(
            (row for row in table if row["model_id"] == model and int(row["sample_count"]) > 0),
            key=lambda row: float(row["bin_lower"]),
        )
        figure.add_trace(_line(
            *MODELS[model], [float(row["mean_probability"]) for row in rows],
            [float(row["observed_rate"]) for row in rows],
            "Bin %{customdata[0]:.0%}–%{customdata[1]:.0%}<br>"
            "Mean forecast %{x:.1%}<br>Observed rate %{y:.1%}<br>Pair-windows %{customdata[2]:,d}",
            customdata=[[float(row["bin_lower"]), float(row["bin_upper"]), int(row["sample_count"])] for row in rows],
        ))
    _finish(figure, height=440)
    figure.update_xaxes(title_text="Mean forecast probability", tickformat=".0%", range=[-0.025, 1.025], dtick=0.2)
    figure.update_yaxes(title_text="Observed frequency", tickformat=".0%", range=[-0.025, 1.025], dtick=0.2)
    return Chart(
        figure, "Probability reliability",
        "Observed event frequency against mean forecast probability across occupied bins for all five probabilistic outputs.",
        "Points on the diagonal match observed frequencies. Hover to see how many pair-windows support each point.",
    )


def _strata(table):
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, shared_yaxes=True, vertical_spacing=0.16,
        subplot_titles=("Active in prior 30 days", "Inactive in prior 30 days"),
    )
    for panel, label in enumerate(("active_last_30", "inactive_last_30"), start=1):
        for model in CORE:
            rows = sorted(
                (row for row in table if row["model_id"] == model and row["metric"] == AP and row["slice"] == label),
                key=lambda row: row["origin"],
            )
            figure.add_trace(_line(
                *MODELS[model], [row["origin"] for row in rows],
                [float(row["value"]) if row["value"] else None for row in rows],
                "Cutoff %{x}<br>AP %{y:.2%}<br>Pairs %{customdata[0]:,d}<br>Positive pairs %{customdata[1]:,d}",
                customdata=[[int(row["candidate_count"]), int(row["positive_count"])] for row in rows],
                legendgroup=model, showlegend=panel == 1,
            ), row=panel, col=1)
    _finish(figure, height=510)
    figure.update_layout(margin_t=32)
    figure.update_annotations(font_size=12)
    figure.update_yaxes(title_text="Average precision", tickformat=".0%", range=[0, 1.02], nticks=4)
    figure.update_xaxes(hoverformat="%Y-%m-%d", row=1, col=1)
    _cutoffs(figure, row=2, col=1)
    return Chart(
        figure, "Average precision by prior activity",
        "The same four models shown within two pair groups defined at each forecast cutoff.",
        "The panels share an AP scale. Hover to see the number of candidate and positive pairs in each window and group.",
    )


def build_charts(tables: dict[str, list[dict[str, str]]]) -> dict[str, Chart]:
    return {
        "ranking": _ranking(tables["metrics_summary"]),
        "performance": _performance(tables["metrics_by_origin"]),
        "paired": _paired(tables["paired_comparisons"]),
        "activity": _activity(tables["origin_activity"]),
        "reliability": _reliability(tables["reliability"]),
        "strata": _strata(tables["conditional_slices"]),
    }
