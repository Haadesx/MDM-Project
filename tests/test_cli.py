import json
from pathlib import Path

from jsonschema import Draft202012Validator

from cooperalink.cli import main
from cooperalink.artifacts import read_parquet

ROOT = Path(__file__).resolve().parents[1]


def test_offline_fixture_writes_all_six_candidates_and_report(tmp_path, monkeypatch):
    import socket

    def forbid_network(*args, **kwargs):
        raise AssertionError("offline demo attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbid_network)
    output = tmp_path / "demo"
    assert main(["demo", "--config", str(ROOT / "config/demo.json"), "--output", str(output)]) == 0
    rows = read_parquet(output / "predictions.parquet")
    assert len(rows) == 36
    persistence = [r for r in rows if r["model_id"] == "persistence_binary"]
    assert [r["score"] for r in persistence] == [1, 0, 0, 1, 0, 1]
    assert all(row["synthetic"] and "label" not in row for row in rows)
    completion = json.loads((output / "completion.json").read_text())
    Draft202012Validator(json.loads((ROOT / "schemas/completion.schema.json").read_text())).validate(completion)
    assert completion["demo_complete"]
    assert not completion["research_complete"]
    assert "SYNTHETIC" in (output / "report.html").read_text()
    assert main(["report", "--run-id", str(output)]) == 0


def test_missing_research_source_produces_structured_exit(tmp_path, capsys):
    output = tmp_path / "main"
    assert main(["run", "--config", str(ROOT / "config/research.json"), "--input",
                 str(tmp_path / "input"), "--output", str(output)]) != 0
    captured = json.loads(capsys.readouterr().out)
    assert captured["status"] == "blocked"
    completion = json.loads((output / "completion.json").read_text())
    assert not completion["research_complete"]
    assert len(completion["missing_models"]) == 10
    assert "source.json" in completion["blockers"][0]["detail"]


def test_multiyear_freezes_fitted_artifacts_and_reuses_batch_cache(tmp_path):
    output = tmp_path / "multi"
    args = ["demo", "--config", str(ROOT / "config/demo.json"), "--multiyear", "--output", str(output)]
    assert main(args) == 0
    fitness = json.loads((output / "fit_status.json").read_text())
    assert set(fitness["completed"]) == {"static_logistic_topology", "demo_forecast_stub_mapped"}
    fit_dir = output / "fitted"
    topology = json.loads((fit_dir / "static_logistic_topology.json").read_text())
    mapper = json.loads((fit_dir / "demo_forecast_stub_mapped.json").read_text())
    assert topology["provenance"]["years"] == [2021, 2022]
    assert mapper["provenance"]["years"] == [2023]
    assert mapper["provenance"]["fitting_rows"] == 72
    scores = read_parquet(output / "predictions.parquet")
    assert len(scores) == 7 * 12 * 6
    assert main(["resume", "--run-id", str(output)]) == 0
    assert not any(row["cache_hit"] for row in read_parquet(
        output / "forecasts/test_demo_forecast_stub_mapped.parquet"))
    # Simulate a stop after valid forecasts and before the evaluation receipt.
    (output / "evaluated.json").unlink()
    assert main(["resume", "--run-id", str(output)]) == 0
    assert read_parquet(output / "predictions.parquet") == scores
    assert json.loads((fit_dir / "demo_forecast_stub_mapped.json").read_text()) == mapper
    forecasts = read_parquet(output / "forecasts/test_demo_forecast_stub_mapped.parquet")
    assert all(row["cache_hit"] for row in forecasts)
    forecast = next(iter((output / "checkpoints").glob("*.json")))
    artifact = json.loads(forecast.read_text())
    # Calibration forecasts have a separately hash-protected fit receipt after fitting.
    if artifact["key"]["origin"] < "2023-12-31":
        forecast = next(p for p in (output / "checkpoints").glob("*.json")
                        if json.loads(p.read_text())["key"]["origin"] >= "2023-12-31")
    forecast.write_text("{")
    (output / "evaluated.json").unlink()
    assert main(["resume", "--run-id", str(output)]) != 0
    completion = json.loads((output / "completion.json").read_text())
    assert any("Corrupt checkpoint" in blocker["detail"] for blocker in completion["blockers"])


def test_bounded_classical_workers_preserve_pair_positions(tmp_path):
    from types import SimpleNamespace
    from datetime import date

    import numpy as np

    from cooperalink.artifacts import read_json
    from cooperalink.pipeline import RESEARCH, Run

    run = Run(tmp_path, read_json(RESEARCH), tmp_path / "input")
    history = SimpleNamespace(origin=date(2023, 1, 30),
                              counts=np.tile([[0], [1], [2], [3]], (1, 90)))
    try:
        result = run.forecast_batch("arima", history, 0, 4)
        assert result["status"] == ["constant_series"] * 4
        assert result["forecast"].tolist() == [[level] * 30 for level in range(4)]
        assert run.classical_pool is not None
    finally:
        run.close()
