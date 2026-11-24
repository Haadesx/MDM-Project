import csv
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone

from .artifacts import file_hash, read_json
from .domain import CoverageError, DataContractError
from .ingestion import classify_event

REQUIRED = ("SQLDATE", "DATEADDED", "EventCode", "Actor1CountryCode", "Actor2CountryCode")
COVERAGE_COLUMNS = ("date", "status", "evidence_kind", "evidence_id", "extraction_start_utc",
                    "extraction_end_utc", "source_row_count", "eligible_row_count",
                    "expected_parts", "received_parts", "source_snapshot_id", "notes")


def source_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise DataContractError(f"Missing or invalid input file: {name}")
    return path


def field_map(names):
    groups = {}
    for name in names:
        groups.setdefault(name.casefold(), []).append(name)
    if any(len(groups.get(name.casefold(), [])) != 1 for name in REQUIRED):
        raise DataContractError(f"Export requires unambiguous columns {REQUIRED}")
    ids = groups.get("globaleventid", [])
    if not ids or len(ids) > 2 or len(ids) == 2 and set(ids) != {"GlobalEventID", "GLOBALEVENTID"}:
        raise DataContractError("Export requires unambiguous GLOBALEVENTID alias columns")
    return {name: groups[name.casefold()][0] for name in REQUIRED} | {
        ("GlobalEventID" if name == "GlobalEventID" else "GLOBALEVENTID"): name for name in ids}


def export_rows(path, spec):
    if path.suffix.lower() == ".parquet":
        import pyarrow as pa
        import pyarrow.parquet as pq

        data = pq.ParquetFile(path)
        fields = field_map(data.schema_arrow.names)
        code_type = data.schema_arrow.field(fields["EventCode"]).type
        if not (pa.types.is_string(code_type) or pa.types.is_large_string(code_type)):
            raise DataContractError("Parquet EventCode must use a string schema")
        for batch in data.iter_batches(columns=list(fields.values())):
            for row in batch.to_pylist():
                yield {target: row[source] for target, source in fields.items()}
    elif path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = spec.get("delimiter")
        if delimiter not in {",", "\t", "|", ";"}:
            raise DataContractError(f"Declare the delimiter for {spec['path']}")
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream, delimiter=delimiter)
            fields = field_map(reader.fieldnames or [])
            for row in reader:
                if None in row or any(row[source] is None for source in fields.values()):
                    raise DataContractError(f"Wrong number of fields in {spec['path']}:{reader.line_num}")
                yield {target: row[source] for target, source in fields.items()}
    else:
        raise DataContractError(f"Unsupported export format: {spec['path']}")


def read_export(root, files, countries, start, end):
    events = {}
    directions = {}
    audit = Counter()
    year_counts = Counter()
    lag_histogram = Counter()
    excluded_codes = Counter()
    for spec in files:
        path = source_file(root, spec["path"])
        for index, row in enumerate(export_rows(path, spec), 1):
            audit["source_rows"] += 1
            try:
                event, reason = classify_event(row, countries)
                if reason == "unknown_country":
                    excluded_codes.update(str(row[k]).strip() for k in
                                          ("Actor1CountryCode", "Actor2CountryCode")
                                          if str(row[k]).strip() not in countries)
                if event is None:
                    audit[reason] += 1
                    continue
                if not start <= event.observed_day < end:
                    raise DataContractError(f"DATEADDED outside declared extraction: {event.observed_day}")
                existing = events.setdefault(event.event_id, event)
                if existing != event:
                    raise DataContractError(f"Conflicting identity for event {event.event_id}")
                directions.setdefault(event.event_id, set()).add(
                    (str(row["Actor1CountryCode"]), str(row["Actor2CountryCode"])))
                audit["eligible_copies"] += 1
            except DataContractError as exc:
                raise DataContractError(f"{spec['path']} record {index}: {exc}") from exc

    for event in events.values():
        year_counts[event.observed_day.year] += 1
        lag_histogram[(event.observed_day - event.event_day).days] += 1
    audit["duplicate"] = audit["eligible_copies"] - len(events)
    return tuple(events[key] for key in sorted(events)), {
        **dict.fromkeys(["source_rows", "relation", "blank_country", "unknown_country", "self_pair"], 0),
        **audit, "malformed": 0, "conflicts": 0, "eligible_unique": len(events),
        "eligible_by_year": {str(k): v for k, v in year_counts.items()},
        "lag_days_histogram": {str(k): v for k, v in lag_histogram.items()},
        "excluded_country_codes": dict(excluded_codes),
    }, {key: sorted(value) for key, value in directions.items()}


def read_coverage(path, start, end):
    if not path.is_file():
        raise CoverageError(f"Missing extraction coverage manifest: {path.name}")
    if path.suffix == ".parquet":
        from .artifacts import read_parquet

        rows = read_parquet(path)
    else:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
    by_day = {}
    complete = set()
    for row in rows:
        if not set(COVERAGE_COLUMNS) <= row.keys():
            raise CoverageError("Coverage manifest lacks required fields")
        day = date.fromisoformat(str(row["date"]))
        if day in by_day or not start <= day < end:
            raise CoverageError(f"Duplicate or out-of-range coverage day {day}")
        if row["status"] not in {"complete", "failed", "missing"}:
            raise CoverageError(f"Unrecognized coverage status on {day}")
        if row["status"] == "complete":
            try:
                midnight = datetime.combine(day, time.min, timezone.utc)
                left, right = (datetime.fromisoformat(str(row[field]).replace("Z", "+00:00"))
                               for field in ("extraction_start_utc", "extraction_end_utc"))
                if not left <= midnight < midnight + timedelta(days=1) <= right:
                    raise ValueError("partial day")
                if not all(isinstance(row[k], str) and row[k].strip() for k in
                           ("evidence_kind", "evidence_id", "source_snapshot_id")):
                    raise ValueError("missing extraction evidence")
                expected, received = (None if row[k] in (None, "") else int(row[k])
                                      for k in ("expected_parts", "received_parts"))
                if expected != received or (expected is not None and expected < 1):
                    raise ValueError("incomplete source inventory")
                counts = [None if row[k] in (None, "") else int(row[k])
                          for k in ("source_row_count", "eligible_row_count")]
                if any(value is not None and value < 0 for value in counts):
                    raise ValueError("negative row count")
                if None not in counts and counts[1] > counts[0]:
                    raise ValueError("eligible rows exceed source rows")
            except (ValueError, TypeError) as exc:
                raise CoverageError(f"Invalid complete-day evidence for {day}: {exc}") from exc
            complete.add(day)
        by_day[day] = {key: row[key] for key in COVERAGE_COLUMNS} | {"date": day.isoformat()}
    for offset in range((end - start).days):
        day = start + timedelta(days=offset)
        by_day.setdefault(day, dict.fromkeys(COVERAGE_COLUMNS) |
                          {"date": day.isoformat(), "status": "missing", "notes": "No source certificate"})
    return complete, [by_day[day] for day in sorted(by_day)]


def read_registry(path):
    if not path.is_file():
        raise DataContractError(f"Missing CAMEO country registry: {path}")
    provenance = read_json(path.with_suffix(".json"))
    lookup = source_file(path.parent, provenance["lookup"])
    if file_hash(lookup) != provenance["sha256"] or file_hash(path) != provenance["registry_sha256"]:
        raise DataContractError("CAMEO country registry provenance hash mismatch")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    countries = {r["code"] for r in rows if r["eligible"] == "true"}
    if not countries or len({r["code"] for r in rows}) != len(rows) or any(
        not re.fullmatch("[A-Z]{3}", r["code"]) or r["eligible"] not in {"true", "false"}
        or not r["reason"] or r["source_version"] != provenance["sha256"] for r in rows
    ):
        raise DataContractError("Invalid CAMEO country registry")
    return countries, rows, provenance


def local_input(root, config, project):
    if not (root / "source.json").is_file():
        raise DataContractError(f"Missing certified GDELT 2.0 export manifest at {root / 'source.json'}")
    source = read_json(root / "source.json")
    config_data = config["data"]
    if (source.get("dataset") != config_data["dataset"] or source.get("synthetic") is not False
            or not source.get("snapshot") or not source.get("extraction_scope")
            or not source.get("extracted_at_utc") or not source.get("files")
            or source.get("start") != config_data["start"]
            or source.get("end_exclusive") != config_data["end_exclusive"]):
        raise DataContractError("Source must describe the complete requested GDELT 2.0 DATEADDED extraction")
    try:
        extracted = datetime.fromisoformat(source["extracted_at_utc"].replace("Z", "+00:00"))
        if extracted.utcoffset() != timedelta(0):
            raise ValueError("non-UTC offset")
    except (ValueError, AttributeError) as exc:
        raise DataContractError("Source extracted_at_utc must be an ISO timestamp in UTC") from exc
    start, end = (date.fromisoformat(config_data[k]) for k in ("start", "end_exclusive"))
    registry = project / config["cohort"]["registry"]
    countries, registry_rows, registry_source = read_registry(registry)
    coverage_path = source_file(root, source.get("coverage", "coverage.csv"))
    complete, coverage = read_coverage(coverage_path, start, end)
    files = [source_file(root, entry["path"]) for entry in source["files"]]
    fingerprints = {str(path.relative_to(root.resolve())): {"sha256": file_hash(path), "bytes": path.stat().st_size}
                    for path in (root.resolve() / "source.json", coverage_path, *files)}
    for entry, path in zip(source["files"], files, strict=True):
        if entry.get("sha256") and fingerprints[str(path.relative_to(root.resolve()))]["sha256"] != entry["sha256"]:
            raise DataContractError(f"Source hash mismatch: {entry['path']}")
    events, audit, directions = read_export(root, source["files"], countries, start, end)
    counts = Counter(str(event.observed_day) for event in events)
    for row in coverage:
        if row["status"] != "complete":
            continue
        if row["source_snapshot_id"] != source["snapshot"]:
            raise CoverageError(f"Coverage snapshot disagrees with source snapshot on {row['date']}")
        for field in ("source_row_count", "eligible_row_count"):
            if row[field] not in (None, "") and int(row[field]) < counts[row["date"]]:
                raise CoverageError(f"Certified {field.replace('_', ' ')} below distinct imported events on {row['date']}")
    for name, fingerprint in fingerprints.items():
        if file_hash(source_file(root, name)) != fingerprint["sha256"]:
            raise DataContractError(f"Source changed during validation: {name}")
    return events, complete, coverage, registry_rows, audit, directions, {
        "source": source, "files": fingerprints, "registry": registry_source}
