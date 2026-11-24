# 04. Architecture and scientific decisions

These decisions resolve ambiguity before implementation. They are recommendations for this project, not claims of prior TA approval. Changes require a short entry in `DECISIONS_LOG.md`, updated configuration/tests, and a fresh experiment identity. No change may be selected because it improves an already-inspected final test score.

| ID | Decision | Reason | Consequence / alternative |
| --- | --- | --- | --- |
| ADR-01 | Predict observed future records, not an enduring diplomatic relationship | A precise target can be constructed from the provided event source | A label zero means no observed record, not no real cooperation |
| ADR-02 | Use undirected canonical country pairs | Bilateral economic-cooperation question and symmetric graph features | Raw actor roles preserved for audit; directed prediction would be a separately registered study |
| ADR-03 | Use exact `061` and unique GDELT event IDs | Matches proposal relation and avoids mention-count inflation | No `06*` prefix, aid code, or weighted article counts |
| ADR-04 | Bin by UTC `DATEADDED` | Observations were unavailable before being recorded | Label concerns newly recorded events; SQLDATE remains an audit column |
| ADR-05 | Select fixed top-30 countries from 2020 incidence | Contains ARIMA/Prophet cost and prevents future-informed cohort selection | All 435 combinations are mandatory; country coverage is restricted and disclosed |
| ADR-06 | Use all positives and all negatives | Small panel makes sampling unnecessary and preserves prevalence | No balanced-negative evaluation, class weighting, or easy-negative selection |
| ADR-07 | Daily graph snapshots aggregate the trailing 30 days | Defines the formerly unspecified snapshot and captures recent network structure | 90 model rows require 119 raw days; one-day graphs are an optional preregistered sensitivity study |
| ADR-08 | Hold out calendar roles and use exactly 30-day labels | Separates fit, choice, probability mapping, and final evidence | Twelve windows per year; omit the remaining five/six target days and report them |
| ADR-09 | Keep Timestral backbone fixed, use topology as past covariates | Follows a supported API and the proposed target/feature distinction | No future graph values, fine-tuning, or paid generative API |
| ADR-10 | Use full 30-point forecast vector in a fixed L2 logistic map | Closely implements the proposal's vector-to-link formula | Scaler/map fit on 2023 only; output is not automatically empirically calibrated |
| ADR-11 | Retain every proposed baseline and add cheap strong checks | Makes any gain attributable and satisfies TA persistence requirement | Timestral count-only, recent-count30, and PA also required |
| ADR-12 | Use exact tie-aware P@K and explicit filtered MRR | Binary persistence has many ties; arbitrary ordering must not decide results | Display can use lexical tie order; metric computation uses its documented tie rule |
| ADR-13 | Local batch Python with Parquet and DuckDB | Sufficient for the cohort, portable, auditable, low operational cost | No web service or distributed infrastructure required |
| ADR-14 | Immutable caches with resumable stages | Classical fits and downloads can be costly to repeat | Cache keys include input/config/model identity; atomic completion receipts |
| ADR-15 | Separate demo, engineering, and scientific completion | Missing external data cannot be disguised by mock success | A working program may be delivered with an explicit real-data blocker |
| ADR-16 | Treat 2026 model on older data as retrospective evaluation | Model vintage and possible training overlap cannot be resolved by feature cutoffs | No historically deployable-as-of-2024 claim |

## Decisions the implementation agent may make without asking

Choose small function names/internal class organization, a tested vectorized graph calculation, logging format, notebook presence, plot colors, local cache compression, and compatible dependency pins. Preserve public starter APIs unless a documented defect requires a coordinated correction. Pick an available device and a smaller batch size when necessary; record the actual runtime.

The agent may repair an incorrectly typed export through a fresh source export with explicit schema. It must not repair uncertainty by guessing that a numeric event code meant `061`. It may classify routine country-registry entries from official evidence and record decisions without asking the user repeatedly.

## Decisions that change the experiment

Changing country count, membership rule, event-time convention, relation family, graph window, label horizon, negative sampling, model size, global fit years, probability features, metric population, or test windows creates a new named configuration. Such changes must be written before inspecting their final evaluation. Preserve and report the originally registered main study; do not silently replace it with a more favorable or cheaper subset.

## Cost versus scope

The base run contains 435 pairs and 12 final windows, or 5,220 candidate outcomes per model. Forecast-based calibration adds another 5,220 candidate contexts per model. Thus a classical backend has at most 10,440 local context tasks before declared constant-series shortcuts, caching, retries, or optional diagnostics. This is a workload count, not a promised runtime. Measure representative nonconstant cases before scheduling the full run.

An all-country expansion multiplies work quadratically. Increase coverage only after the fixed study works; do not trade away the required baselines. Hardware acceleration chiefly helps batched foundation-model inference; it does not remove the per-series classical fitting work.
