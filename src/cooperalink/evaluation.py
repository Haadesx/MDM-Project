"""Validate a completed score panel and compute comparable evaluation tables."""

from collections import Counter, defaultdict
from datetime import date
from math import fsum, isfinite
from numbers import Real
import re

from .artifacts import digest
from .domain import DataContractError, Metric, Prediction
from .metrics import average_precision, filtered_mrr, precision_at_k, roc_auc
from .temporal import annual_folds
from .universe import candidate_pairs

DIRECT_MODELS = (
    "persistence_binary",
    "recent_count30",
    "jaccard",
    "common_neighbors",
    "preferential_attachment",
)
TOPOLOGY_MODEL = "static_logistic_topology"
FORECAST_MODELS = ("arima", "prophet", "timestral_count_only", "timestral_graph")
RESEARCH_MODELS = (*DIRECT_MODELS, TOPOLOGY_MODEL, *FORECAST_MODELS)
DEMO_MAPPED = "demo_forecast_stub_mapped"
PROBABILITY_TOLERANCE = 1e-12
HASH = re.compile(r"[0-9a-f]{64}")
COUNTRY_CODE = re.compile(r"[A-Z]{3}")


def evaluate_predictions(rows, config, origins, pairs):
    """Evaluate labels joined by exact score key after score persistence."""
    models = tuple(config["models"]["required"])
    dates = tuple(sorted(_iso_date(origin) for origin in origins))
    pairs = tuple(pairs)
    try:
        countries = tuple(sorted({country for pair in pairs for country in pair}))
        valid_pairs = set(candidate_pairs(countries))
    except (TypeError, ValueError) as exc:
        raise DataContractError("Invalid candidate pairs") from exc
    if (
        not pairs or len(pairs) != len(valid_pairs) or set(pairs) != valid_pairs
        or any(not COUNTRY_CODE.fullmatch(country) for country in countries)
    ):
        raise DataContractError("Expected pairs must be a complete canonical candidate panel")
    if not dates or len(dates) != len(set(dates)):
        raise DataContractError("Expected origins must be nonempty and unique")
    if not models or len(models) != len(set(models)):
        raise DataContractError("Expected model inventory must be nonempty and unique")
    if "persistence_binary" not in models:
        raise DataContractError("Model inventory must include persistence_binary")

    k_values = tuple(config["evaluation"]["k_values"])
    synthetic = config["synthetic"]
    if not synthetic:
        if set(models) != set(RESEARCH_MODELS):
            raise DataContractError("Research model inventory must contain all ten registered IDs")
        if dates != tuple(fold.origin.isoformat() for fold in annual_folds(2024)):
            raise DataContractError("Research origins must match the 12 fixed 2024 target blocks")
        if len(countries) != 30 or len(pairs) != 435:
            raise DataContractError("Research requires 30 countries and 435 candidate pairs")
        if k_values != (10, 25, 50):
            raise DataContractError("Research requires Precision@K values 10, 25 and 50")
        if config["evaluation"]["probability_score_absolute_tolerance"] != PROBABILITY_TOLERANCE:
            raise DataContractError("Research probability score tolerance must be 1e-12")

    forecast_models = FORECAST_MODELS
    if synthetic and config.get("multi_year"):
        forecast_models = (*forecast_models, DEMO_MAPPED)
    probability_models = (TOPOLOGY_MODEL, *forecast_models)
    panel, truth, run_id = _validate_panel(
        rows, models, dates, valid_pairs, synthetic, digest(config), forecast_models
    )
    metrics = []
    origin_activity = []
    for origin in dates:
        outcomes = [truth[origin, pair] for pair in pairs]
        positive_count = sum(label for label, _ in outcomes)
        active_count = sum(active for _, active in outcomes)
        origin_activity.append({
            "run_id": run_id,
            "origin": origin,
            "candidate_count": len(pairs),
            "positive_count": positive_count,
            "negative_count": len(pairs) - positive_count,
            "positive_prevalence": positive_count / len(pairs),
            "active_count": active_count,
            "activity_rate": active_count / len(pairs),
        })
        for model in models:
            group = [panel[model, origin, pair] for pair in pairs]
            for name, selected in (
                ("all_pairs", group),
                ("active_last_30", [row for row in group if row["active_last_30"]]),
                ("inactive_last_30", [row for row in group if not row["active_last_30"]]),
            ):
                common = {"run_id": run_id, "model_id": model, "origin": origin, "slice": name}
                metrics.extend(_measure(selected, common, k_values, countries, model in probability_models))

    primary = [row for row in metrics if row["slice"] == "all_pairs"]
    return {
        "metrics_by_origin": primary,
        "conditional_slices": [row for row in metrics if row["slice"] != "all_pairs"],
        "metrics_summary": _summarize(metrics),
        "paired_comparisons": _paired(primary, models, dates, run_id),
        "origin_activity": origin_activity,
        "model_diagnostics": _model_diagnostics(panel.values(), models, run_id),
        "reliability": _reliability(panel.values(), probability_models, run_id),
    }


def _iso_date(value):
    try:
        normalized = date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise DataContractError(f"Invalid origin date {value!r}") from exc
    if normalized != str(value):
        raise DataContractError(f"Origin date must use YYYY-MM-DD: {value!r}")
    return normalized


def _validate_panel(rows, models, dates, pairs, synthetic, config_hash, forecast_models):
    panel = {}
    truth = {}
    mapper_ids = defaultdict(set)
    run_ids = set()
    dates = set(dates)
    for row in rows:
        model = row.get("model_id")
        origin = _iso_date(row.get("origin"))
        pair = (row.get("country_a"), row.get("country_b"))
        key = (model, origin, pair)
        if model not in models:
            raise DataContractError(f"Unexpected model in prediction inventory: {model}")
        if origin not in dates or any(not isinstance(code, str) for code in pair) or pair not in pairs:
            raise DataContractError(f"Unexpected origin or candidate pair: {key}")
        if key in panel:
            raise DataContractError(f"duplicate prediction for {key}")
        _validate_score(row, key, synthetic, forecast_models)
        label = row.get("label", row.get("y_true"))
        active = row.get("active_last_30")
        if label not in (0, 1) or active not in (False, True) or row.get("y_true", label) != label:
            raise DataContractError(f"Invalid joined label or activity flag for {key}")
        outcome = (int(label), bool(active))
        if truth.setdefault((origin, pair), outcome) != outcome:
            raise DataContractError(f"Models disagree on joined label or activity for {origin}, {pair}")
        if model == "persistence_binary" and row["score"] != int(active):
            raise DataContractError(f"Persistence score disagrees with last-30-day activity for {key}")
        if model in forecast_models:
            mapper_ids[model].add(row["mapper_id"])
        run_ids.add(row["run_id"])
        if row["configuration_hash"] != config_hash:
            raise DataContractError(f"Prediction configuration identity does not match this run for {key}")
        panel[key] = {**row, "label": outcome[0], "active_last_30": outcome[1]}

    identities = [identity for values in mapper_ids.values() for identity in values]
    if any(len(values) != 1 for values in mapper_ids.values()) or len(set(identities)) != len(identities):
        raise DataContractError("Forecast models require distinct frozen mapper identities")
    missing_models = set(models) - {key[0] for key in panel}
    if missing_models:
        raise DataContractError(f"Missing models from prediction inventory: {sorted(missing_models)}")
    if len(panel) != len(models) * len(dates) * len(pairs):
        missing = next(
            (model, origin, pair)
            for model in models for origin in sorted(dates) for pair in sorted(pairs)
            if (model, origin, pair) not in panel
        )
        raise DataContractError(f"Missing prediction for candidate panel key {missing}")
    if len(run_ids) != 1:
        raise DataContractError("Prediction panel must use one run identity")
    return panel, truth, run_ids.pop()


def _validate_score(row, key, synthetic, forecast_models):
    model = key[0]
    if row.get("schema_version") != "1.0.0" or row.get("synthetic") is not synthetic:
        raise DataContractError(f"Prediction schema or synthetic provenance mismatch for {key}")
    if not isinstance(row.get("run_id"), str) or not row["run_id"].strip():
        raise DataContractError(f"Missing run identity for {key}")
    for field in ("input_hash", "configuration_hash"):
        if not isinstance(row.get(field), str) or not HASH.fullmatch(row[field]):
            raise DataContractError(f"Invalid prediction {field} for {key}")
    runtime = row.get("runtime_seconds")
    if runtime is not None and (not isinstance(runtime, Real) or not isfinite(runtime) or runtime < 0):
        raise DataContractError(f"Invalid prediction runtime for {key}")
    status = row.get("status")
    if status != "ok" and not (status == "constant_series" and model in ("arima", "prophet")):
        raise DataContractError(f"Unsuccessful prediction for {key}: {status} {row.get('error_reason') or ''}")
    score = row.get("score")
    if not isinstance(score, Real) or isinstance(score, bool) or not isfinite(score):
        raise DataContractError(f"Invalid numerical score for {key}")
    probability = row.get("probability")
    if model == TOPOLOGY_MODEL or model in forecast_models:
        if (
            not isinstance(probability, Real)
            or isinstance(probability, bool)
            or not 0 <= probability <= 1
            or not 0 <= score <= 1
            or abs(score - probability) > PROBABILITY_TOLERANCE
        ):
            raise DataContractError(f"Ranking score must match probability for {key}")
        if model in forecast_models:
            mapper = row.get("mapper_id")
            if not isinstance(mapper, str) or not mapper.strip():
                raise DataContractError(f"Forecast probability requires a mapper identity for {key}")
    elif probability is not None or row.get("mapper_id") is not None:
        raise DataContractError(f"Direct model must report raw scores without a probability for {key}")


def _measure(rows, common, k_values, countries, has_probability):
    predictions = [
        Prediction((row["country_a"], row["country_b"]), row["score"], row["label"])
        for row in rows
    ]
    positive = sum(row.label for row in predictions)
    counts = {
        "candidate_count": len(rows), "positive_count": positive, "negative_count": len(rows) - positive
    }

    def record(name, value, reason, **support):
        return {
            **common, "metric": name, "value": value, "reason": reason, **counts,
            "requested_k": support.get("requested_k"),
            "effective_k": support.get("effective_k"),
            "positive_query_count": support.get("positive_query_count"),
        }

    metrics = []
    for name, metric in (
        ("roc_auc", roc_auc(predictions)),
        ("average_precision", average_precision(predictions)),
    ):
        metrics.append(record(name, metric.value, metric.reason))
    for k in k_values:
        precision = precision_at_k(predictions, k)
        metrics.append(record(
            "precision_at_k", precision.value, None if rows else "empty_slice",
            requested_k=k, effective_k=precision.effective_k,
        ))
    if common["slice"] == "all_pairs":
        mrr = filtered_mrr(predictions, countries)
        metrics.append(record(
            "filtered_mrr", mrr.value, mrr.reason, positive_query_count=mrr.positive_query_count
        ))
    if has_probability:
        brier = _brier(rows)
        metrics.append(record("brier_score", brier.value, brier.reason))
    return metrics


def _brier(rows):
    if not rows:
        return Metric(None, "empty_slice")
    return Metric(fsum((row["probability"] - row["label"]) ** 2 for row in rows) / len(rows))


def _summarize(metrics):
    groups = defaultdict(list)
    group_fields = ("run_id", "model_id", "slice", "metric", "requested_k")
    for row in metrics:
        groups[tuple(row[field] for field in group_fields)].append(row)
    summary = []
    for key, rows in groups.items():
        scores = [row["value"] for row in rows if row["value"] is not None]
        reasons = Counter(row["reason"] for row in rows if row["reason"])
        summary.append({
            **dict(zip(group_fields, key)),
            "value": fsum(scores) / len(scores) if scores else None,
            "valid_windows": len(scores),
            "evaluated_windows": len(rows),
            "undefined_reasons": "; ".join(f"{reason} ({count})" for reason, count in sorted(reasons.items())),
            "candidate_rows": sum(row["candidate_count"] for row in rows),
            "positive_rows": sum(row["positive_count"] for row in rows),
            "negative_rows": sum(row["negative_count"] for row in rows),
            "positive_queries": sum(row["positive_query_count"] or 0 for row in rows),
        })
    return summary


def _paired(metrics, models, dates, run_id):
    comparisons = [(model, "persistence_binary") for model in models if model != "persistence_binary"]
    if "timestral_graph" in models and "timestral_count_only" in models:
        comparisons.append(("timestral_graph", "timestral_count_only"))
    indexed = {
        (row["origin"], row["model_id"], row["metric"], row["requested_k"]): row for row in metrics
    }
    metric_keys = dict.fromkeys((row["metric"], row["requested_k"]) for row in metrics)
    results = []
    for origin in dates:
        for model, reference in comparisons:
            for metric, requested_k in metric_keys:
                model_row = indexed.get((origin, model, metric, requested_k))
                reference_row = indexed.get((origin, reference, metric, requested_k))
                if model_row is None or reference_row is None:
                    continue
                value = model_row["value"]
                reference_value = reference_row["value"]
                difference = None
                reason = model_row["reason"] or reference_row["reason"]
                if value is not None and reference_value is not None:
                    difference = value - reference_value
                results.append({
                    "run_id": run_id, "origin": origin, "model_id": model, "reference_model_id": reference,
                    "metric": metric, "requested_k": requested_k, "value": value,
                    "reference_value": reference_value, "difference": difference, "reason": reason,
                    "sign": None if difference is None else int(difference > 0) - int(difference < 0),
                    "candidate_count": model_row["candidate_count"],
                })
    return results


def _model_diagnostics(rows, models, run_id):
    groups = defaultdict(list)
    for row in rows:
        groups[row["model_id"]].append(row)
    diagnostics = []
    for model in models:
        model_rows = groups[model]
        runtimes = [row["runtime_seconds"] for row in model_rows if row.get("runtime_seconds") is not None]
        diagnostics.append({
            "run_id": run_id, "model_id": model, "candidate_rows": len(model_rows),
            "failed_rows": sum(row["status"] == "failed" for row in model_rows),
            "constant_shortcut_rows": sum(row["status"] == "constant_series" for row in model_rows),
            "runtime_seconds": fsum(runtimes) if runtimes else None,
        })
    return diagnostics


def _reliability(rows, probability_models, run_id):
    bins = defaultdict(list)
    for row in rows:
        probability = row.get("probability")
        if probability is not None:
            bins[row["model_id"], min(int(probability * 10), 9)].append(row)

    reliability = []
    for model in probability_models:
        if not any((model, index) in bins for index in range(10)):
            continue
        for index in range(10):
            group = bins[model, index]
            reliability.append({
                "run_id": run_id, "model_id": model, "bin_lower": index / 10,
                "bin_upper": (index + 1) / 10, "sample_count": len(group),
                "mean_probability": fsum(row["probability"] for row in group) / len(group) if group else None,
                "observed_rate": sum(row["label"] for row in group) / len(group) if group else None,
            })
    return reliability


def write_evaluation(output, tables, config, manifest=None, completion=None):
    from .reporting import write_evaluation as write

    write(output, tables, config, manifest, completion)


def render_report(output, config, manifest=None, completion=None):
    from .reporting import render_report as render

    render(output, config, manifest, completion)
