# Experiment protocol

Status: implementation contract and recommended clarification of the submitted proposal. These decisions have not been approved by the TA. The original proposal remains in [`references/original_proposal.pdf`](../references/original_proposal.pdf).

## 1. Research question and claim boundary

For a fixed cohort of countries, can numerical forecasts of recent economic-cooperation activity improve prediction of whether a country pair will receive at least one new GDELT economic-cooperation event record during the next 30 days, compared with persistence, topological scores, and classical forecasting?

The outcome is an observed event-record occurrence. It does not measure trade value, establish the first occurrence of real-world cooperation, or prove the absence of cooperation when no record is found. Repeated cooperation is part of the primary task. Beating a baseline is not a completion requirement: a reproducible negative result is a valid research result.

The evaluated history is 2020-2024. A foundation model released later than those years makes this a retrospective historical evaluation with fixed pretrained weights. Audit and disclose the model's known training provenance and any unknown overlap with the evaluation period. Correct feature timestamps alone do not establish that the pretrained model was historically available or free of pretraining contamination.

## 2. Event records and temporal semantics

An eligible event has all of the following properties:

1. `EventCode` is the exact string `061`.
2. `Actor1CountryCode` and `Actor2CountryCode` are different, nonempty country affiliations admitted by the pinned official CAMEO country-code allowlist.
3. `GLOBALEVENTID` and `DATEADDED` are valid, and the record lies within the configured extraction period.
4. The record passes the input schema and coverage checks.

Use actor affiliations, not the geographic location fields `Actor1Geo_CountryCode`, `Actor2Geo_CountryCode`, or `ActionGeo_CountryCode`. CAMEO country codes are the internal identifiers; do not assume they are interchangeable with every ISO country code. The allowlist must exclude regional and international-organization identifiers and be versioned with its source and checksum. The full run must record its exact allowlist and cohort.

Deduplicate copies of the same `GLOBALEVENTID`. Conflicting copies of an ID are a data-quality error rather than a reason to choose whichever row appeared last. Two distinct IDs remain two event records, including records with reversed actors. Do not claim to have deduplicated real-world news events merely by deduplicating IDs. Do not weight observations by `NumMentions`, `NumArticles`, or `NumSources`.

Set `recorded_day` to the UTC date of `DATEADDED`; retain `SQLDATE` as an audit field. This is an explicit refinement of the proposal: the forecast concerns newly recorded cooperation, and historical observations become available on their recorded day. It avoids silently incorporating a late report into a historical feature window based only on its occurrence date.

For cutoff date `T`, prediction is conceptually issued immediately after the end of UTC day `T`. Inputs include recorded days through `T`; targets begin on `T + 1`. Client or machine local time zones must not change these boundaries.

## 3. Undirected links and frozen candidate panel

Represent each pair as `(country_low, country_high)`, sorted lexicographically, with unequal endpoints. The primary graph is undirected. This is justified as a modeling decision for economic exchange under CAMEO 061, whose codebook describes reciprocal exchange; the raw GDELT actor roles are nevertheless retained in the normalized event table for audit.

Construct the full-study cohort once:

1. Use eligible, deduplicated records with `recorded_day` in calendar year 2020.
2. Count one incidence for each endpoint of each record, before restricting to the final cohort.
3. Rank countries by descending incidence, then ascending country code for ties.
4. Select the first 30 countries and freeze that set `V` before producing 2021 examples.

Insufficient valid countries is a failed full-study precondition. A smaller demo cohort must be a separately labeled profile, not a silent replacement. Do not select countries by their 2021-2024 activity, and do not revise the roster when a later country first appears.

At every origin the candidate set is every unordered pair in `V`, including pairs never observed before that origin. For 30 countries, this is exactly 435 pairs. No self-links, duplicate reversals, test-active-pair filtering, or retrospective pair discovery are permitted. All models receive the same candidate panel.

Define daily counts and the primary target:

```text
y[u,v,d] = number of distinct eligible event IDs for canonical pair {u,v}
           whose recorded_day is d

label[u,v,T] = 1 if sum(y[u,v,d] for d in [T+1, T+30]) >= 1 else 0
```

If a required day has verified coverage but zero eligible events, its count is zero. A missing or failed extraction is not verified zero activity. The coverage gate must reject or explicitly exclude an incomplete origin before labels or metrics are produced, consistently for every model.

## 4. Negatives and useful subsets

A negative is a candidate pair with no eligible observed record in the complete next-30-day target window. It is an observational non-event, not a verified absence of economic cooperation.

Use every candidate pair during fitting, validation, calibration, and testing. Negative sampling is unnecessary at this cohort size and is prohibited in the primary study. Report the number of positives, negatives, candidates, and positive prevalence for every origin.

In addition to the main results, report the two historical activity strata:

- `active_last_30`: at least one record in `[T-29, T]`.
- `inactive_last_30`: no record in `[T-29, T]`.

Compute these flags only from history available at `T`. Inactivity for 30 days is not proof of a novel relationship. An optional `never_seen_so_far` diagnostic may use all recorded history from the dataset start through `T`; label it precisely and do not replace the main candidate set or outcome with it. If a subset lacks the classes needed by a metric, report the metric as undefined with its support.

## 5. Historical graph and sequence construction

For each day `d`, build a simple graph on the frozen vertex set `V`, with an edge when that pair has at least one record during `[d-29, d]`. The graph is updated daily and uses a trailing 30-day aggregation window. This is a documented refinement of the proposal's unspecified daily snapshot, not a hidden change made after observing test performance.

Restrict graph edges and degrees to `V`. Multiple records do not create parallel graph edges. Keep isolated countries in `V`.

For each pair and day, calculate common neighbors, Jaccard similarity, and preferential attachment from the same graph:

```text
common_neighbors = size(N(u) intersection N(v))
jaccard = common_neighbors / size(N(u) union N(v)), or 0 if union is empty
preferential_attachment = degree(u) * degree(v)
```

At cutoff `T`, the main numerical context has exactly 90 daily rows, `[T-89, T]`, with channels `[count, jaccard, preferential_attachment]`. Because the earliest graph row also requires a 30-day graph history, the raw support is exactly 119 days, `[T-118, T]`. Require complete coverage for that support. A sequence length of 91, a 90-day raw-data allowance, or a centered rolling window is incorrect.

Any Timestral adapter limitation concerning multivariate inputs must be handled according to the verified model-capability decision in the architecture documents. Do not fabricate support or silently present another model as Timestral.

## 6. Temporal phases and prediction origins

| Calendar period | Purpose | Permitted learning |
| --- | --- | --- |
| 2020 | Cohort selection and warm-up | Define `V` using only 2020 incidence |
| 2021 | Initial fitting | Fit the static logistic baseline and its scaler |
| 2022 | Validation | Select static-logistic regularization using validation macro AP |
| 2021-2022 | Final supervised refit | Refit the chosen static logistic configuration and scaler |
| 2023 | Probability calibration | Fit the forecast-to-link mappings using 2023 forecast vectors and outcomes |
| 2024 | Final test | Score frozen global models using rolling, available historical observations |

For each year, define target windows starting January 1, then every 30 days, retaining only windows with all 30 target days in that year. Each year therefore contributes 12 target windows. Cutoff `T` is the day immediately before its target window begins. These are 30-day blocks, not calendar months.

| Year | First cutoff | Last cutoff | Last target window | Unscored tail |
| --- | --- | --- | --- | --- |
| 2021 | 2020-12-31 | 2021-11-26 | 2021-11-27 to 2021-12-26 | 5 days |
| 2022 | 2021-12-31 | 2022-11-26 | 2022-11-27 to 2022-12-26 | 5 days |
| 2023 | 2022-12-31 | 2023-11-26 | 2023-11-27 to 2023-12-26 | 5 days |
| 2024 | 2023-12-31 | 2024-11-25 | 2024-11-26 to 2024-12-25 | 6 days |

The omitted tails are excluded as target blocks, not deleted from the event history. They may appear in a later origin's historical inputs. No random row split is allowed. All examples from one origin stay in the same phase.

Overlapping historical contexts across adjacent origins are intentional; overlapping target windows are not. Earlier 2024 observations may enter later 2024 contexts because they would then be available. No 2024 outcome may select a hyperparameter, country roster, feature definition, model family, or probability mapping.

## 7. Required models and fitting rules

Every full-study comparison includes the following models on the identical 435-pair panel:

| Model | Required behavior |
| --- | --- |
| `persistence_binary` | Binary score: one or more records in `[T-29,T]` |
| `recent_count30` | Total eligible record count in `[T-29,T]` |
| `jaccard` | Score from the trailing-30-day graph at `T` |
| `common_neighbors` | Score from the same graph at `T` |
| `preferential_attachment` | Product of endpoint degrees in the same graph at `T` |
| `static_logistic_topology` | Supervised classification on the fixed topological feature vector below |
| `arima` | 30 count forecasts from the last 90 observed daily counts, with preregistered configuration |
| `prophet` | Same count context and horizon, with preregistered configuration |
| `timestral_graph` | Verified numerical adapter with historical graph covariates and its own 30-day forecast-to-link head |
| `timestral_count_only` | Same checkpoint/settings without graph covariates and with its own separately fitted head |

The static-logistic feature vector is `[jaccard, common_neighbors, log1p(preferential_attachment), min_endpoint_degree, max_endpoint_degree]` at `T`. Fit `StandardScaler` and logistic regression on 2021 examples. Select `C` from exactly `[0.1, 1.0, 10.0]` using the highest 2022 macro AP; choose the smallest `C` if tied. Refit scaler and estimator on combined 2021-2022 examples with the selected `C`. Do not use 2023 or 2024 to expand the search. Other estimator arguments follow the fixed configuration file.

For each of `timestral_graph`, `timestral_count_only`, `arima`, and `prophet`, generate a 30-dimensional point-forecast vector at each 2023 origin using only the designated history through that origin. Apply the adapter's fixed, documented postprocessing. Fit a separate `StandardScaler` plus logistic-regression mapping with `C=1.0` to those forecast vectors and the next-30-day binary outcomes. The fixed main run requires all 12 x 435 = 5,220 calibration examples per model with successful forecasts and complete coverage. Missing required examples block that mapper; they cannot be dropped to create a reduced calibration panel. The scaler is fit to forecast vectors, not future realized trajectories. Neither its parameters nor the logistic mapping sees 2024 data.

The forecast-to-link head is supervised, even when the foundation model's numerical forecast is zero-shot. Describe that distinction accurately.

Freeze before the first 2024 prediction: the country roster, preprocessing rules, graph width, global model weights, learned static-logistic pipeline, calibration heads, and all selected hyperparameters. The Timestral pretrained backbone is never fine-tuned in the required study.

**Local classical fitting is permitted:** ARIMA and Prophet fit their local series parameters separately at each origin on the rolling 90-day context. This is part of their predeclared forecasting algorithm, not global model selection or training on future outcomes. Their orders, seasonalities, optimization policy, and fallback rules remain fixed. Do not describe this as freezing every local ARIMA/Prophet parameter before 2024.

Model failures must produce explicit status records. Never omit failed pairs from only that model's metrics. Any permitted fallback must be declared in advance, tested, retained in the output, and counted in the report. A single-class fitting or calibration set must invoke the model contract's explicit degenerate-data policy; it must never borrow later labels or pretend an ordinary fit succeeded.

The continuous 30-day-count baseline, preferential-attachment score, and count-only Timestral ablation are required additional comparators. They supplement every comparator promised in the proposal. A topology-plus-history logistic baseline is optional and cannot replace `static_logistic_topology`. Keep the binary persistence baseline as its own named result.

## 8. Metrics and ranking conventions

**Primary selection and comparison metric:** macro average precision (AP) across complete eligible origins. The proposal's ROC-AUC, Precision@K, and MRR remain mandatory. AP is added to make performance under the actual candidate-panel prevalence easier to assess.

Compute each metric separately per origin, then take an unweighted mean across origins where that metric is defined. Publish the number of eligible, evaluated, and metric-defined origins, with exclusion reasons. A pooled dyad-window metric is secondary and must not replace the macro result.

### ROC-AUC and AP

ROC-AUC gives half credit to tied positive-negative scores. AP uses score-threshold groups, so a tied group enters together; do not resolve ties lexicographically before computing AP.

For no-positive origins, ROC-AUC and AP are undefined. For all-positive origins, ROC-AUC is undefined and AP is 1. Return null and an explicit reason for undefined metrics, not zero or an invented 0.5.

### Precision@K

Report `K = 10, 25, 50`. On the full panel each K is less than 435. If a tie crosses the cutoff, use the expected number of positive hits under uniform selection from the tied group. If `a` items rank strictly above the cutoff tie, `h` of them are positive, and the boundary tie has `b` items including `p` positives, then:

```text
expected_precision_at_k = (h + (K-a)*p/b) / K
```

This avoids assigning artificial advantage to country-code order, especially for binary persistence. A small demo may use `K_effective = min(K, candidate_count)`; report both requested and effective K. No-positive origins have Precision@K equal to zero.

### Filtered MRR with mean-rank ties

For every positive undirected pair `{u,v}`, evaluate both endpoint queries `u -> v` and `v -> u`. For query `u -> v`, rank `v` among all other cohort countries using the corresponding pair scores. Remove other targets that are positive for `u` **at this same origin**, while retaining `v`. This is an evaluation-only filter, never an inference input. Do not remove targets because they are positive at some different or later origin.

For the target after filtering, define:

```text
rank = number_of_strictly_higher_scores + (number_tied_including_target + 1)/2
reciprocal_rank = 1/rank
```

Average reciprocal ranks over both endpoint queries for every positive pair at the origin, then macro-average those origin-level MRR values. This is the reciprocal of the mean tied rank; it is not the expectation of reciprocal rank over random tie permutations. An origin with no positive pair has undefined MRR and zero query support.

### Hand-checkable metric fixture

For four countries A, B, C, D, let only AB be positive, with scores `AD=.9, AB=.7, AC=.7, BC=.6, BD=.2, CD=.1`. Expected ROC-AUC is `0.7`, AP is `1/3`, tie-aware Precision@2 is `0.25`, and filtered MRR is `0.7`. In MRR, A's target B has mean rank 2.5 and reciprocal 0.4; B's target A has rank 1 and reciprocal 1.

## 9. Comparison, uncertainty, and interpretation

Report per-window results and paired per-window differences against persistence. Compare models only over the same complete origins; show support rather than hiding excluded windows. Include prevalence, persistence activity rate, forecast failure/fallback counts, and inference/fit runtime alongside quality metrics.

There are only 12 primary test windows. Dyads share countries and news conditions; neighboring windows may remain dependent despite non-overlapping labels. Do not treat all 5,220 dyad-window rows as independent observations to claim narrow uncertainty intervals.

An optional exploratory paired block bootstrap may resample consecutive window blocks, using the same sampled blocks for all compared models, a fixed seed, and 2,000 replicates. Record the block length and construction. Explain the limited temporal sample and dependence assumption. Such an interval does not establish general superiority. A descriptive paired-window table is sufficient for the required result.

Report weak, equal, or worse Timestral performance honestly. Do not change the target, roster, metrics, or reporting population after seeing the test results to obtain a favorable ranking.

## 10. Profiles and completion conditions

The **full study** is the complete 2020-2024, top-30-country, all-pairs protocol with every required baseline and all 12 planned origins in each designated phase. Missing required coverage or a missing required pair/model score prevents full scientific-completion status. Partial diagnostic outputs may exclude invalid origins consistently across models, but must remain labeled incomplete. The restriction to 30 countries is part of the study definition and must appear in the report title/subtitle or methods summary.

The **demo** uses small synthetic or explicitly labeled fixture data to exercise the pipeline, contracts, and report generation offline. It is an engineering check, never evidence of real-data accuracy. A smaller real-data pilot is also labeled pilot and cannot count as completion of the full study.

An **all-country expansion** is optional. It must define its roster from 2020 only, run the same required baselines on its own identical candidate panel, and fit/calibrate under the same temporal rules. Do not compare a cheap model on all countries with an expensive model on a test-selected subset and call it a fair comparison.

Before a full expensive run, estimate costs from a bounded pilot. Cache deterministic data, features, and forecasts under configuration/content hashes. Never drop Prophet or ARIMA selectively to meet an implicit time limit. If resources or model access block the full run, retain the working demo, explicit blocker, completed outputs, and resumable execution plan; report the study as incomplete.

Required final evidence includes the frozen cohort and allowlist, event filtering and coverage counts, origin schedule, model/adapter versions and configuration hashes, per-pair predictions and statuses, per-window metrics and supports, macro comparison, test log, reproducibility instructions, and limitations. No real-data score may be copied from fixtures or inferred from a model name.

## Sources

- Original project proposal: [`references/original_proposal.pdf`](../references/original_proposal.pdf), especially Sections 3.1-3.3. The attached TA feedback requires a link definition, candidate pairs, negative handling, and a last-30-day persistence baseline.
- GDELT, [Event Database Data Format Codebook V2.0](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf): actor affiliations, event IDs, event-code strings, and UTC `DATEADDED` semantics.
- Schrodt et al., [CAMEO Event and Actor Codebook v1.1b3](https://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf), printed page 34 / PDF page 40: economic cooperation under code 061. The codebook supports the relation interpretation; the cohort, windows, metrics, and evaluation rules above are this project's explicit design choices.
