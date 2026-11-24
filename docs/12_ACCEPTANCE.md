# 12. Acceptance and completion gates

## The three completion levels

| Level | What it proves | Insufficient evidence |
| --- | --- | --- |
| Engineering complete | Required modules/CLI work, relevant tests pass, errors and recovery work | Passing only the original red-contract subset |
| Demo complete | Offline synthetic end-to-end execution and labeled report | A screenshot or hard-coded metric table |
| Research complete | Actual fixed GDELT experiment with genuine model backends and all required outputs | Mock inference, missing candidates/models/windows, or invented data |

The delivered kit is at none of these application-completion levels. It is a validated implementation handoff with intentionally red functions. Its authoring-time integrity checks are separately recorded in `KIT_VALIDATION.md`.

## Gate A: software and contracts

- All starter contracts and new source/model/calibration/pipeline tests pass for the implementation; no scientific test was deleted or disguised as skipped to evade a failure.
- Pure modules import without heavy backend side effects. Offline demo and tests make no network calls.
- Real source schema aliases are handled explicitly; malformed eligible rows and conflicting identities fail clearly.
- Candidate generation, date boundaries, graph support, future-injection invariance, and tie-aware metrics match the specification.
- The completed CLI produces structured status, correct exit codes, schemas, and resumable artifacts.
- Dependency lock and exact setup/reproduction commands work in a clean environment of the documented platform, or any unverified platform is clearly labeled untested.

## Gate B: data and country cohort

- Real GDELT 2.0 input uses exact `061`, actor affiliations, strict UTC `DATEADDED`, and unique event IDs.
- Official registry source/version and any normalization/classification decisions are recorded.
- Complete 2020 extraction coverage supports selection; the research caller requires exactly 30 selected countries. A reusable helper returning fewer does not satisfy this gate.
- The saved cohort is independent of later-year outcomes, and its all-pairs table contains exactly 435 unique canonical pairs.
- Source history and label coverage are established for every planned final origin. Missing data is never zero-filled as an observed non-event.
- All cleaning/rejection/duplicate counts and source intervals are reported. Data and cohort hashes are saved.

## Gate C: actual models

The exact required model inventory is:

```text
persistence_binary
recent_count30
jaccard
common_neighbors
preferential_attachment
static_logistic_topology
arima
prophet
timestral_count_only
timestral_graph
```

The final acceptance function must check this inventory explicitly. `validate_prediction_keys` only checks models passed to it; passing an empty dictionary or leaving out Prophet cannot satisfy Gate C.

- Genuine Timestral-209M and real ARIMA/Prophet smoke tests have run, with actual versions/revisions recorded.
- Both Timestral variants use the same required checkpoint and differ only in the specified covariate use.
- ARIMA/Prophet constant-history shortcuts follow the predetermined rule and have their usage counted.
- Static logistic selection/refitting uses only its designated years. Four distinct forecast mapping artifacts fit only 2023 complete examples.
- Global mappings and settings are frozen before final testing; local classical context fits are permitted only on the prescribed as-of history.
- No fallback model, fake backend, altered candidate population, or missing prediction is hidden under a required model ID.
- Forecast-based ranking scores equal their mapped link probabilities, with nonempty mapper identities; static logistic scores equal its probabilities. Enforce the registered absolute tolerance of `1e-12`. All 12 calibration origins and every candidate must succeed before fitting a required forecast mapper.

## Gate D: complete final evaluation

- Exactly 12 planned 2024 windows, each with 435 scored pair rows per required model: 5,220 final pair-origin scores per model and 52,200 across the ten required IDs.
- All original metrics plus AP appear with per-origin results, exact tie semantics, valid-window counts, and null reasons. Undefined metrics caused by the observed class distribution are legitimate; missing predictions are not.
- Precision rows contain the configured integer K values 10, 25 and 50 and reconcile `effective_k=min(requested_k,candidate_count)`. MRR records contain an integer positive-query count. Candidate/positive/negative counts and MRR support reconcile with the scored panel.
- The primary comparison uses full candidates. Active/inactive-last-30 slices retain support counts; filtered MRR remains the full-cohort primary metric unless a separate subset definition is registered.
- Paired per-window comparisons to persistence and the count-only ablation are reported without selecting only favorable origins.
- Any source gap or required model failure makes the fixed full research run incomplete. A reduced-coverage diagnostic may be delivered separately, with no false full-study completion claim.
- No model-performance threshold is required. Beating persistence is not a software test or graduation gate.

## Gate E: report and reproducibility

- The report answers all four TA points with implemented definitions and evidence.
- Numbers in report/figures match immutable CSV/Parquet/JSON outputs; all ten baseline/main rows are visible.
- Cohort restriction, observation-time target, news/record noise, 90-versus-119-day information support, 2026 model vintage, and unknown pretraining overlap are disclosed.
- Full source/model/config/dependency identities and actual hardware/runtime are recorded; no moving revision is presented as a reproducible pin.
- Resume and cache-invalidation tests pass; exact rerun/resume commands are included.
- `completion.json` satisfies its schema and lists specific blockers for every incomplete gate.

## Required final artifact inventory

At minimum: `resolved_config.json`, `environment.json`, `run_manifest.json`, `completion.json`, `country_registry.csv`, `cohort.csv`, `candidate_pairs.parquet`, `coverage.parquet`, `origins.csv`, normalized-data fingerprints, fitted-model/map metadata, `predictions.parquet`, `metrics_by_origin.csv`, `metrics_summary.csv`, `paired_comparisons.csv`, conditional-slice results, figures, `report.md`, `report.html`, and actual test logs.

Large source data and model weights can remain in local caches with hashes and acquisition instructions; they are not required inside a submission ZIP. If course rules require additional file formats, add them without changing the study.
