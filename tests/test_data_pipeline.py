import csv
import json
from datetime import date, timedelta

import pytest

from cooperalink.domain import CoverageError, DataContractError
from cooperalink.ingestion import normalize_event
from cooperalink.source import read_export, read_coverage
from cooperalink.features import FeaturePanel
from tests.helpers import complete_days, fixture_events, COUNTRIES, ORIGIN


def test_typed_exports_and_overlap(tmp_path):
    row = dict(GLOBALEVENTID="0042", GlobalEventID="42", SQLDATE="20200101",
               DATEADDED="20200103000000", Actor1CountryCode="USA",
               Actor2CountryCode="CAN", EventCode="061")
    for filename, delimiter in [("a.csv", ","), ("b.tsv", "\t")]:
        with (tmp_path / filename).open("w") as stream:
            writer = csv.DictWriter(stream, row, delimiter=delimiter)
            writer.writeheader()
            writer.writerow(row)
    import pyarrow as pa
    import pyarrow.parquet as pq

    pq.write_table(pa.Table.from_pylist([row]), tmp_path / "c.parquet")
    manifest = [{"path": "a.csv", "delimiter": ","}, {"path": "b.tsv", "delimiter": "\t"},
                {"path": "c.parquet"}]
    events, audit, _ = read_export(tmp_path, manifest, {"CAN", "USA"}, date(2020, 1, 1), date(2021, 1, 1))
    assert [(event.event_id, event.observed_day) for event in events] == [("42", date(2020, 1, 3))]
    assert audit["duplicate"] == 2
    with pytest.raises(DataContractError, match="conflicting"):
        normalize_event(row | {"GlobalEventID": "43"}, {"CAN", "USA"})
    pq.write_table(pa.Table.from_pylist([row | {"EventCode": 61}]), tmp_path / "c.parquet")
    with pytest.raises(DataContractError, match="string"):
        read_export(tmp_path, manifest, {"CAN", "USA"}, date(2020, 1, 1), date(2021, 1, 1))


def test_coverage_requires_full_day_evidence(tmp_path):
    row = dict(date="2020-01-01", status="complete", evidence_kind="query_receipt",
               evidence_id="job", extraction_start_utc="2020-01-01T00:00:00Z",
               extraction_end_utc="2020-01-02T00:00:00Z", source_row_count="0",
               eligible_row_count="0", expected_parts="", received_parts="",
               source_snapshot_id="snapshot", notes="")
    with (tmp_path / "coverage.csv").open("w") as stream:
        writer = csv.DictWriter(stream, row)
        writer.writeheader()
        writer.writerows([row, row | {"date": "2020-01-02", "status": "missing"}])
    complete, _ = read_coverage(tmp_path / "coverage.csv", date(2020, 1, 1), date(2020, 1, 4))
    assert complete == {date(2020, 1, 1)}
    with (tmp_path / "coverage.csv").open("w") as stream:
        writer = csv.DictWriter(stream, row)
        writer.writeheader()
        writer.writerow(row | {"extraction_end_utc": "2020-01-01T23:00:00Z"})
    with pytest.raises(CoverageError, match="2020-01-01"):
        read_coverage(tmp_path / "coverage.csv", date(2020, 1, 1), date(2020, 1, 4))


def test_history_is_aligned_and_independent_of_future_events():
    events = fixture_events()
    days = complete_days()
    panel = FeaturePanel(events, COUNTRIES, days)
    before = FeaturePanel((e for e in events if e.observed_day <= ORIGIN), COUNTRIES, days)
    history = panel.history(ORIGIN)
    history_before = before.history(ORIGIN)
    assert history.origins_days[0] == ORIGIN - timedelta(days=89)
    assert history.counts.shape == (6, 90)
    assert history.covariates.shape == (6, 90, 2)
    assert history.hash == history_before.hash
    assert not hasattr(history, "labels")
    assert history.recent.tolist() == [2, 0, 0, 1, 0, 1]
    assert panel.labels(ORIGIN).tolist() == [0, 0, 1, 0, 1, 1]
    assert before.labels(ORIGIN).tolist() == [0] * 6
    with pytest.raises(CoverageError):
        FeaturePanel(events, COUNTRIES, set(days) - {ORIGIN - timedelta(days=118)}).history(ORIGIN)


def test_research_cohort_requires_complete_2020_and_exact_thirty():
    from cooperalink.pipeline import cohort_for, RESEARCH
    from cooperalink.artifacts import read_json

    complete = {date(2020, 1, 1) + timedelta(days=i) for i in range(366)}
    with pytest.raises(CoverageError, match="2020-12-31"):
        cohort_for(read_json(RESEARCH), [], complete - {date(2020, 12, 31)})
    with pytest.raises(DataContractError, match="exactly 30"):
        cohort_for(read_json(RESEARCH), [], complete)


def test_csv_does_not_treat_lost_zero_prefix_as_unrelated_relation():
    row = {"GLOBALEVENTID": 42, "SQLDATE": "20200101", "DATEADDED": "20200101000000",
           "Actor1CountryCode": "USA", "Actor2CountryCode": "CAN", "EventCode": "61"}
    with pytest.raises(DataContractError, match="leading zero"):
        normalize_event(row, {"CAN", "USA"})


@pytest.mark.parametrize("override,message", [
    ({"source_snapshot_id": "different-snapshot"}, "snapshot"),
    ({"source_row_count": "0", "eligible_row_count": "0"}, "row count"),
])
def test_source_certificates_are_bound_to_imported_events(tmp_path, override, message):
    from cooperalink.pipeline import RESEARCH, ROOT
    from cooperalink.artifacts import read_json
    from cooperalink.source import local_input

    source = {"dataset": "GDELT 2.0 Events", "synthetic": False,
              "start": "2020-01-01", "end_exclusive": "2025-01-01",
              "snapshot": "source-snapshot", "extracted_at_utc": "2026-11-20T16:00:00Z",
              "extraction_scope": "Date-bounded 061 export", "files": [{"path": "events.csv", "delimiter": ","}]}
    (tmp_path / "source.json").write_text(json.dumps(source))
    (tmp_path / "events.csv").write_text(
        "GLOBALEVENTID,SQLDATE,DATEADDED,EventCode,Actor1CountryCode,Actor2CountryCode\n"
        "12,20200101,20200101000000,061,USA,CAN\n")
    row = dict(date="2020-01-01", status="complete", evidence_kind="query_receipt",
               evidence_id="job", extraction_start_utc="2020-01-01T00:00:00Z",
               extraction_end_utc="2020-01-02T00:00:00Z", source_row_count="1",
               eligible_row_count="1", expected_parts="", received_parts="",
               source_snapshot_id="source-snapshot", notes="")
    with (tmp_path / "coverage.csv").open("w") as stream:
        writer = csv.DictWriter(stream, row)
        writer.writeheader()
        writer.writerow(row | override)
    with pytest.raises(CoverageError, match=message):
        local_input(tmp_path, read_json(RESEARCH), ROOT)


def test_registered_local_prepare_saves_frozen_435_pair_inventory(tmp_path):
    from cooperalink.artifacts import read_json, read_parquet
    from cooperalink.cli import main
    from cooperalink.pipeline import RESEARCH, ROOT
    from cooperalink.source import COVERAGE_COLUMNS, read_registry

    config = read_json(RESEARCH)
    input_dir, output = tmp_path / "input", tmp_path / "prepare"
    input_dir.mkdir()
    countries, _, _ = read_registry(ROOT / config["cohort"]["registry"])
    selected = sorted(countries)[:30]
    later_country = sorted(countries)[30]
    rows = [(a, b, "20200101") for a, b in zip(selected[:-1], selected[1:], strict=True)]
    rows += [(later_country, selected[0], "20240101")] * 31
    with (input_dir / "events.tsv").open("w") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["GLOBALEVENTID", "SQLDATE", "DATEADDED", "EventCode",
                         "Actor1CountryCode", "Actor2CountryCode"])
        for idx, (a, b, day) in enumerate(rows, 1):
            writer.writerow([idx, day, day + "000000", "061", a, b])
    (input_dir / "source.json").write_text(json.dumps({
        "dataset": config["data"]["dataset"], "synthetic": False, "start": "2020-01-01",
        "end_exclusive": "2025-01-01", "snapshot": "test-receipt", "extraction_scope": "Test fixture",
        "extracted_at_utc": "2026-11-20T16:00:00Z", "files": [{"path": "events.tsv", "delimiter": "\t"}],
    }))
    start, end = date(2020, 1, 1), date(2025, 1, 1)
    with (input_dir / "coverage.csv").open("w") as stream:
        writer = csv.DictWriter(stream, COVERAGE_COLUMNS)
        writer.writeheader()
        for i in range((end - start).days):
            d = start + timedelta(days=i)
            writer.writerow({"date": str(d), "status": "complete", "evidence_kind": "test_fixture",
                             "evidence_id": "test-receipt", "source_snapshot_id": "test-receipt",
                             "extraction_start_utc": f"{start}T00:00:00Z",
                             "extraction_end_utc": f"{end}T00:00:00Z"})
    assert main(["prepare", "--config", str(RESEARCH), "--input", str(input_dir), "--output", str(output)]) == 0
    pairs = read_parquet(output / "candidate_pairs.parquet")
    assert len(pairs) == 435
    assert sorted({row[k] for row in pairs for k in ("country_a", "country_b")}) == selected
    assert read_json(output / "run_manifest.json")["source_coverage"]["complete"]
    assert not read_json(output / "completion.json")["research_complete"]
