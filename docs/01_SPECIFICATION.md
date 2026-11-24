# 01. Research and implementation specification

## Objective

Build a local, reproducible pipeline to predict whether a pair of country affiliations will have at least one newly recorded economic-cooperation event in the next 30 days. Compare a numerical time-series foundation model conditioned on temporal graph features against strong simple and classical baselines. Produce code, auditable outputs, figures, and a course-project report that can be defended against the supplied TA feedback.

The target is **observed news-derived cooperation records**. It is not a treaty database, trade-volume estimator, causal geopolitical model, trading strategy, or proof of countries' actual relationship status. Event records may contain extraction errors, duplicate descriptions of real incidents, and uneven news coverage.

## Source proposal commitments

The two-page supplied proposal specifies GDELT 2.0, CAMEO `061`, data from 2020–2024, a 90-day historical window, Jaccard and preferential-attachment series, Timestral, a 30-day horizon, logistic mapping, walk-forward evaluation, and topological, ARIMA, Prophet, and static logistic baselines. The TA additionally requires a link definition, candidate-pair definition, negative handling, and persistence baseline. The original PDF is preserved in `references/`.

The supplied PDF's `NeurIPS 2023` footer is template furniture, not evidence of publication. The generated report should use a neutral course-project title page and retain Urvi Desai, Sinchana Arun, and Varesh Patel as the proposal authors unless the owner supplies an updated author list. Do not infer instructor, course number, submission deadline, or publication venue.

## Formal target

For a distinct country pair `u < v` and UTC day `d`, define `y(u,v,d)` as the number of distinct accepted GDELT event IDs first added on that day for that pair. At end-of-day cutoff `T`:

```text
label(u,v,T) = 1 if sum(y(u,v,d), d=T+1..T+30) >= 1 else 0
persistence(u,v,T) = 1 if sum(y(u,v,d), d=T-29..T) >= 1 else 0
context_dates(T) = T-89..T                    # 90 daily positions
raw_support_for_graph_context(T) = T-118..T  # 119 daily positions
```

All date ranges above are inclusive. Internally, timestamp queries should use half-open intervals to avoid ambiguity about midnight. `T` means the last complete UTC observation day, not local clock time.

## Candidate cohort

Create a versioned allowlist of genuine country/territorial country-code entries from the official CAMEO country lookup. Exclude aggregate regions, organizations, missing codes, and codes that cannot be resolved unambiguously; record exclusions. Keep raw CAMEO codes internally rather than assuming every code is ISO-3166 compatible. See the data contract for the registry review gate.

Among valid cross-country `061` records first added in 2020, count each distinct record once for each endpoint. Rank countries by descending endpoint incidence, with country code as the deterministic tie-breaker. Select the top 30 and freeze that list before accessing later-year outcomes for model selection. No country needs to have interacted with every other selected country. If fewer than 30 valid countries exist, the research profile fails its declared cohort size and must be explicitly revised; the demo can use four.

The main candidate universe is all unordered pairs in the frozen roster. With 30 countries this is 435 pairs. The graph is the induced graph over this same cohort; countries outside it do not become hidden additional neighbors. Report the cohort selection rule and retained share of source records. This is a restricted-cohort study. An all-eligible-country extension is separately named and is not required for the base deliverable.

## Functional requirements

| ID | Requirement | Observable acceptance |
| --- | --- | --- |
| FR-01 | Ingest local GDELT 2.0 exports or a verified bounded source query | Provenance, typed fields, coverage manifest, reject report |
| FR-02 | Filter, validate, canonicalize, and deduplicate | Exact-code, country-code, self-pair, date and duplicate tests pass |
| FR-03 | Freeze a 2020-only country roster and full pair universe | Saved roster/candidate hashes; exactly 435 unique pairs |
| FR-04 | Produce coverage-aware daily count panels | Complete days have explicit zeros; missing days remain errors |
| FR-05 | Generate causal 90-day contexts and graph covariates | Shapes/date boundaries; future-injection invariance |
| FR-06 | Generate 30-day labels and annual fold manifests | Disjoint complete horizons; no label beyond coverage |
| FR-07 | Implement binary persistence exactly as TA requested | Hand-calculated boundary tests and reported comparator |
| FR-08 | Implement all proposed baselines and additional cheap comparators | Uniform score schema and equal candidate keys |
| FR-09 | Integrate genuine Timestral-209M with past covariates | Pinned source/weights, real inference smoke, shape assertions |
| FR-10 | Fit probability mappings using 2023 only | Saved scaler/model training-row and date provenance |
| FR-11 | Implement untouched 2024 evaluation and count-only ablation | Complete per-origin predictions for every required model |
| FR-12 | Compute explicit, tie-aware, support-aware metrics | Golden metric fixture and per-origin/macro tables |
| FR-13 | Produce readable evidence-backed report and figures | All claims trace to immutable output tables |
| FR-14 | Resume interrupted work and invalidate stale caches | Checkpoint/resume and cache-key integration tests |
| FR-15 | Provide an offline synthetic demonstration | One-command demo visibly marked synthetic |
| FR-16 | Record dependency, data, model and configuration provenance | Full revision/hash manifest with actual environment |
| FR-17 | Separate software completion from real scientific execution | Machine-readable completion status and honest final summary |

## Main experiment and baseline inventory

Required model IDs are stable output keys:

1. `persistence_binary`: the exact last-30-days binary indicator.
2. `recent_count30`: count of records in the last 30 days.
3. `jaccard`: origin graph Jaccard score.
4. `common_neighbors`: origin graph common-neighbor count.
5. `preferential_attachment`: origin graph degree product.
6. `static_logistic_topology`: supervised classifier on five specified graph features.
7. `arima`: fixed ARIMA(1,0,0) context forecasts and a 2023 logistic mapper.
8. `prophet`: fixed low-complexity context forecasts and a 2023 logistic mapper.
9. `timestral_count_only`: genuine 209M target-only ablation plus its own mapper.
10. `timestral_graph`: genuine 209M with two historical graph covariates plus its own mapper.

Do not treat the count-only ablation as an interchangeable replacement for the main model. The additional cheap comparators make it possible to see whether observed gains come from recent activity, graph topology, or the foundation model.

## Evaluation and success

Preserve all originally proposed metrics: ROC-AUC, Precision@K, and MRR. Add average precision as the primary model-selection summary and report candidate prevalence. Use the exact definitions in the protocol, including ties and undefined cases. Primary results macro-average the complete final-year windows; pooled scores are supplementary.

Success means the experiment is valid, the code is tested, and the report answers the research question honestly. It does not require Timestral to outperform persistence. An inconclusive or worse result is acceptable if correctly measured and explained.

## Deliverables from the finished project

- Source code and a locked, documented environment; all tests passing for the implemented system.
- Data extraction/import commands, registry, data dictionary, rejection counts, coverage and split manifests.
- Reproducible feature/prediction caches and fitted mapping artifacts.
- Per-pair predictions, per-window metrics, aggregate comparisons, and conditional inactive/active analyses.
- A report in Markdown and standalone HTML, plus exported figures; an optional PDF can be generated from the same report.
- README reproduction commands, offline demo, source citations, experiment manifest, and completion status.

No public deployment, web application, database server, authentication, payment integration, distributed training, new foundation model training, or automated coursework submission is required.

## Explicit refinements to the proposal

| Previously unspecified detail | Selected implementation |
| --- | --- |
| Pair direction | Undirected bilateral aggregation, preserving raw actor direction for audit |
| Time semantics | First-recorded UTC day to prevent occurrence-date backfilling |
| Country population | Fixed top-30 cohort using only 2020 eligible-record incidence |
| Daily graph support | Trailing 30-day graph refreshed daily |
| Meaning of a positive | Any qualifying record in the entire next-30-day window |
| Negative population | Every other pair in the same fixed complete panel |
| Forecast-to-link fitting | Separate fixed-regularization map on 2023 |
| MRR/tie policy | Filtered endpoint queries and mean-rank ties |

These are recommended design decisions, not changes already approved by the TA. The clarification in `docs/11_TA_FEEDBACK_RESPONSE.md` makes them reviewable without leaving the implementation underspecified.
