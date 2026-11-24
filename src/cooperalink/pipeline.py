import importlib.metadata as metadata
import json
import os
import platform
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timedelta, timezone
from functools import cached_property
from multiprocessing import get_context
from pathlib import Path
from time import perf_counter

from .artifacts import digest, file_hash, read_json, read_parquet, write_csv, write_json, write_parquet
from .checkpoints import checkpoint
from .domain import CoverageError, DataContractError, Event, Fold
from .features import FeaturePanel
from .ingestion import deduplicate_events, normalize_event
from .source import COVERAGE_COLUMNS, local_input
from .temporal import annual_folds, assert_chronology, date_window, require_coverage
from .universe import candidate_pairs, country_incidence, select_countries

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "config/research.json"
DIRECT = ("persistence_binary", "recent_count30", "jaccard", "common_neighbors",
          "preferential_attachment")
FORECAST = ("arima", "prophet", "timestral_count_only", "timestral_graph")
STATIC = "static_logistic_topology"
DEMO_FORECAST = "demo_forecast_stub"
VERSION = "1.0.0"
THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")


def set_numerical_threads(threads):
    for key in THREAD_ENV:
        os.environ[key] = str(threads)


def code_identity():
    return digest({str(path.relative_to(ROOT)): file_hash(path) for path in sorted(
        [*Path(__file__).parent.glob("*.py"), *ROOT.glob("schemas/*.json")]
    )})


def environment():
    packages = ("numpy", "scipy", "pandas", "pyarrow", "scikit-learn", "statsmodels",
                "prophet", "cmdstanpy", "timestral", "torch", "huggingface-hub", "matplotlib")
    versions = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {"python": platform.python_version(), "platform": platform.platform(),
            "machine": platform.machine(), "processor": platform.processor(), "logical_cpus": os.cpu_count(),
            "packages": versions, "lock_sha256": file_hash(ROOT / "uv.lock")}


def demo_input(config):
    countries = config["cohort"]["countries"]
    if config.get("multi_year"):
        start, end = date(2020, 1, 1), date(2025, 1, 1)
        rows = []
        for offset in range((end - start).days):
            day = start + timedelta(days=offset)
            for index, (a, b) in enumerate(candidate_pairs(countries)):
                if (offset + index * 23) % (19 + index * 7) < 2 and (offset // 90 + index) % 3 != 0:
                    rows.append({"GlobalEventID": str(len(rows) + 1), "EventCode": "061",
                                 "Actor1CountryCode": a, "Actor2CountryCode": b,
                                 "SQLDATE": day.strftime("%Y%m%d"), "DATEADDED": day.strftime("%Y%m%d") + "000000"})
    else:
        origin = date.fromisoformat(config["origin"])
        start = origin - timedelta(days=config["temporal"]["raw_context_days"] - 1)
        end = origin + timedelta(days=config["temporal"]["horizon_days"] + 1)
        rows = read_json(ROOT / config["fixture"])
    fixture_hash = digest(rows)
    events = deduplicate_events(normalize_event(row, countries) for row in rows)
    complete = {start + timedelta(days=i) for i in range((end - start).days)}
    counts = Counter(event.observed_day for event in events)
    coverage = [
        dict.fromkeys(COVERAGE_COLUMNS) | {"date": str(day), "status": "complete",
        "evidence_kind": "synthetic_fixture", "evidence_id": fixture_hash,
        "extraction_start_utc": f"{day}T00:00:00Z",
        "extraction_end_utc": f"{day + timedelta(days=1)}T00:00:00Z",
        "source_row_count": counts[day], "eligible_row_count": counts[day],
        "source_snapshot_id": "synthetic"}
        for day in sorted(complete)]
    registry = [{"code": code, "label": code, "eligible": "true", "entity_kind": "synthetic_fixture",
                 "reason": "Synthetic demo roster", "source_version": "synthetic"} for code in countries]
    directions = {}
    for row in rows:
        directions.setdefault(str(row["GlobalEventID"]), set()).add(
            (row["Actor1CountryCode"], row["Actor2CountryCode"]))
    audit = {"source_rows": len(rows), "eligible_unique": len(events), "duplicate": len(rows) - len(events)}
    return events, complete, coverage, registry, audit, {k: sorted(v) for k, v in directions.items()}, {
        "source": {"dataset": "deterministic synthetic fixture", "synthetic": True},
        "files": {"fixture": {"sha256": fixture_hash}}}


def plan_origins(config):
    horizon = config["temporal"]["horizon_days"]
    if config["synthetic"] and not config.get("multi_year"):
        origin = date.fromisoformat(config["origin"])
        return {"test": [Fold(origin.year, 0, origin, origin + timedelta(days=1),
                              origin + timedelta(days=horizon))]}
    return {role: [fold for year in config["temporal"]["roles"][role] for fold in annual_folds(year, horizon)]
            for role in ("train", "validation", "calibration", "test")}


def source_coverage(coverage):
    return {"start": coverage[0]["date"],
            "end_exclusive": str(date.fromisoformat(coverage[-1]["date"]) + timedelta(days=1)),
            "complete": all(row["status"] == "complete" for row in coverage),
            "evidence_kind": ", ".join(sorted({row["evidence_kind"] for row in coverage if row["evidence_kind"]})),
            "complete_day_count": sum(row["status"] == "complete" for row in coverage),
            "expected_day_count": len(coverage)}


def cohort_for(config, events, complete):
    if config["synthetic"]:
        return sorted(config["cohort"]["countries"]), [
            {"country_code": code, "incidence": None, "rank": index + 1, "selection_year": None,
             "selected": True, "synthetic": True}
            for index, code in enumerate(sorted(config["cohort"]["countries"]))]
    year = config["cohort"]["selection_year"]
    first, end = date(year, 1, 1), date(year + 1, 1, 1)
    require_coverage(date_window(end - timedelta(days=1), (end - first).days), complete)
    limit = config["cohort"]["top_n"]
    selected = select_countries(events, year, limit)
    if len(selected) != limit:
        raise DataContractError(f"Cohort requires exactly {limit} countries, selected {len(selected)}")
    return selected, [{"country_code": code, "incidence": count, "rank": idx + 1,
                       "selection_year": year, "selected": code in selected, "synthetic": False}
                      for idx, (code, count) in enumerate(country_incidence(events, year).items())]


def panel_for(config, events, countries, complete):
    temporal = config["temporal"]
    return FeaturePanel(events, countries, complete, temporal["context_days"],
                        temporal["graph_window_days"], temporal["horizon_days"])


def fold_rows(config, folds, complete):
    context, raw = (config["temporal"][key] for key in ("context_days", "raw_context_days"))
    return [{"role": role, "origin": str(f.origin), "label_year": f.year, "index": f.index,
             "label_start": str(f.label_start), "label_end": str(f.label_end),
             "raw_support_start": str(f.origin - timedelta(days=raw - 1)),
             "context_start": str(f.origin - timedelta(days=context - 1)),
             "history_complete": set(date_window(f.origin, raw)) <= complete,
             "label_complete": set(date_window(f.label_end, (f.label_end - f.origin).days)) <= complete,
             "synthetic": config["synthetic"]}
            for role, group in folds.items() for f in group]


def persist_features(path, panel, days, synthetic):
    import numpy as np
    import pyarrow as pa

    n = len(panel.pairs)
    a, b = zip(*panel.pairs, strict=True)
    count_rows = {
        "day": [str(day) for day in days for _ in range(n)],
        "country_a": list(a) * len(days), "country_b": list(b) * len(days),
        "synthetic": np.full(len(days) * n, synthetic, dtype=bool)}
    counts = [panel.daily.get(day, {}).get(pair, 0) for day in days for pair in panel.pairs]
    write_parquet(path / "daily_counts.parquet", pa.table(count_rows | {"count": counts}))
    graph_days = [day for day in days if set(date_window(day, panel.width)) <= panel.complete]
    if graph_days:
        graph = np.array([panel.snapshot(day) for day in graph_days]).reshape(-1, 5)
        write_parquet(path / "daily_graph_features.parquet", pa.table({
            "day": [str(day) for day in graph_days for _ in range(n)],
            "country_a": list(a) * len(graph_days), "country_b": list(b) * len(graph_days),
            "jaccard": graph[:, 0], "common_neighbors": graph[:, 1].astype(int),
            "preferential_attachment": graph[:, 2].astype(int), "min_degree": graph[:, 3].astype(int),
            "max_degree": graph[:, 4].astype(int), "graph_window_days": np.full(len(graph), panel.width),
            "synthetic": np.full(len(graph), synthetic, dtype=bool)}))


class Run:
    def __init__(self, output, config, input_path=None):
        self.output = output
        self.config = config
        self.synthetic = config["synthetic"]
        self.input = input_path
        self.id = output.name
        self.config_hash = digest(config)
        self.env = environment()
        self.code_hash = code_identity()
        self.folds = plan_origins(config)
        self.required = tuple(config["models"]["required"])
        self.forecast_ids = tuple(model for model in self.required
                                  if model in FORECAST or model.startswith(DEMO_FORECAST))
        self.threads = config.get("execution", {}).get("total_numerical_threads", 4)
        set_numerical_threads(self.threads)
        self.classical_pool = None
        self.timestral = None
        self.backend_error = None

    def close(self):
        if self.classical_pool is not None:
            self.classical_pool.shutdown(cancel_futures=True)
            self.classical_pool = None

    def path(self, name):
        return self.output / name

    def read(self, name):
        return read_json(self.path(name))

    def write(self, name, value):
        write_json(self.path(name), value)

    @cached_property
    def identity(self):
        return {"configuration_hash": self.config_hash, "code_hash": self.code_hash,
                "lock_sha256": self.env["lock_sha256"], "platform": self.env["platform"],
                "python": self.env["python"], "packages": self.env["packages"]}

    def initialize(self):
        if self.path("run_request.json").exists():
            prior = self.read("run_request.json")
            if (prior["identity"] != self.identity or prior["input"] != (str(self.input) if self.input else None)
                    or digest(self.read("resolved_config.json")) != self.config_hash):
                raise DataContractError("Run identity changed. Use a new output directory")
            return
        self.write("resolved_config.json", self.config)
        self.write("environment.json", self.env)
        self.status("pending", "prepare")
        self.write("run_request.json", {"identity": self.identity, "input": str(self.input) if self.input else None,
                                        "created_at": datetime.now(timezone.utc).isoformat()})

    def status(self, status, stage, detail=None):
        path = self.path("stage_status.json")
        previous = read_json(path) if path.exists() else {}
        self.write("stage_status.json", previous | {stage: {"status": status, "detail": detail}})

    def validate_source(self):
        data = self.raw_data()
        cohort_for(self.config, data[0], data[1])
        require_coverage((date.fromisoformat(row["date"]) for row in data[2]), data[1])
        rows = fold_rows(self.config, self.folds, data[1])
        missing = [r["origin"] for r in rows if not r["history_complete"] or not r["label_complete"]]
        if missing:
            raise CoverageError(f"Missing history or label coverage for {len(missing)} origins, first {missing[0]}")
        return data[4]

    def raw_data(self):
        return demo_input(self.config) if self.synthetic else local_input(self.input, self.config, ROOT)

    def check_prepared(self, prepared):
        if self.synthetic:
            files = demo_input(self.config)[-1]["files"]
            if files != prepared["provenance"]["files"]:
                raise DataContractError("Synthetic fixture changed. Use a new output directory")
        else:
            from .source import read_registry, source_file

            for name, expected in prepared["provenance"]["files"].items():
                if file_hash(source_file(self.input, name)) != expected["sha256"]:
                    raise DataContractError(f"Source {name} changed. Use a new output directory")
            registry = ROOT / self.config["cohort"]["registry"]
            if read_registry(registry)[2] != prepared["provenance"]["registry"]:
                raise DataContractError("Source registry changed. Use a new output directory")
        for name, sha in prepared["artifacts"].items():
            if not self.path(name).is_file() or file_hash(self.path(name)) != sha:
                raise DataContractError(f"Corrupt or missing prepared artifact {name}")

    def prepare(self):
        if self.path("prepared.json").exists():
            prepared = self.read("prepared.json")
            self.check_prepared(prepared)
            return prepared
        self.status("running", "prepare")
        events, complete, coverage, registry, audit, directions, provenance = self.raw_data()
        self.write("cleaning_audit.json", audit)
        write_csv(self.path("country_registry.csv"), registry)
        write_parquet(self.path("coverage.parquet"), [row | {"synthetic": self.synthetic} for row in coverage])
        countries, cohort = cohort_for(self.config, events, complete)
        panel = panel_for(self.config, events, countries, complete)
        if len(panel.pairs) != self.config["cohort"]["expected_pairs"]:
            raise DataContractError("Candidate count disagrees with registered configuration")
        origin_records = fold_rows(self.config, self.folds, complete)
        write_csv(self.path("origins.csv"), origin_records)
        write_csv(self.path("cohort.csv"), cohort)
        write_parquet(self.path("candidate_pairs.parquet"), [
            {"country_a": a, "country_b": b, "synthetic": self.synthetic} for a, b in panel.pairs])
        ledger = [{"event_id": e.event_id, "country_a": e.country_a, "country_b": e.country_b,
                   "event_day": str(e.event_day), "added_at_utc": e.added_at.isoformat(),
                   "observed_day": str(e.observed_day), "event_code": "061",
                   "actor_directions": directions[e.event_id], "synthetic": self.synthetic} for e in events]
        write_parquet(self.path("events.parquet"), ledger)
        retained = sum(sum(counts.values()) for counts in panel.daily.values())
        self.write("cleaning_audit.json", audit | {"cohort_retained": retained,
                   "cohort_retained_share": retained / len(events) if events else None})
        persist_features(self.output, panel, sorted(complete), self.synthetic)
        labels = []
        missing = []
        for role, folds in self.folds.items():
            for fold in folds:
                try:
                    counts = panel.future_counts(fold.origin)
                except CoverageError:
                    missing.append(str(fold.origin))
                    continue
                labels.extend({"role": role, "origin": str(fold.origin), "country_a": a, "country_b": b,
                               "future_count": int(value), "label": int(value > 0), "synthetic": self.synthetic}
                              for (a, b), value in zip(panel.pairs, counts, strict=True))
        write_parquet(self.path("labels.parquet"), labels)
        normalized = [{"event_id": e.event_id, "pair": e.pair, "event_day": str(e.event_day),
                       "added_at": e.added_at.isoformat()} for e in events]
        self.write("data_fingerprints.json", provenance | {"normalized_sha256": digest(normalized),
                   "cohort_sha256": digest(cohort), "candidate_sha256": digest(panel.pairs)})
        if missing or any(not row["history_complete"] for row in origin_records):
            raise CoverageError("At least one registered origin lacks certified history or label coverage, see origins.csv")
        require_coverage((date.fromisoformat(row["date"]) for row in coverage), complete)
        artifacts = {path.name: file_hash(path) for path in self.output.iterdir()
                     if path.name in {"daily_counts.parquet", "daily_graph_features.parquet", "events.parquet",
                                      "labels.parquet", "country_registry.csv", "cohort.csv", "origins.csv",
                                      "candidate_pairs.parquet", "coverage.parquet", "data_fingerprints.json",
                                      "cleaning_audit.json"}}
        data = {"countries": list(countries), "provenance": provenance, "artifacts": artifacts,
                "coverage": source_coverage(coverage), "data_hash": digest(normalized), "cohort_hash": digest(cohort)}
        self.write("prepared.json", data)
        self.status("complete", "prepare")
        self.prepared_panel = panel
        return data

    def load_panel(self):
        if hasattr(self, "prepared_panel"):
            return self.prepared_panel
        prepared = self.prepare()
        complete = {date.fromisoformat(row["date"]) for row in read_parquet(self.path("coverage.parquet"))
                    if row["status"] == "complete"}
        events = (Event(row["event_id"], row["country_a"], row["country_b"], date.fromisoformat(row["event_day"]),
                        datetime.fromisoformat(row["added_at_utc"]))
                  for row in read_parquet(self.path("events.parquet")))
        self.prepared_panel = panel_for(self.config, events, prepared["countries"], complete)
        return self.prepared_panel

    def load_foundation(self):
        from .models import load_timestral

        if self.timestral is None and self.backend_error is None:
            try:
                self.timestral, provenance = load_timestral()
                self.write("timestral_backend.json", provenance)
            except (OSError, RuntimeError, ImportError, ValueError) as exc:
                self.backend_error = str(exc)
        return self.timestral

    def forecast_batch(self, model, history, start, end):
        import numpy as np

        from .models import forecast_classical

        counts = history.counts[start:end]
        if model.startswith(DEMO_FORECAST):
            level = counts[:, -30:].mean(axis=1)
            forecast = np.repeat(level[:, None], 30, axis=1)
            if self.config.get("multi_year"):
                forecast += 0.01 * history.covariates[start:end, -1, :1]
            return {"forecast": forecast, "raw": forecast, "status": ["ok"] * len(counts),
                    "error": [None] * len(counts), "min_raw": level.tolist(), "n_values_clipped": [0] * len(counts)}
        if model in ("arima", "prophet"):
            workers = self.config["execution"]["max_concurrent_classical_workers"]
            seed = self.config["random_seed"]
            if workers == 1 or len(counts) == 1:
                return forecast_classical(model, counts, history.origin, seed=seed)
            if self.classical_pool is None:
                self.classical_pool = ProcessPoolExecutor(
                    max_workers=workers, mp_context=get_context("spawn"),
                    initializer=set_numerical_threads, initargs=(max(1, self.threads // workers),))
            pending = [self.classical_pool.submit(forecast_classical, model, batch, history.origin, seed=seed)
                       for batch in np.array_split(counts, min(workers, len(counts)))]
            parts = [future.result() for future in pending]
            return {key: np.concatenate([part[key] for part in parts]) if key in ("raw", "forecast")
                    else [row for part in parts for row in part[key]] for key in parts[0]}
        return self.timestral.forecast(counts, history.covariates[start:end] if model == "timestral_graph" else None)

    def forecasts(self, model, history, deadline=None):
        provenance = self.model_provenance(model)
        batch_size = self.config["models"].get("timestral", {}).get("batch_size", 32)
        rows = []
        for start in range(0, len(history.pairs), batch_size):
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("Wall-time cap reached. Completed forecast batches are retained")
            end = min(start + batch_size, len(history.pairs))
            pairs = history.pairs[start:end]
            identity = self.identity | {"history_hash": history.hash, "model": provenance, "pairs": [list(pair) for pair in pairs]}

            def compute():
                before = perf_counter()
                result = self.forecast_batch(model, history, start, end)
                elapsed = (perf_counter() - before) / len(pairs)
                batch = []
                for i, (a, b) in enumerate(pairs):
                    ok = result["status"][i] != "failed"
                    batch.append({"origin": str(history.origin), "model_id": model,
                                  "country_a": a, "country_b": b, "input_hash": history.hash,
                                  "synthetic": self.synthetic, "status": result["status"][i],
                                  "raw_forecast": result["raw"][i].tolist() if ok else None,
                                  "forecast": result["forecast"][i].tolist() if ok else None,
                                  "n_values_clipped": result["n_values_clipped"][i],
                                  "min_raw": result["min_raw"][i], "runtime_seconds": elapsed,
                                  "error_reason": result["error"][i],
                                  "optimizer_warnings": result.get("warnings", [[]] * len(pairs))[i],
                                  "optimizer_diagnostics_json": json.dumps(
                                      result.get("diagnostics", [{}] * len(pairs))[i], allow_nan=False),
                                  "raw_forecast_scope": "returned_after_backend_clipping" if model.startswith("timestral_")
                                  else "returned_before_adapter_clipping"})
                return batch

            batch, hit = checkpoint(self.path("checkpoints"), model, str(history.origin),
                                    start // batch_size, identity, compute)
            if [(row["country_a"], row["country_b"]) for row in batch] != list(pairs):
                raise DataContractError(f"Checkpoint pair order mismatch for {model} {history.origin}")
            rows.extend(row | {"cache_hit": hit} for row in batch)
        return rows

    def model_provenance(self, model):
        settings = self.config["models"].get({
            STATIC: "static_logistic", "timestral_graph": "timestral", "timestral_count_only": "timestral",
        }.get(model, model), {})
        if model.startswith(DEMO_FORECAST):
            identity = {"backend_kind": "fake", "backend": "deterministic_synthetic_stub"}
        elif model in DIRECT:
            identity = {"backend_kind": "deterministic_rule"}
        elif model.startswith("timestral_"):
            identity = {"backend_kind": "real"}
            if self.path("timestral_backend.json").exists():
                identity |= self.read("timestral_backend.json")
                identity |= {"library": "timestral", "version": identity["timestral_version"]}
        else:
            library = {"arima": "statsmodels", "prophet": "prophet", STATIC: "scikit-learn"}[model]
            identity = {"backend_kind": "real", "library": library, "version": self.env["packages"][library]}
        return {"model_id": model, "settings_sha256": digest(settings), **identity}

    def labels_by_origin(self, roles):
        panel = self.load_panel()
        pair_order = {pair: i for i, pair in enumerate(panel.pairs)}
        by_origin = {}
        for row in read_parquet(self.path("labels.parquet"), [("role", "in", list(roles))]):
            key = (row["country_a"], row["country_b"])
            group = by_origin.setdefault(row["origin"], {})
            if key in group or key not in pair_order:
                raise DataContractError("Duplicate or unknown label key")
            group[key] = row["label"]
        expected = {str(f.origin) for role in roles for f in self.folds[role]}
        if set(by_origin) != expected:
            raise DataContractError("Stored outcomes do not match the expected role origins")
        for origin, group in by_origin.items():
            if set(group) != set(panel.pairs):
                raise DataContractError(f"Incomplete truth panel for {origin}")
        return {origin: [group[pair] for pair in panel.pairs] for origin, group in by_origin.items()}

    def read_head(self, model):
        path = self.path(f"fitted/{model}.json")
        if not path.exists():
            return None
        record = read_json(path)
        if record["model_id"] != model or record["id"] != digest({k: v for k, v in record.items() if k != "id"}):
            raise DataContractError(f"Invalid fitted head for {model}")
        forecast_sha = record["provenance"].get("calibration_forecasts_sha256")
        if forecast_sha:
            calibration = self.path(f"forecasts/calibration_{model}.parquet")
            if not calibration.is_file() or file_hash(calibration) != forecast_sha:
                raise DataContractError(f"Corrupt or missing calibration artifacts for {model}")
        return record

    def fit_provenance(self, folds, row_hash, **metadata):
        return {"label_start": str(min(f.label_start for f in folds)),
                "label_end": str(max(f.label_end for f in folds)),
                "origins": [str(f.origin) for f in folds], "row_hash": row_hash,
                "years": sorted({f.year for f in folds}), **metadata}

    def fit(self, deadline=None):
        import numpy as np

        from .models import fit_forecast_mapper, fit_topology_logistic

        panel = self.load_panel()
        self.status("running", "fit")
        heads, errors = {}, {}
        if STATIC in self.required:
            try:
                training, validation = (self.folds[k] for k in ("train", "validation"))
                labels = self.labels_by_origin(("train", "validation"))
                assert_chronology([f.label_end for f in training], validation[0].origin)
                assert_chronology([f.label_end for f in training + validation], self.folds["test"][0].origin)
                train_x, val_x = (np.concatenate([panel.history(f.origin).topology for f in folds])
                                  for folds in (training, validation))
                train_y, val_y = (np.concatenate([labels[str(f.origin)] for f in folds])
                                  for folds in (training, validation))
                val_origins = [str(f.origin) for f in validation for _ in panel.pairs]
                row_hash = digest([train_x.tolist(), train_y.tolist(), val_x.tolist(), val_y.tolist(), val_origins,
                                   [str(f.origin) for f in training], panel.pairs])
                prior = self.read_head(STATIC)
                if prior and prior["provenance"]["row_hash"] == row_hash:
                    heads[STATIC] = prior
                else:
                    fitted, c, ap = fit_topology_logistic(train_x, train_y, val_x, val_y, val_origins)
                    heads[STATIC] = freeze_head(fitted, STATIC, self.fit_provenance(
                        training + validation, row_hash, training_rows=len(train_y), validation_rows=len(val_y),
                        selected_C=c, validation_macro_ap={str(key): value for key, value in ap.items()}))
                    self.write(f"fitted/{STATIC}.json", heads[STATIC])
            except (DataContractError, ValueError, RuntimeError, ImportError) as exc:
                errors[STATIC] = str(exc)

        if self.folds.get("calibration"):
            calibration = self.folds["calibration"]
            if len(calibration) != 12 or any(f.year != 2023 for f in calibration):
                raise DataContractError("Forecast mapping requires the complete 2023 origin schedule")
            assert_chronology([f.label_end for f in calibration], self.folds["test"][0].origin)
            labels = self.labels_by_origin(("calibration",))
            self.profile(panel, calibration)
            for model in self.forecast_ids:
                try:
                    if model.startswith("timestral_") and self.load_foundation() is None:
                        raise DataContractError(f"Timestral unavailable: {self.backend_error}")
                    backend = self.model_provenance(model)
                    provenance = self.fit_provenance(calibration, None, backend=backend)
                    prior = self.read_head(model)
                    if prior and all(prior["provenance"][key] == value
                                     for key, value in provenance.items() if key != "row_hash"):
                        heads[model] = prior
                        continue
                    rows = [row for f in calibration for row in self.forecasts(model, panel.history(f.origin), deadline)]
                    write_parquet(self.path(f"forecasts/calibration_{model}.parquet"), rows)
                    if len(rows) != 12 * len(panel.pairs) or any(
                        row["status"] not in {"ok", "constant_series"} for row in rows
                    ):
                        raise DataContractError("Incomplete or failed calibration forecasts; inspect forecast artifacts")
                    targets = [y for f in calibration for y in labels[str(f.origin)]]
                    values = [row["forecast"] for row in rows]
                    fitted = fit_forecast_mapper(values, targets)
                    row_hash = digest([[r["origin"], r["country_a"], r["country_b"], r["forecast"], y]
                                       for r, y in zip(rows, targets, strict=True)])
                    heads[model] = freeze_head(fitted, model, self.fit_provenance(
                        calibration, row_hash, backend=backend, fitting_rows=len(targets),
                        calibration_forecasts_sha256=file_hash(self.path(f"forecasts/calibration_{model}.parquet")),
                        class_counts={str(k): v for k, v in Counter(targets).items()}))
                    self.write(f"fitted/{model}.json", heads[model])
                except (DataContractError, ValueError, RuntimeError, ImportError) as exc:
                    errors[model] = str(exc)
        self.write("fit_status.json", {"completed": {model: head["id"] for model, head in heads.items()},
                                      "errors": errors})
        self.status("failed" if errors else "complete", "fit", errors or None)
        return heads, errors

    def profile(self, panel, calibration):
        if self.synthetic or self.path("backend_profile.json").exists():
            return
        import numpy as np

        from .models import forecast_classical

        items = {}
        representative = None
        for fold in calibration:
            history = panel.history(fold.origin)
            nonconstant = np.flatnonzero(np.ptp(history.counts, axis=1))
            if len(nonconstant):
                representative = (history, nonconstant[:self.config["models"]["timestral"]["batch_size"]])
                break
        if representative:
            history, indices = representative
            counts = history.counts[indices]
            for model in ("arima", "prophet"):
                before = perf_counter()
                result = forecast_classical(model, counts[:1], history.origin)
                items[model] = {"seconds": perf_counter() - before, "pairs": 1,
                                "status": result["status"], "errors": result["error"]}
            adapter = self.load_foundation()
            if adapter:
                before = perf_counter()
                result = adapter.forecast(counts, history.covariates[indices])
                items["timestral_graph"] = {"seconds": perf_counter() - before, "pairs": len(counts),
                                           "status": result["status"], "errors": result["error"]}
            else:
                items["timestral_graph"] = {"status": "blocked", "error": self.backend_error}
        self.write("backend_profile.json", items or {"status": "no_nonconstant_calibration_history"})

    def evaluate(self, heads=None, fit_errors=None, deadline=None):
        from .evaluation import evaluate_predictions, write_evaluation

        panel = self.load_panel()
        self.status("running", "evaluate")
        if heads is None:
            fit_state = self.read("fit_status.json")
            heads = {model: self.read_head(model) for model in fit_state["completed"]}
            if any(head is None or head["id"] != fit_state["completed"][model] for model, head in heads.items()):
                raise DataContractError("Fitted model artifacts disagree with fit status")
            fit_errors = fit_state["errors"]
        fit_errors = dict(fit_errors or {})
        if any(model.startswith("timestral_") and model in heads for model in self.forecast_ids):
            self.load_foundation()
        for model, head in heads.items():
            assert_chronology([date.fromisoformat(head["provenance"]["label_end"])], self.folds["test"][0].origin)
            if model.startswith("timestral_") and self.backend_error:
                fit_errors[model] = self.backend_error
            elif model in self.forecast_ids and head["provenance"]["backend"] != self.model_provenance(model):
                fit_errors[model] = "Backend provenance changed since calibration"

        predictions, activity, forecast_rows = [], {}, []
        for fold in self.folds["test"]:
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError("Wall-time cap reached. Completed forecast batches are retained")
            history = panel.history(fold.origin)
            or_key = str(fold.origin)
            activity[or_key] = {pair: bool(n) for pair, n in zip(panel.pairs, history.recent, strict=True)}
            direct = {"persistence_binary": history.recent > 0, "recent_count30": history.recent,
                      "jaccard": history.topology[:, 0], "common_neighbors": history.topology[:, 1],
                      "preferential_attachment": history.covariates[:, -1, 1]}
            for model in self.required:
                head = heads.get(model)
                if model in fit_errors or (model not in direct and model != DEMO_FORECAST and head is None):
                    reason = fit_errors.get(model, "Required forecast or topology mapping is unavailable")
                    fields = [{"status": "blocked", "error_reason": reason}] * len(panel.pairs)
                elif model in direct:
                    fields = [{"score": float(value)} for value in direct[model]]
                elif model == STATIC:
                    fields = [{"score": float(value), "probability": float(value)}
                              for value in apply_head(head, history.topology)]
                else:
                    raw = self.forecasts(model, history, deadline)
                    forecast_rows.extend(raw)
                    fields = []
                    valid = [r["forecast"] for r in raw if r["forecast"] is not None]
                    values = iter(apply_head(head, valid) if head and valid else [v[0] for v in valid])
                    for row in raw:
                        value = float(next(values)) if row["forecast"] is not None else None
                        fields.append({"score": value, "probability": value if head else None,
                                       "status": row["status"], "error_reason": row["error_reason"],
                                       "mapper_id": head["id"] if head else None,
                                       "runtime_seconds": row["runtime_seconds"]})
                for (a, b), value in zip(panel.pairs, fields, strict=True):
                    predictions.append({"schema_version": VERSION, "run_id": self.id, "origin": or_key,
                                        "model_id": model, "country_a": a, "country_b": b,
                                        "synthetic": self.synthetic, "score": None, "probability": None,
                                        "status": "ok", "error_reason": None, "mapper_id": None,
                                        "runtime_seconds": 0.0, "input_hash": history.hash,
                                        "configuration_hash": self.config_hash, **value})

        write_parquet(self.path("predictions.parquet"), predictions)
        if forecast_rows:
            for model in self.forecast_ids:
                rows = [r for r in forecast_rows if r["model_id"] == model]
                if rows:
                    write_parquet(self.path(f"forecasts/test_{model}.parquet"), rows)
        failures = [r for r in predictions if r["status"] not in {"ok", "constant_series"}]
        missing = sorted({r["model_id"] for r in failures})
        if failures:
            self.status("failed", "evaluate", f"{len(failures)} blocked or failed scores")
            self.manifest(predictions)
            self.completion("evaluate", "incomplete_scores",
                            f"{len(failures)} blocked or failed scores, see predictions.parquet and fit_status.json",
                            missing, len(self.folds["test"]) - len({r["origin"] for r in failures}), predictions)
            return False

        # Only after the immutable score panel has been written do final outcomes enter evaluation.
        labels = self.labels_by_origin(("test",))
        outcome = {origin: dict(zip(panel.pairs, scores, strict=True)) for origin, scores in labels.items()}
        joined = []
        for row in predictions:
            origin = row["origin"]
            pair = (row["country_a"], row["country_b"])
            joined.append(row | {"label": outcome[origin][pair],
                                 "active_last_30": activity[origin][pair]})
        origins = [f.origin for f in self.folds["test"]]
        tables = evaluate_predictions(joined, self.config, origins, panel.pairs)
        manifest = self.manifest(predictions)
        completion = self.completion(completed_origins=len(origins), predictions=predictions, publish=False)
        write_evaluation(self.output, tables, self.config, manifest, completion=completion)
        self.status("complete", "evaluate")
        verified = [self.path(name) for name in ("predictions.parquet", "metric_exports_manifest.json",
                                                 "fit_status.json")]
        verified.extend(self.path("fitted").glob("*.json"))
        verified.extend(self.path("forecasts").glob("*.parquet"))
        self.write("evaluated.json", {"origins": len(origins), "score_count": len(predictions), "hashes": {
            str(path.relative_to(self.output)): file_hash(path) for path in verified}})

        self.manifest(predictions)
        self.write("completion.json", completion)
        self.manifest(predictions)
        return True

    def existing_evaluation(self):
        if not self.path("evaluated.json").is_file():
            return None
        from .evaluation import render_report

        receipt = self.read("evaluated.json")
        for name, sha in receipt["hashes"].items():
            if not self.path(name).is_file() or file_hash(self.path(name)) != sha:
                raise DataContractError(f"Corrupt or missing evaluated artifact {name}")
        predictions = read_parquet(self.path("predictions.parquet"))
        completion = self.completion(completed_origins=receipt["origins"], predictions=predictions, publish=False)
        render_report(self.output, self.config, self.read("run_manifest.json"), completion=completion)
        self.write("completion.json", completion)
        self.manifest(predictions)
        return completion

    @cached_property
    def quality(self):
        receipt = ROOT / "outputs/verification/quality.json"
        if receipt.is_file():
            value = read_json(receipt)
            if (value.get("code_hash") == self.code_hash and value.get("lock_sha256") == self.env["lock_sha256"]
                    and value.get("evidence_sha256")
                    and all((ROOT / name).is_file() and file_hash(ROOT / name) == artifact_hash
                            for name, artifact_hash in value["evidence_sha256"].items())):
                return value
        return {}

    def completion(self, stage=None, code=None, detail=None, missing=None, completed_origins=0, predictions=None, *, publish=True):
        quality = self.quality
        engineering = quality.get("engineering_complete", False)
        demo = quality.get("demo_complete", False) or (self.synthetic and bool(predictions))
        blockers = [{"stage": stage, "code": code, "detail": detail}] if stage else []
        if not self.synthetic and not engineering:
            blockers.append({"stage": "verification", "code": "engineering_evidence_missing",
                             "detail": "Run scripts/verify_application.py against this code and lock"})
        if not self.synthetic and not demo:
            blockers.append({"stage": "verification", "code": "demo_evidence_missing",
                             "detail": "Generate the offline demo and verification receipt"})
        real_timestral = bool(not self.synthetic and predictions
                              and not set(missing or ()) & {"timestral_graph", "timestral_count_only"})
        if self.synthetic:
            blockers.append({"stage": "research", "code": "synthetic_profile",
                             "detail": "Real GDELT source and genuine research model execution required"})
        elif real_timestral and not quality.get("genuine_smoke_complete", False):
            blockers.append({"stage": "verification", "code": "model_smoke_evidence_missing",
                             "detail": "Run scripts/smoke_models.py and regenerate the verification receipt"})
        result = {"schema_version": VERSION, "run_id": self.id, "engineering_complete": engineering,
                  "demo_complete": demo, "research_complete": bool(real_timestral and not blockers),
                  "real_data_executed": not self.synthetic and self.path("prepared.json").exists(),
                  "real_timestral_209m_executed": real_timestral,
                  "completed_test_origins": completed_origins,
                  "missing_models": list(missing) if missing is not None else (
                      list(self.required) if not predictions else []), "blockers": blockers}
        self.validate_schema("completion", result)
        if publish:
            self.write("completion.json", result)
        return result

    def validate_schema(self, name, value):
        from jsonschema import Draft202012Validator, FormatChecker

        Draft202012Validator(read_json(ROOT / f"schemas/{name}.schema.json"),
                            format_checker=FormatChecker()).validate(value)

    def manifest(self, predictions):
        prepared = self.read("prepared.json")
        by_model = {model: [] for model in self.required}
        for row in predictions:
            by_model[row["model_id"]].append(row)
        models = []
        for model, rows in by_model.items():
            fitted = self.read_head(model)
            models.append(self.model_provenance(model) | {
                "status": "complete" if rows and all(r["status"] in {"ok", "constant_series"} for r in rows)
                          else "blocked" if not rows or all(r["status"] == "blocked" for r in rows) else "failed",
                "fit_label_last_day": fitted["provenance"]["label_end"] if fitted else None,
                "fitted_id": fitted["id"] if fitted else None,
                "status_counts": dict(Counter(r["status"] for r in rows)),
                "runtime_seconds": sum(r["runtime_seconds"] for r in rows)})
        artifact_index = [
            {"path": str(path.relative_to(self.output)), "sha256": file_hash(path), "bytes": path.stat().st_size}
            for path in sorted(self.output.rglob("*"))
            if path.is_file() and path.name != "run_manifest.json"
            and not path.name.startswith(".") and "checkpoints" not in path.relative_to(self.output).parts
        ]
        manifest = {"schema_version": VERSION, "run_id": self.id,
                    "profile": self.config["profile"], "synthetic": self.synthetic,
                    "created_at": self.read("run_request.json")["created_at"],
                    "config_sha256": self.config_hash, "code_sha256": self.code_hash,
                    "data_sha256": prepared["data_hash"], "cohort_sha256": prepared["cohort_hash"],
                    "country_registry_sha256": file_hash(self.path("country_registry.csv")),
                    "environment_lock_sha256": self.env["lock_sha256"],
                    "verification": self.quality.get("evidence_sha256", {}),
                    "source_coverage": prepared["coverage"], "source_provenance": prepared["provenance"],
                    "candidate_count": self.config["cohort"]["expected_pairs"], "models": models,
                    "planned_test_origins": [str(f.origin) for f in self.folds["test"]],
                    "artifact_index": artifact_index}
        self.validate_schema("run_manifest", manifest)
        self.write("run_manifest.json", manifest)
        return manifest


def freeze_head(model, model_id, provenance):
    scaler, classifier = (model.named_steps[key] for key in ("standardscaler", "logisticregression"))
    artifact = {"model_id": model_id, "provenance": provenance, "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(), "weights": classifier.coef_[0].tolist(),
                "intercept": float(classifier.intercept_[0])}
    return artifact | {"id": digest(artifact)}


def apply_head(head, values):
    import numpy as np
    from scipy.special import expit

    return expit(((np.asarray(values) - head["mean"]) / head["scale"]) @ head["weights"] + head["intercept"])
