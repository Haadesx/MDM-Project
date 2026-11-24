# 10. Execution, data access, and recovery runbook

## Environment bootstrap

The lock and model smoke tests were verified with Python 3.12 on Apple silicon macOS. Other platforms and CUDA are untested.

```bash
uv sync --locked --python 3.12 --extra test
uv run --no-sync python scripts/smoke_models.py
uv run --no-sync python scripts/verify_application.py
```

Core modules import without model initialization. Run genuine smoke checks with the official cached checkpoint supplied at the pinned snapshot.

## Required CLI surface

| Command | Required behavior |
| --- | --- |
| `cooperalink doctor --config PATH` | Check configuration, Python/backends, optional device, model revisions/cache, source availability; no paid work |
| `cooperalink validate-input --input DIR --config PATH` | Validate schemas, coverage, registry, timestamps, duplicates, and declared interval |
| `cooperalink prepare --input DIR --config PATH --output DIR` | Save normalized ledger, roster, full pair panel, counts, features, and folds |
| `cooperalink demo --config config/demo.json` | Offline synthetic vertical slice and clearly labeled report |
| `cooperalink fit --config PATH --run-id ID` | Train/select/refit topology classifier and fit four 2023 forecast mappers |
| `cooperalink evaluate --config PATH --run-id ID` | Score fixed final origins, validate model/key inventory, join labels, compute metrics |
| `cooperalink report --run-id ID` | Render results already stored for that exact run; no fitting or metric changes |
| `cooperalink run --config PATH --input DIR --output DIR` | Execute all needed stages with checkpoints and no duplicate work |
| `cooperalink resume --run-id ID` | Validate run identity and continue incomplete stages only |

`cooperalink export-source --dry-run --project YOUR_EXISTING_PROJECT` submits the bounded query for an estimate using an existing authenticated `bq` client. The project CLI supports dry runs only. A separate authorized export must have a positive maximum billed-bytes cap. No actual estimate is available from the verified environment because `bq` is absent.

The commands below use the project's virtual environment. Run them via `uv run --no-sync cooperalink` if the environment is inactive.

Desired finished-project commands:

```bash
cooperalink doctor --config config/research.json
cooperalink demo --config config/demo.json
cooperalink validate-input --input data/input --config config/research.json
cooperalink run --config config/research.json --input data/input --output outputs/research_top30_final
```

## Data prerequisites

The preferred input is an existing typed GDELT 2.0 `061` extract covering recorded days 2020-2024, plus source/extraction-coverage evidence. A complete query receipt or verified inventory is required to distinguish zero rows from missing extraction. Read `docs/03_DATA_CONTRACT.md` before importing.

For a local export, put `source.json` alongside the data files. Set `snapshot` to a stable nonsecret ID shared by the coverage records. Replace placeholder values with verified extraction evidence.

```json
{
  "dataset": "GDELT 2.0 Events",
  "synthetic": false,
  "start": "2020-01-01",
  "end_exclusive": "2025-01-01",
  "snapshot": "EXTRACTION_SNAPSHOT_ID",
  "extraction_scope": "Source table, exact query or inventory identity, and half-open UTC DATEADDED bounds",
  "extracted_at_utc": "REPLACE_WITH_ACTUAL_UTC_TIMESTAMP",
  "coverage": "coverage.csv",
  "files": [{"path": "events.csv", "delimiter": ","}]
}
```

For Parquet files omit `delimiter` and keep `EventCode` typed as a string. Use a literal tab delimiter encoded as `"\t"` for TSV files. A file entry may also supply a SHA-256 under `sha256`. Coverage expects the columns in [the data contract](03_DATA_CONTRACT.md#coverage-manifest). Include a successful extraction receipt or complete inventory record for each day, including verified zero-row days. All complete rows must use the manifest snapshot ID.

The bounded BigQuery dry-run command is available when an existing authenticated `bq` client is available. BigQuery may require the user's existing project/credentials and may incur charges; no query cost was measured for this kit. Prepare the query, verify the schema, dry-run it, and enforce an approved maximum byte limit. Do not enable a billing account or provision storage automatically.

Raw official Event ZIPs are a fallback for bounded samples or cached data. The default new-raw-file cap is 96 archives, so a small acquisition smoke can run without accidentally fetching five years. Raising that cap or selecting a five-year crawl must be an explicit data-acquisition decision supported by a volume estimate. Continue the software implementation while the full export is unavailable.

## Model and hardware prerequisites

The required checkpoint is `mistralai/Timestral-209M`, loaded through its official package. Existing Hugging Face caches should be reused. Record exact source/weight revisions, weight/config checksums, precision, and actual device. The model source commit is `a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff` and the cached checkpoint revision is `9874d252ab0aae16f7f7c999f98f98d6ad7d8365`. If that cache is unavailable, populate it explicitly from the official repo:

```bash
uv run --no-sync hf download mistralai/Timestral-209M config.json model.safetensors --revision 9874d252ab0aae16f7f7c999f98f98d6ad7d8365
```

CPU execution is supported and is the portable default fallback. If an available CUDA device is compatible with the installed torch build, use it for one batched Timestral process. Do not assume a remote GPU is online or launch other user jobs. Start at batch 32 and reduce on measured out-of-memory failure. MPS experimentation and smaller model sizes are optional development variants, not required research dependencies.

ARIMA/Prophet run with two concurrent workers and a total numerical-thread budget of four initially. On larger hardware, tuning worker count after a measured pilot is allowed, while preserving results and configuration semantics. Report actual fit counts, cache hits, constant-series shortcuts, runtimes, and peak memory where available. Do not extrapolate vendor benchmark throughput to this workload.

## Runtime control and failure recovery

Before the full run, profile representative nonconstant contexts for both classical backends and one Timestral batch. Log an estimated remaining workload and its measurement basis. Local computation may continue until completion; no arbitrary hard time limit is imposed by this kit. If the owner configures a time budget, checkpoint at its boundary and leave a precise resume command.

Persist states `pending`, `running`, `complete`, `failed`, or `blocked` per stage/task. A process restart must validate output hashes and resume from completed tasks, not rerun downloads/fits blindly. Write outputs atomically. Retry transient source failures with a bounded policy; never retry a scientific schema or chronology error indefinitely.

On model fit failure, preserve the failed pair/origin and diagnostics. Do not quietly substitute persistence or drop the row. On missing coverage, preserve the whole affected origin's status across all models. On invalid calibration (including a one-class set), stop scientific fitting and report the exact violated precondition while retaining completed software and input audits.

## Data and model isolation

Use a local `.env` or standard credential store only if needed, and never commit or print secrets. Record a nonsecret source identity in manifests. No credentials, raw source URLs containing tokens, user-private absolute home paths, or model binaries should appear in a submission bundle.

Model predictions are saved before future labels are joined. All fitted probability heads retain their 2023 fit-row hashes and label-maturity range. The report includes enough provenance to reconstruct the result without exposing credentials.

## Final handoff when a prerequisite is blocked

Give the user the working repository, passing fast and integration tests actually run, synthetic demonstration, precise absent input/dependency, and exact command that resumes the next real stage. Mark `research_complete=false`. Do not claim a missing project component is implemented merely because this specification describes it. Do not end early if independent engineering work remains possible.
