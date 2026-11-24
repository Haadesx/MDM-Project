import argparse
import fcntl
import json
from pathlib import Path
import shutil
from time import perf_counter

from .artifacts import digest, read_json
from .domain import CoverageError, DataContractError
from .pipeline import DEMO_FORECAST, RESEARCH, ROOT, STATIC, Run, environment

RESEARCH_DIGEST = "d1dba68f782e8f0cf883b1a6c951d8d6d4fb63940c9d81cfff8fb3a2751d2890"
DEMO = ROOT / "config/demo.json"


def config_from(path, multiyear=False):
    config = read_json(path)
    if config.get("synthetic") is False and digest(config) == RESEARCH_DIGEST:
        return config
    if config != read_json(DEMO):
        raise DataContractError("Use the registered research.json or demo.json profile")
    if multiyear:
        main = read_json(RESEARCH)
        return config | {"profile": "demo_synthetic_multiyear", "multi_year": True,
                         "temporal": main["temporal"],
                         "models": config["models"] | {"required": [
                             *config["models"]["required"][:-1], STATIC,
                             DEMO_FORECAST + "_mapped"]}}
    return config


def parser():
    cli = argparse.ArgumentParser(prog="cooperalink")
    commands = cli.add_subparsers(dest="command", required=True)
    for name in ("doctor", "validate-input", "prepare", "demo", "fit", "evaluate", "report", "run", "resume"):
        sub = commands.add_parser(name)
        if name not in {"report", "resume"}:
            sub.add_argument("--config", type=Path, default=DEMO if name == "demo" else RESEARCH)
        if name in {"doctor", "validate-input", "prepare", "run"}:
            sub.add_argument("--input", type=Path, default=ROOT / "data/input")
        if name in {"prepare", "demo", "run"}:
            sub.add_argument("--output", type=Path)
        if name in {"fit", "evaluate", "report", "resume"}:
            sub.add_argument("--run-id", required=True)
        if name == "demo":
            sub.add_argument("--multiyear", action="store_true")
    export = commands.add_parser("export-source")
    export.add_argument("--dry-run", action="store_true", required=True)
    export.add_argument("--start", default="2020-01-01")
    export.add_argument("--end-exclusive", default="2025-01-01")
    export.add_argument("--project")
    export.add_argument("--maximum-bytes-billed", type=int)
    return cli


def doctor(config, input_path):
    from .models import TIMESTRAL_SOURCE_REVISION, TIMESTRAL_WEIGHTS_REVISION, _source_revision

    env = environment()
    if config["synthetic"]:
        return {"status": "ready", "profile": config["profile"], "environment": env,
                "offline": True, "blockers": []}
    missing = [k for k, v in env["packages"].items() if v is None]
    checks = {"source_manifest": (input_path / "source.json").is_file(),
              "registry": (ROOT / config["cohort"]["registry"]).is_file(),
              "bigquery_cli": bool(shutil.which("bq")),
              "timestral_source_revision": _source_revision(),
              "timestral_expected_source_revision": TIMESTRAL_SOURCE_REVISION,
              "timestral_expected_weights_revision": TIMESTRAL_WEIGHTS_REVISION,
              "weights_cached_local": False}
    if env["packages"]["huggingface-hub"]:
        from huggingface_hub import try_to_load_from_cache

        checks["weights_cached_local"] = all(isinstance(try_to_load_from_cache(
            config["models"]["timestral"]["checkpoint"], filename, revision=TIMESTRAL_WEIGHTS_REVISION), str)
            for filename in ("config.json", "model.safetensors"))
    blockers = [key for key in ("source_manifest", "registry", "weights_cached_local") if not checks[key]]
    if checks["timestral_source_revision"] != TIMESTRAL_SOURCE_REVISION:
        blockers.append("timestral_source_revision")
    return {"status": "blocked" if blockers or missing else "ready", "profile": config["profile"],
            "environment": env, "checks": checks, "blockers": blockers + missing}


def saved_run(args):
    target = Path(args.run_id)
    output = target.resolve() if target.is_absolute() or len(target.parts) > 1 else ROOT / "outputs" / target
    config = read_json(output / "resolved_config.json")
    if hasattr(args, "config") and config != config_from(args.config, config.get("multi_year", False)):
        raise DataContractError("Supplied configuration disagrees with the saved run")
    if config != config_from(DEMO if config["synthetic"] else RESEARCH, config.get("multi_year", False)):
        raise DataContractError("Saved run configuration differs from the registered profile")
    source = read_json(output / "run_request.json")["input"]
    return Run(output, config, Path(source) if source else None)


def execute(run, command):
    from .evaluation import render_report

    if command == "report":
        manifest_path = run.path("run_manifest.json")
        render_report(run.output, run.config, read_json(manifest_path) if manifest_path.exists() else None)
        return 0, {"status": "complete", "task": "report", "output": str(run.output)}
    run.initialize()
    deadline = run.config.get("execution", {}).get("initial_run_wall_time_hours")
    deadline = perf_counter() + deadline * 3600 if deadline is not None else None
    stage = "prepare"
    try:
        prepared = run.prepare()
        evaluated = run.path("evaluated.json").exists()
        if evaluated and command in {"resume", "run", "evaluate", "demo"}:
            stage = "evaluate"
            completion = run.existing_evaluation()
            ok = run.synthetic or completion["research_complete"]
            return (0 if ok else 1), {"status": "complete" if ok else "blocked", "run_id": run.id,
                                      "output": str(run.output), **completion}
        if command == "prepare":
            if evaluated:
                return 0, {"status": "complete", "task": stage, "data_sha256": prepared["data_hash"]}
            run.manifest([])
            run.completion(stage="fit", code="pending", detail="Run the fitting and evaluation stages")
            return 0, {"status": "complete", "task": stage, "data_sha256": prepared["data_hash"]}
        heads = errors = None
        if command != "evaluate":
            stage = "fit"
            heads, errors = run.fit(deadline)
        if command == "fit":
            if evaluated:
                return (1 if errors else 0), {"status": "blocked" if errors else "complete", "task": stage,
                                             "errors": errors, "fitted": list(heads)}
            run.manifest([])
            run.completion(stage="fit" if errors else "evaluate", code="incomplete_fits" if errors else "pending",
                           detail=str(errors) if errors else "Run the evaluation stage",
                           missing=sorted(errors))
            return (1 if errors else 0), {"status": "blocked" if errors else "complete", "task": stage,
                                         "errors": errors, "fitted": list(heads)}
        stage = "evaluate"
        success = run.evaluate(heads, errors, deadline)
        completion = run.read("completion.json")
        if not success:
            render_report(run.output, run.config, run.read("run_manifest.json"))
        ok = success and (run.synthetic or completion["research_complete"])
        return (0 if ok else 1), {"status": "complete" if ok else "blocked", "run_id": run.id,
                                  "output": str(run.output), **completion}
    except (CoverageError, DataContractError, FileNotFoundError, ValueError, RuntimeError, ImportError, TimeoutError) as exc:
        status = "blocked" if isinstance(exc, (CoverageError, FileNotFoundError, TimeoutError)) or stage == "prepare" else "failed"
        run.status(status, stage, str(exc))
        code = "coverage" if isinstance(exc, CoverageError) else "wall_time" if isinstance(exc, TimeoutError) else "stage_error"
        completion = run.completion(stage, code, str(exc))
        render_report(run.output, run.config, None)
        return 1, {"status": status, "task": stage, "output": str(run.output), **completion}


def dispatch(args):
    command = args.command
    if command == "export-source":
        from .acquisition import dry_run_source

        return 0, {"status": "complete", **dry_run_source(args.start, args.end_exclusive,
                                                         args.project, args.maximum_bytes_billed)}
    if hasattr(args, "run_id"):
        run = saved_run(args)
    else:
        config = config_from(args.config, getattr(args, "multiyear", False))
        if command == "demo" and not config["synthetic"]:
            raise DataContractError("The offline demo requires demo.json")
        if command in {"doctor", "validate-input"}:
            if command == "doctor":
                checks = doctor(config, args.input)
                return (0 if checks["status"] == "ready" else 1), checks
            output = ROOT / "outputs" / "validation"
            run = Run(output, config, args.input.resolve() if not config["synthetic"] else None)
            return 0, {"status": "complete", "cleaning_audit": run.validate_source()}
        default = "demo_multiyear" if config.get("multi_year") else "demo" if config["synthetic"] else "research_top30"
        output = (args.output or ROOT / "outputs" / default).resolve()
        run = Run(output, config, args.input.resolve() if not config["synthetic"] else None)
    run.output.mkdir(exist_ok=True, parents=True)
    with run.path(".run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DataContractError(f"Run {run.id} is already active") from exc
        try:
            return execute(run, command)
        finally:
            run.close()


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        rc, result = dispatch(args)
    except (OSError, ValueError, KeyError, RuntimeError, ImportError) as exc:
        rc, result = 1, {"status": "blocked", "task": args.command, "detail": str(exc)}
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
