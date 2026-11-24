# 07. Test-driven development guide

## What is already executable

The kit supplies 43 behavioral `unittest` cases, typed domain records, function signatures, and independent synthetic expectations. They need only Python's standard library. Each application algorithm deliberately raises `NotImplementedError`; this is the starting red state, not a broken attempt to deliver finished software. Pytest can run the same tests after installing its optional dependency.

The tests cover ingestion, time windows, cohort selection, graph features, metrics, and selected leakage invariants. They do **not** yet implement or fully test model adapters, data acquisition, probability fitting, the CLI, cache recovery, or reporting. Add those tests during their work packages. A green starter suite alone does not satisfy the final acceptance gate.

## Workflow for each behavior

1. Read the governing requirement and the smallest relevant fixture. State what observable outcome must be true.
2. Run the relevant test and confirm the intended red reason. A missing package or syntax error is not evidence that the scientific test is valid.
3. Implement the smallest correct behavior in its owning module. Avoid I/O inside numerical transforms.
4. Rerun the focused tests. Refactor only after they pass; keep outputs and edge behavior unchanged.
5. Add a regression test for any real defect discovered. If a golden expectation is wrong, independently recalculate it and explain the change in `DECISIONS_LOG.md` before editing it.
6. Run the neighboring integration test when the behavior crosses an interface. Run the full fast suite at integration milestones, not after every unrelated text edit.

Do not require a particular research score or hard-code outputs to the fixture. Tests must detect wrong semantics on new inputs, not reward a copied lookup table.

## Starter tests and what they protect

| Test file | Important assertions | Requirement IDs |
| --- | --- | --- |
| `test_ingestion.py` | Exact `061`, actor affiliation fields, UTC dates, canonical pairs, no integer-code repair, distinct IDs, duplicate/conflict handling | FR-01,02 |
| `test_universe.py` | 2020-only roster, future-country immunity, full six-pair toy universe, identical model key sets | FR-03,08 |
| `test_temporal.py` | Exactly 90 days, late reports counted when observed, horizon endpoints, persistence endpoints, missing coverage, leap year, fit-label maturity | FR-04,06,07 |
| `test_graph.py` | Fixed induced graph, 30-day boundaries, known graph metrics, future-event immunity, 119-day raw support | FR-05 |
| `test_metrics.py` | Half-credit AUC ties, threshold AP, expected cutoff ties, filtered MRR, null unsupported cases | FR-12 |

The isolated lower-bound tests matter: an event exactly at `T-29` must be tested without a newer event masking an accidental off-by-one error. The golden ranking fixture has AUC 0.7, AP 1/3, P@2 0.25, and filtered MRR 0.7; its derivation is in `fixtures/README.md`.

Run focused starter tests with, for example:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_temporal.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_metrics.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Additional tests required before engineering completion

### A. Source and coverage contracts

- Local CSV/TSV/Parquet import preserves `061` as a string. Support the explicit `GLOBALEVENTID`/`GlobalEventID` alias, rejecting contradictory simultaneous values.
- Complete zero-row day versus failed/missing extraction day produces different coverage states.
- An eligible malformed timestamp fails input validation with an identifiable reason; unrelated non-061 rows are excluded according to the documented cleaning order.
- Duplicate data across overlapping file exports remains idempotent. Conflicting immutable identity cannot be silently overwritten.
- A bounded source query uses exact columns and both time bounds. The adapter honors dry-run mode and any configured maximum bytes. No cloud call occurs in ordinary tests.
- Source reads cannot mark 2020 cohort selection complete if its interval is incomplete. The research caller requires exactly 30 selected countries even though the reusable helper can return fewer.

### B. Feature assembly and leakage

- The feature builder emits aligned count dates, covariate dates, pair order, and origin metadata. Every sequence has exactly 90 positions and the support starts at `T-118`.
- Inject records at `T+1` and after `T+30`; historical counts, graph rows, persistence, and saved input hashes through T do not change.
- Modify 2024 labels or add later-year countries; the 2020 roster, 2021/2022 selection result, 2023 mapper, and all earlier forecasts do not change.
- The main history/adapter objects have no future-label field. Evaluate only after joining separately saved labels to scored keys.
- Reordering raw rows, pair batching, or workers leaves pair/score association intact. Swapping endpoints does not create a second unordered candidate.
- A vectorized implementation agrees with hand-calculated fixture functions. Large-data optimization must not redefine date or graph windows.

### C. Timestral adapter using a spy backend

Use a fake only to inspect the adapter boundary; it must not be callable under a research model identity in real evaluation.

- Counts enter `context` as `(B,1,90)`, graph channels enter `past_covariates` as `(B,2,90)`, horizon equals 30, and no future graph argument is supplied.
- Main and count-only adapters have distinct model IDs and identical checkpoint settings; only the covariate argument differs.
- Returned tensor handling detaches and moves to CPU before persistence. Validate `(B,1,30)` median output and pair identities.
- Reject NaN/Infinity, wrong dimensions, wrong number of pairs, and incomplete horizons before mapping. Negative finite outputs follow the registered clipping rule.
- Record backend clipping separately from any clipping applied to values it returns. Never infer hidden pre-clipping outputs.
- Dependency or weight absence produces a structured unavailable status. Research mode cannot silently load a fake or smaller checkpoint.
- Cache identity changes with model source/weight revision, context content, graph values, cohort, dates, dtype, and inference settings.

### D. Real adapters, run separately from fast tests

- One genuine Timestral-209M smoke test forecasts a small batch containing zero, constant, and nonconstant histories; assert shapes and finite values, not a guessed exact forecast or performance threshold.
- One real ARIMA and one real Prophet smoke test produce 30-day forecasts from a nonconstant 90-day series.
- The declared constant-history shortcut returns exactly 30 copies of the constant and an explicit `constant_series` status for ARIMA/Prophet only.
- A fit failure or nonconvergence cannot be mistaken for a successful zero forecast. Include an intentional backend exception test.
- The actual library versions and model revisions are written to provenance. Model-loading tests do not redownload weights on every run.

Missing optional heavy dependencies may exclude a real-integration job from the **fast** development suite, but the final research gate must show that the genuine jobs were actually executed. A skipped real-model job cannot count as scientific success.

### E. Supervised fitting and calibration isolation

- Static logistic scalers are fit on 2021 for selection, with `C` chosen using only 2022 macro AP; exact ties select the smaller C. Final refit uses 2021+2022 only.
- Each forecast family has its own 2023 scaler/map using the complete 30-vector, all classes at their observed frequency, and fixed regularization.
- A one-class training or calibration input fails clearly. Constant feature columns are accepted when both classes exist.
- Transforming test features never invokes fit or fit-transform. Instrument fit calls and assert maximum label availability is before each allowed prediction origin.
- Altering the final-year outcomes cannot change selected hyperparameters, scaler means, or fitted coefficients.
- Probability output is finite and in `[0,1]`; score column semantics remain explicit for direct baselines without probabilities.

### F. End-to-end artifact and recovery tests

- Generate a small deterministic multi-year **synthetic** dataset with all role years and both classes; run prepare/fit/evaluate/report without network. Keep the existing one-origin hand fixture for boundary tests.
- The demonstration report has an obvious synthetic banner and `research_complete=false`.
- Model registry acceptance requires all ten canonical IDs; checking the keys of only the models supplied is insufficient. An empty model dictionary must not pass completion.
- Each real final model has exactly 435 pairs per origin and 12 expected final origins. Duplicates, extras, or missing rows invalidate the main table.
- Interrupt a stage after a valid batch, resume, and compare outputs against an uninterrupted run. Verify no duplicate work and no reuse after a changed input/config hash.
- Corrupt or truncate a cache file; validation refuses it instead of reading partial predictions.
- Recompute report table values from exported metrics and check agreement within declared floating-point tolerance. JSON contains no NaN/Infinity.
- The final CLI exits nonzero on a failed requested research run, writes precise blockers, and preserves useful completed outputs.

## Appropriate verification depth

Correctness and leakage defenses matter more than a decorative coverage percentage. Use coverage tools to locate untested branches, especially date/coverage/error handling, without treating 100% coverage as evidence of scientific validity. Static checks should include formatting, syntax, and useful typing checks on public interfaces. Do not add tests that merely assert an implementation chose a particular loop or private helper.

Profile one representative batch of nonconstant histories and log actual throughput/memory before the full run. A reasonable implementation should avoid repeated model loads and redundant graph construction. Do not promise a runtime without measurement or use unstable timing assertions in unit tests.

## Red-phase evidence and final evidence

`KIT_VALIDATION.md` records the starter's actual authoring-time state. The finished project must replace the red evidence with its own test logs and actual run manifests while preserving this kit's provenance. Final handoff must distinguish a collected test, a passing test, a mocked adapter test, and a real-model experiment. They prove different things.
