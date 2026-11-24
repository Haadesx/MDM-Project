# 06. Models and probability mapping

Status: implementation contract. The parameter choices below are project decisions; linked official sources establish the available interfaces. Preserve these choices in the final experiment manifest. Do not change them after inspecting test outcomes.

## 1. Shared input and output contract

At forecast origin `T`, every required model scores exactly the same eligible candidate pairs. All time-series models receive 90 daily count observations, `T-89` through `T`, and predict 30 positions, `T+1` through `T+30`. Inputs must satisfy the project's event-availability and coverage rules. A missing ingestion day must not silently become an observed zero.

Every result retains `model_id`, `origin`, canonical pair identity, model/configuration hashes, input fingerprint, status, and runtime. Successful forecast rows additionally retain 30 raw forecast values, 30 nonnegative forecast features, and clipping diagnostics. Failed rows retain null forecasts plus an error reason, never a fabricated zero vector. Mapped predictions retain `mapper_id` and a finite probability in `[0,1]`. For `timestral_graph`, `timestral_count_only`, `arima`, `prophet`, and `static_logistic_topology`, the ranking `score` must equal the model's predicted link probability within absolute tolerance `1e-12`; do not fit a mapper and then bypass it by ranking a raw forecast sum. Direct baselines retain their separately defined raw scores.

Reject nonfinite output before clipping. Negative finite values become zero, with `n_values_clipped`, minimum raw value, and clipping policy recorded. Never round forecasts to integers. Probability mapping uses the complete 30-vector; replacing it with a sum or handcrafted feature set creates a separately named experiment.

## 2. Timestral: required main model and ablation

The verified checkpoint is `mistralai/Timestral-209M`. It supports numerical targets, past-only covariates, a 32,768-step context, and 21 forecast quantiles [S1]. Use the official `TimestralForecaster` adapter [S2, S3].

| Argument or output | Exact project contract |
| --- | --- |
| `context` | Float32 array `(B, 1, 90)` of raw daily event counts |
| `past_covariates` | Float32 array `(B, 2, 90)`, ordered `[jaccard, preferential_attachment]` |
| Covariate construction | For each historical date `d`, compute features from the trailing 30-day graph ending at `d` |
| `prediction_length` | `30` |
| `known_covariates` | Omitted; future realized graph features are forbidden |
| `symmetric_averaging` | Explicitly `True` |
| `clip_nonnegative` | Explicitly `True`; also enforce shared output validation |
| Point-feature extraction | `forecast.median`, shape `(B, 1, 30)`; detach, move to CPU, then convert |
| Precision | Float32; no quantization or mixed precision in the primary experiment |

Do not externally standardize the Timestral count context or its raw graph covariates. The scaler in section 4 operates on the resulting forecast features, not the numerical input histories. Pair identities and dates must remain aligned across batching and serialization.

Implement two distinct required IDs: `timestral_graph` and `timestral_count_only`. Both use the same 209M weight revision and inference settings. The count-only ablation sets `past_covariates=None`; it changes nothing else. Fine-tuning is outside scope. Do not switch checkpoints for zero or sparse histories: both variants must genuinely forecast those series.

The official implementation already clips eligible nonnegative-context forecasts. Record that backend clipping was enabled; external clipping diagnostics describe only the values actually returned by that backend. Do not invent an unobserved pre-clipping minimum. Real forecasts are not required to be exact zeros for an all-zero context.

The median forecast is an intensity signal, not a proven expected count. A sum of daily medians is not generally the median or expectation of the total; marginal quantiles do not define an interval for that total. The learned probability mapper supplies the link-prediction layer.

## 3. Classical forecast baselines

Fit each baseline independently per pair and origin, on that pair's same 90 observed daily counts. Do not fit across the future target window. Re-estimating a time-series model at each test origin from then-available history is permitted; selecting new settings using test labels is not.

**`arima`:** use `statsmodels.tsa.arima.model.ARIMA`, `order=(1,0,0)`, `trend="c"`, no seasonal terms or exogenous regressors. Retain stationarity/invertibility enforcement, require finite input, and request 30 forecasts from the fitted result [S7]. Do not add automatic order selection. If the default state-space optimizer does not converge, retry the same likelihood with BFGS for up to 150 iterations. A successful retry requires convergence. Persist both attempts in the diagnostics.

**`prophet`:** provide the 90 dates and counts in `ds`/`y` columns and predict the next 30 daily dates [S8]. Fix these options:

```yaml
growth: linear
weekly_seasonality: false
yearly_seasonality: false
daily_seasonality: false
n_changepoints: 5
changepoint_prior_scale: 0.05
seasonality_mode: additive
uncertainty_samples: 0
```

No holidays, custom seasonalities, extra regressors, or parameter search. Use the point prediction `yhat`. Record the actual installed Prophet/backend versions and seed where the backend supports one.

**Constant-history preflight:** before ARIMA or Prophet fitting, if all 90 integer counts equal `c`, return a 30-vector filled with `c` and `status=constant_series`. This is a declared baseline rule applied to every constant history, including all-zero histories, without examining labels. Count shortcut usage in the report. This rule does not apply to Timestral.

Fit exceptions, invalid outputs, and nonconvergence are explicit failures. Capture warnings and optimizer diagnostics. Never respond by substituting another model, silently returning recent means, or dropping the affected candidate. A required model missing pair/origin scores prevents scientific-completion status.

## 4. Frozen logistic mapping of forecast vectors

Fit a separate pipeline for each of `timestral_graph`, `timestral_count_only`, `arima`, and `prophet`:

1. `StandardScaler` on the 30 nonnegative forecast features.
2. Logistic regression with `C=1.0`, pure L2 regularization, `solver="lbfgs"`, `class_weight=None`, `fit_intercept=True`, and `max_iter=2000`.

Fit both stages only on all eligible candidate rows assigned to the **2023 calibration role**, with complete, mature 30-day labels as defined by the experiment schedule. The fixed main run requires all 12 calibration origins and all 435 candidate pairs per origin to have successful forecasts before fitting a mapper. Do not discard failed forecasts or missing origins to fit a reduced panel. Use every positive and negative row; no class balancing, negative sampling, prevalence correction, or sample reweighting. Feature-column order is `forecast_day_01` through `forecast_day_30`.

Serialize the scaler, coefficients, intercept, feature schema, fit-origin list, last label-availability time, class counts, and training-input hash. Freeze before the first 2024 test prediction. Do not refit on test outcomes, recalibrate separately for favorable test origins, or use 2023 fit-set scores as final generalization evidence. Calibration here means a learned probability mapping; empirical calibration quality must still be measured on held-out data.

A calibration set containing only one class is a failed data/experiment precondition. Report it; do not invent probabilities. Constant feature columns are legal and remain subject to the standard scaler's constant-column behavior. A failed optimizer must be investigated and reported rather than treated as a successful fit.

**Version-specific constructor:** the mathematical requirement is L2. For locked scikit-learn versions at or above 1.8, express it using `l1_ratio=0.0`; current documentation deprecates the older `penalty` argument. With an older compatible lock, `penalty="l2"` is the corresponding interface. Do not add the deprecated `n_jobs` argument [S9].

The minimum expensive forecasting scope is 2023 calibration plus 2024 test. Optional 2022 diagnostics must remain separately labeled. There is no requirement to generate all-pair Timestral/ARIMA/Prophet forecasts throughout 2021.

## 5. Direct baselines and topology classifier

For every origin, calculate these scores without fitting:

| Required ID | Score at `T` |
| --- | --- |
| `persistence_binary` | `1` iff the pair has at least one eligible event in `[T-29,T]`; otherwise `0` |
| `recent_count30` | Total eligible event count in `[T-29,T]` |
| `jaccard` | Jaccard similarity on the trailing 30-day graph |
| `common_neighbors` | Number of common neighbors on that graph |
| `preferential_attachment` | Product of endpoint degrees on that graph |

These are ranking scores; binary persistence is the TA-required decision rule. Do not describe raw topology/count scores as probabilities or feed them to probability-only diagnostics. Follow the common metric contract for ties, eligible candidates, and undefined cases.

The required `static_logistic_topology` classifier uses the ordered vector `[jaccard, common_neighbors, log1p(preferential_attachment), min_degree, max_degree]`, computed at the origin from its trailing graph. Use a scaler followed by L2 logistic regression with the same solver, iteration cap, intercept, and unweighted classes as above.

Train each candidate `C` in `[0.1,1.0,10.0]` on 2021 rows, including scaler fitting. Select by 2022 macro average precision across valid origins; break an exact tie with the smaller `C`. Refit scaler and classifier on combined 2021+2022 rows using the selected value and freeze. No extra tuning on 2023 or 2024. A single-class training/refit set or no valid validation AP windows is an explicit failed precondition; do not borrow later labels or claim a successful ordinary fit. A stronger classifier adding interaction-history features is optional and must have a different model ID; it cannot replace this baseline.

## 6. Budget, provenance, and completion

Use one Timestral process, batch size 32 initially, and halve the batch on GPU out-of-memory until successful or size 1 fails. CPU inference remains supported. Default classical fitting to two workers, with a total numerical-thread budget of four. Initialize the foundation model once, cache intermediate forecasts, and resume completed pair/origin tasks. Cache keys must include input hashes, origin, candidate ordering, feature version, source/weight revisions, and inference options. No paid endpoint or broad parameter sweep is required.

Resolve and record full source and weight revisions during installation; do not invent pins or finalize results against moving `main`. Save the environment lock, hardware/device/dtype, runtime, licenses, and weight/config checksums. Official loading supports local cached weights and validates float32 inference [S4]. Code uses Apache-2.0; weights have a separate Modified MIT license [S5]. The ZIP should contain neither downloaded model weights nor credentials.

Ordinary tests use a spy/fake backend to verify shapes, argument routing, temporal boundaries, output validation, and cache invalidation. Scientific completion additionally requires genuine 209M smoke inference and the required real-data evaluation. Missing dependencies or weights produce `blocked`/`not_run`, not synthetic research metrics. A result that fails to beat persistence is still a valid completed study if execution and evaluation are sound.

**Interpretation limitation:** Timestral was released in October 2026, after the 2020–2024 study period. Present this as a retrospective experiment with a later foundation model, not historical deployment performance. Mistral describes a real-and-synthetic post-training mixture; this project has not independently excluded pretraining overlap with GDELT [S6].

## Official sources

- **S1:** [Timestral-209M model card](https://huggingface.co/mistralai/Timestral-209M).
- **S2:** [Official Timestral repository and loading guidance](https://github.com/mistralai/timestral).
- **S3:** [Exact forecast interface and output implementation](https://raw.githubusercontent.com/mistralai/timestral/main/src/timestral/forecaster.py).
- **S4:** [Checkpoint loader and float32 validation note](https://raw.githubusercontent.com/mistralai/timestral/main/src/timestral/loading.py).
- **S5:** [Weight license](https://huggingface.co/mistralai/Timestral-209M/blob/main/LICENSE).
- **S6:** [Mistral release and training description](https://mistral.ai/news/timestral/).
- **S7:** [Statsmodels ARIMA interface](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html).
- **S8:** [Prophet official Python workflow](https://meta.github.io/prophet/docs/quick_start.html).
- **S9:** [Scikit-learn LogisticRegression parameters and deprecations](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).

Sources checked on 2026-11-20. Installation must verify the pinned versions' interfaces; source URLs with `main` are documentation references, not the required reproducibility pins.
