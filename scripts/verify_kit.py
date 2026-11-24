#!/usr/bin/env python3
"""Verify the intact specification package; this does not test implementation.

Run once on receipt. After deliberately editing the project, use
--structure-only if an authoring-structure check is still useful. Application
test and research-completion evidence must come from their own test/run gates.
"""

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODELS = {
    "persistence_binary", "recent_count30", "jaccard", "common_neighbors",
    "preferential_attachment", "static_logistic_topology", "arima", "prophet",
    "timestral_count_only", "timestral_graph",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure-only", action="store_true")
    args = parser.parse_args()
    required = [
        "README.md", "AGENTS.md", "CODEX_PROMPT.md", "KIT_VALIDATION.md",
        "references/original_proposal.pdf", "references/ta_feedback.md",
        "config/research.json", "config/demo.json", "config/work_plan.json",
    ]
    for name in required:
        require((ROOT / name).is_file(), f"Missing required package file: {name}")
    for i in range(1, 14):
        require(len(list((ROOT / "docs").glob(f"{i:02d}_*.md"))) == 1,
                f"Expected one numbered document {i:02d}")
    parsed_json = {}
    for path in ROOT.rglob("*.json"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        parsed_json[path.relative_to(ROOT).as_posix()] = json.loads(path.read_text())
    cfg = parsed_json["config/research.json"]
    require(cfg["synthetic"] is False, "Research configuration cannot be synthetic")
    require(cfg["data"]["event_code"] == "061", "Wrong CAMEO relation")
    require(cfg["data"]["time_field"] == "DATEADDED", "Wrong observational clock")
    require(cfg["data"]["timezone"] == "UTC", "Wrong observation timezone")
    require(cfg["cohort"]["top_n"] == 30, "Wrong registered cohort size")
    require(cfg["cohort"]["expected_pairs"] == math.comb(30, 2), "Wrong pair count")
    require(cfg["cohort"]["negative_sampling"] is False, "Negative sampling forbidden")
    temporal = cfg["temporal"]
    require(temporal["context_days"] == 90 and temporal["horizon_days"] == 30,
            "Wrong context or prediction horizon")
    require(temporal["raw_context_days"] == temporal["context_days"] + temporal["graph_window_days"] - 1,
            "Graph context needs 119 raw days")
    require(temporal["roles"] == {"cohort": [2020], "train": [2021], "validation": [2022],
                                  "calibration": [2023], "test": [2024]}, "Wrong year roles")
    models = cfg["models"]["required"]
    require(len(models) == len(set(models)) and set(models) == REQUIRED_MODELS,
            "Required model inventory differs from specification")
    require(cfg["models"]["mapper"]["fit_years"] == [2023], "Wrong mapping fit interval")
    require(cfg["models"]["timestral"]["checkpoint"] == "mistralai/Timestral-209M",
            "Wrong primary checkpoint")
    require(cfg["execution"]["new_cloud_spend_allowed"] is False,
            "New billable services must be disabled by default")
    demo = parsed_json["config/demo.json"]
    require(demo["synthetic"] and not demo["research_complete"] and not demo["network_allowed"],
            "Demo must be explicitly synthetic and offline")

    plan = parsed_json["config/work_plan.json"]
    task_ids = {task["id"] for task in plan["tasks"]}
    done = set()
    while len(done) < len(task_ids):
        ready = {task["id"] for task in plan["tasks"]
                 if set(task["depends_on"]) <= done} - done
        require(bool(ready), "Work plan has unknown dependencies or a cycle")
        done |= ready

    python_count = 0
    test_count = 0
    for directory in [ROOT / "src", ROOT / "tests", ROOT / "scripts"]:
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            python_count += 1
            if directory.name == "tests":
                test_count += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                                  and node.name.startswith("test_") for node in ast.walk(tree))
    require(test_count >= 43, "Expected at least the 43 reviewed starter contracts")

    checked_hashes = 0
    if not args.structure_only:
        manifest = ROOT / "MANIFEST.sha256"
        require(manifest.is_file(), "Missing MANIFEST.sha256")
        for line in manifest.read_text().splitlines():
            expected, relative = line.split("  ", 1)
            path = (ROOT / relative).resolve()
            require(path.is_relative_to(ROOT), "Manifest path escapes package")
            require(path.is_file(), f"Manifest file is missing: {relative}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            require(actual == expected, f"Content changed or damaged: {relative}")
            checked_hashes += 1
    print(json.dumps({"package_integrity": "verified" if not args.structure_only else "not_requested",
                      "configuration_consistency": "passed", "python_files_parsed": python_count,
                      "starter_test_methods": test_count, "manifest_files_checked": checked_hashes,
                      "application_tests_run": False,
                      "note": "The application is intentionally unimplemented; run the RED suite separately."}, indent=2))


if __name__ == "__main__":
    main()
