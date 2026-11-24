import importlib.util
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

from cooperalink.domain import DataContractError

ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG = json.loads((ROOT / "config/demo.json").read_text())
RESEARCH_CONFIG = json.loads((ROOT / "config/research.json").read_text())
DEMO_PAIRS = tuple(combinations(DEMO_CONFIG["cohort"]["countries"], 2))
DEMO_ORIGIN = DEMO_CONFIG["origin"]
RESEARCH_ORIGINS = tuple(
    (date(2023, 12, 31) + timedelta(days=30 * index)).isoformat()
    for index in range(12)
)
RESEARCH_PAIRS = tuple(combinations(
    [f"AA{letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] + ["ABA", "ABB", "ABC", "ABD"], 2
))


def prediction_rows(config, origins, pairs):
    forecasts = ("timestral_graph", "timestral_count_only", "arima", "prophet")
    if config.get("multi_year"):
        forecasts += ("demo_forecast_stub_mapped",)
    config_hash = hashlib.sha256(
        json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    for origin in origins:
        for model in config["models"]["required"]:
            for index, (first, second) in enumerate(pairs):
                label = int(index == 0)
                active = index in (0, 1)
                probability = float(label) if model in (*forecasts, "static_logistic_topology") else None
                score = float(active) if model == "persistence_binary" else float(label)
                yield {
                    "schema_version": "1.0.0",
                    "run_id": "evaluation-example",
                    "model_id": model,
                    "origin": origin,
                    "country_a": first,
                    "country_b": second,
                    "label": label,
                    "active_last_30": active,
                    "score": score,
                    "probability": probability,
                    "mapper_id": f"mapper-{model}" if model in forecasts else None,
                    "status": "ok",
                    "synthetic": config["synthetic"],
                    "input_hash": "0" * 64,
                    "configuration_hash": config_hash,
                }


class EvaluationContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("cooperalink.evaluation"))
        from cooperalink import evaluation

        self.evaluation = evaluation
        self.demo_rows = list(prediction_rows(DEMO_CONFIG, [DEMO_ORIGIN], DEMO_PAIRS))

    def evaluate_demo(self):
        return self.evaluation.evaluate_predictions(
            self.demo_rows, DEMO_CONFIG, [DEMO_ORIGIN], DEMO_PAIRS
        )

    def test_rejects_missing_and_duplicate_pair_scores(self):
        missing = self.demo_rows.pop()
        with self.assertRaisesRegex(DataContractError, "pair|panel"):
            self.evaluate_demo()
        self.demo_rows.extend((missing, missing))
        with self.assertRaisesRegex(DataContractError, "duplicate"):
            self.evaluate_demo()

    def test_rejects_cross_model_activity_disagreement(self):
        self.demo_rows[-1]["active_last_30"] = True
        with self.assertRaisesRegex(DataContractError, "disagree"):
            self.evaluate_demo()

    def test_rejects_consistent_scores_from_another_configuration(self):
        for row in self.demo_rows:
            row["configuration_hash"] = "f" * 64
        with self.assertRaisesRegex(DataContractError, "configuration"):
            self.evaluate_demo()

    def test_demo_support_metrics_and_paired_values_reconcile(self):
        tables = self.evaluate_demo()
        metrics = {
            (row["metric"], row["requested_k"]): row
            for row in tables["metrics_by_origin"] if row["model_id"] == "persistence_binary"
        }
        self.assertEqual(metrics["average_precision", None]["value"], 0.5)
        self.assertEqual(metrics["precision_at_k", 10]["effective_k"], 6)
        self.assertEqual(metrics["precision_at_k", 10]["value"], 1 / 6)
        self.assertEqual(metrics["filtered_mrr", None]["positive_query_count"], 2)
        inactive = [
            row for row in tables["conditional_slices"]
            if row["slice"] == "inactive_last_30" and row["metric"] == "average_precision"
        ][0]
        self.assertEqual((inactive["value"], inactive["reason"]), (None, "no_positives"))
        self.assertEqual((inactive["candidate_count"], inactive["negative_count"]), (4, 4))
        paired = [
            row for row in tables["paired_comparisons"]
            if row["model_id"] == "demo_forecast_stub" and row["metric"] == "average_precision"
        ][0]
        self.assertEqual((paired["reference_value"], paired["value"], paired["difference"]), (.5, 1, .5))

    def test_multiyear_synthetic_mapping_has_own_probability_diagnostics(self):
        config = {
            **DEMO_CONFIG, "multi_year": True,
            "models": {"required": ["persistence_binary", "demo_forecast_stub_mapped"]},
        }
        tables = self.evaluation.evaluate_predictions(
            prediction_rows(config, [DEMO_ORIGIN], DEMO_PAIRS), config, [DEMO_ORIGIN], DEMO_PAIRS
        )
        self.assertEqual({row["model_id"] for row in tables["reliability"]}, {"demo_forecast_stub_mapped"})

    def test_research_rejects_unregistered_model_inventory_and_dates(self):
        bad_config = {**RESEARCH_CONFIG, "models": {"required": ["persistence_binary"]}}
        with self.assertRaisesRegex(DataContractError, "inventory"):
            self.evaluation.evaluate_predictions([], bad_config, RESEARCH_ORIGINS, RESEARCH_PAIRS)
        bad_origins = (*RESEARCH_ORIGINS[:-1], "2024-11-26")
        with self.assertRaisesRegex(DataContractError, "origins"):
            self.evaluation.evaluate_predictions([], RESEARCH_CONFIG, bad_origins, RESEARCH_PAIRS)
        with self.assertRaisesRegex(DataContractError, "inventory"):
            self.evaluation.evaluate_predictions([], RESEARCH_CONFIG, RESEARCH_ORIGINS, RESEARCH_PAIRS)

    def test_research_score_must_match_probability_under_absolute_tolerance(self):
        rows = list(prediction_rows(RESEARCH_CONFIG, RESEARCH_ORIGINS[:1], RESEARCH_PAIRS))
        forecast = next(row for row in rows if row["model_id"] == "arima")
        forecast["score"] = forecast["probability"] - 1e-10
        with self.assertRaisesRegex(DataContractError, "score.*probability"):
            self.evaluation.evaluate_predictions(rows, RESEARCH_CONFIG, RESEARCH_ORIGINS, RESEARCH_PAIRS)

    def test_research_panel_requires_distinct_frozen_mapper_identities(self):
        rows = list(prediction_rows(RESEARCH_CONFIG, RESEARCH_ORIGINS[:1], RESEARCH_PAIRS))
        for row in rows:
            if row["model_id"] == "prophet":
                row["mapper_id"] = "mapper-arima"
        with self.assertRaisesRegex(DataContractError, "distinct.*mapper"):
            self.evaluation.evaluate_predictions(rows, RESEARCH_CONFIG, RESEARCH_ORIGINS, RESEARCH_PAIRS)

    def test_full_research_geometry_covers_every_registered_metric_and_pair(self):
        tables = self.evaluation.evaluate_predictions(
            prediction_rows(RESEARCH_CONFIG, RESEARCH_ORIGINS, RESEARCH_PAIRS),
            RESEARCH_CONFIG, RESEARCH_ORIGINS, RESEARCH_PAIRS,
        )
        self.assertEqual(sum(row["candidate_rows"] for row in tables["model_diagnostics"]), 52_200)
        self.assertTrue(all(row["candidate_rows"] == 5_220 for row in tables["model_diagnostics"]))
        metrics = tables["metrics_by_origin"]
        self.assertEqual(len([row for row in metrics if row["metric"] == "filtered_mrr"]), 120)
        self.assertEqual({row["requested_k"] for row in metrics if row["metric"] == "precision_at_k"}, {10, 25, 50})
        self.assertEqual({row["candidate_count"] for row in metrics}, {435})
        self.assertEqual(len([
            row for row in tables["paired_comparisons"]
            if row["model_id"] == "timestral_graph" and row["reference_model_id"] == "timestral_count_only"
            and row["metric"] == "average_precision"
        ]), 12)

    def test_report_uses_persisted_results_and_labels_synthetic_demo(self):
        from cooperalink.artifacts import write_parquet

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_parquet(output / "daily_counts.parquet", [
                {"day": (date.fromisoformat(DEMO_ORIGIN) + timedelta(days=offset)).isoformat(),
                 "count": 7 if offset in (0, 31) else 1 if offset in (1, 30) else 0}
                for offset in range(32)
            ])
            tables = self.evaluate_demo()
            self.evaluation.write_evaluation(output, tables, DEMO_CONFIG)
            with (output / "origin_activity.csv").open(newline="") as stream:
                self.assertEqual(next(csv.DictReader(stream))["eligible_cohort_records"], "2")
            for artifact in ("report.md", "report.html"):
                report = (output / artifact).read_text()
                self.assertIn("SYNTHETIC SOFTWARE DEMONSTRATION - NOT RESEARCH RESULTS", report)
                self.assertIn("persistence_binary", report)
                self.assertIn("0.5000", report)
            (output / "report.md").unlink()
            self.evaluation.render_report(output, DEMO_CONFIG)
            self.assertIn("0.5000", (output / "report.md").read_text())
            export_metadata = json.loads((output / "metric_exports_manifest.json").read_text())
            self.assertTrue(export_metadata["synthetic"])
            self.assertIn("metrics_by_origin.csv", export_metadata["files"])
            self.assertTrue((output / "figures" / "performance_by_origin.svg").is_file())
            (output / "metrics_summary.csv").write_text("corrupted\n")
            with self.assertRaisesRegex(DataContractError, "metric export.*hash"):
                self.evaluation.render_report(output, DEMO_CONFIG)

    def test_report_accepts_completion_before_publishing_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            completion = {"blockers": [{"stage": "source", "code": "missing", "detail": "Export is pending"}]}
            self.evaluation.render_report(output, RESEARCH_CONFIG, completion=completion)
            self.assertIn("Export is pending", (output / "report.md").read_text())
            self.assertFalse((output / "completion.json").exists())

    def test_research_report_commands_use_saved_input_and_exact_output(self):
        from html import unescape
        from shlex import split
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            root = parent / "kit"
            input_path = root / "data" / "analyst's export"
            for output, argument in (
                (root / "custom jobs" / "run", "custom jobs/run"),
                (root / "root-level output", str(root / "root-level output")),
                (parent / "external jobs" / "run", str(parent / "external jobs" / "run")),
            ):
                with self.subTest(output=output):
                    output.mkdir(parents=True)
                    request = output / "run_request.json"
                    contents = json.dumps({"input": str(input_path), "token": "must-not-appear"})
                    request.write_text(contents)
                    with patch("cooperalink.reporting.ROOT", root):
                        self.evaluation.render_report(output, RESEARCH_CONFIG)
                    markdown = (output / "report.md").read_text()
                    html = (output / "report.html").read_text()
                    commands = markdown.split("```sh\n", 1)[1].split("\n```", 1)[0]
                    self.assertEqual([split(line) for line in commands.splitlines()], [
                        ["cooperalink", "run", "--config", "config/research.json",
                         "--input", "data/analyst's export", "--output", argument],
                        ["cooperalink", "resume", "--run-id", argument],
                        ["cooperalink", "report", "--run-id", argument],
                    ])
                    self.assertIn(commands, unescape(html))
                    self.assertNotIn("must-not-appear", markdown + html)
                    self.assertEqual(request.read_text(), contents)
