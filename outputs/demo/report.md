# Forecasting International Economic Cooperation Links in Temporal Event Networks Using GDELT and Timestral

**SYNTHETIC SOFTWARE DEMONSTRATION - NOT RESEARCH RESULTS**

Urvi Desai, Sinchana Arun, and Varesh Patel

Rutgers course project. Recorded 2026-11-20. Run demo.

## Abstract

This offline report verifies the data-to-metrics workflow with synthetic inputs.

## Problem definition

An economic-cooperation link is at least one distinct GDELT 2.0 event ID with exact CAMEO 061 for an unordered pair during UTC days T+1 through T+30. The endpoints are actor-country affiliations. Observations enter the history on their UTC DATEADDED day, with SQLDATE retained for audit.

A negative is a candidate pair with zero qualifying records in a fully covered target window. Every selected pair is retained, including pairs with no previous record. Missing extraction coverage invalidates the affected origin.

## Data and coverage

The offline fixture exercises 6 synthetic candidate pairs.

| country_code | incidence | rank | selection_year | selected | synthetic |
| --- | --- | --- | --- | --- | --- |
| AUS | — | 1 | — | True | True |
| CAN | — | 2 | — | True | True |
| IND | — | 3 | — | True | True |
| USA | — | 4 | — | True | True |

| Cleaning audit | Observed value |
| --- | --- |
| cohort_retained | 9 |
| cohort_retained_share | 1.0 |
| duplicate | 1 |
| eligible_unique | 9 |
| source_rows | 10 |

| Origin | Candidates | Positives | Negatives | Positive prevalence | Active last 30 days | Eligible cohort records | Extraction coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01-31 | 6 | 3 | 3 | 0.5000 | 0.5000 | 3 | complete |

![Observed link prevalence and activity](figures/observed_activity.svg)

## Methods and temporal protocol

A rolling 30-day graph includes an edge for any recorded pair activity by each day's cutoff. Timestral-209M uses 90 daily count rows and, for the graph variant, historical Jaccard and preferential attachment. Graph aggregation extends raw input support to 119 days. The count-only variant uses 90 days of counts. Its comparison with the enriched variant reflects both topology and the larger effective raw history.

2020 establishes the cohort. The topology logistic scaler and classifier train on 2021, select regularization by 2022 macro AP, and refit on both years. Four separate forecast-to-link logistic heads train on 2023 only. Pretrained Timestral inference is zero-shot and its forecast-to-link mapping is supervised. Frozen global artifacts score 2024. ARIMA and Prophet may fit local rolling histories under their fixed specifications.

The fixed calendar uses 12 full 30-day blocks starting January 1 of each evaluated year. The final five days of non-leap years and six days of leap years remain available as history after their observations mature.

## Baselines and metrics

Binary persistence is 1 when the pair has a record from T−29 through T and 0 otherwise. Recent count and the graph scores use that same cutoff. ARIMA and Prophet repeat an observed constant history with an explicit constant-series status.

Each metric is calculated by origin. Macro averages weight defined windows equally. Equal scores receive half credit in ROC-AUC and enter AP as a single threshold group. Precision uses expected hits across cutoff ties. Filtered MRR keeps each positive target and every negative, removes other same-origin positive targets, and averages reciprocal mean ranks across both endpoints.

| model_id | backend_kind | status | library | version | source_revision | weights_revision | device | dtype |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | deterministic_rule | complete | — | — | — | — | — | — |
| recent_count30 | deterministic_rule | complete | — | — | — | — | — | — |
| jaccard | deterministic_rule | complete | — | — | — | — | — | — |
| common_neighbors | deterministic_rule | complete | — | — | — | — | — | — |
| preferential_attachment | deterministic_rule | complete | — | — | — | — | — | — |
| demo_forecast_stub | fake | complete | — | — | — | — | — | — |

## Results

| Model | Macro AP | Macro ROC-AUC | P@2 | P@10 | Filtered MRR | Brier error | AP windows | AUC windows | Scored rows | Failures | Constant shortcuts | Runtime (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | 0.4444 | 0.3333 | 0.3333 | 0.5000 | 0.7333 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |
| recent_count30 | 0.4444 | 0.2778 | 0.2500 | 0.5000 | 0.7333 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |
| jaccard | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.8000 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |
| common_neighbors | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.8000 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |
| preferential_attachment | 0.4333 | 0.2222 | 0.2500 | 0.5000 | 0.6889 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |
| demo_forecast_stub | 0.4444 | 0.2778 | 0.2500 | 0.5000 | 0.7333 | — | 1/1 | 1/1 | 6 | 0 | 0 | 0.00 |

An em dash marks an undefined or unavailable value. Null reasons and query supports are recorded by origin in metrics_by_origin.csv.

![Average precision by origin](figures/performance_by_origin.svg)

## Paired average precision

| Origin | Model | Reference | AP | Reference AP | Difference | Sign |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-01-31 | recent_count30 | persistence_binary | 0.4444 | 0.4444 | 0.0000 | 0 |
| 2024-01-31 | jaccard | persistence_binary | 0.5000 | 0.4444 | 0.0556 | 1 |
| 2024-01-31 | common_neighbors | persistence_binary | 0.5000 | 0.4444 | 0.0556 | 1 |
| 2024-01-31 | preferential_attachment | persistence_binary | 0.4333 | 0.4444 | -0.0111 | -1 |
| 2024-01-31 | demo_forecast_stub | persistence_binary | 0.4444 | 0.4444 | 0.0000 | 0 |

## Prior activity strata

| Model | Stratum | Macro AP | Valid windows | Positives | Scored rows | Null reasons |
| --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| persistence_binary | inactive_last_30 | 0.6667 | 1 | 2 | 3 | — |
| recent_count30 | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| recent_count30 | inactive_last_30 | 0.6667 | 1 | 2 | 3 | — |
| jaccard | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| jaccard | inactive_last_30 | 0.5833 | 1 | 2 | 3 | — |
| common_neighbors | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| common_neighbors | inactive_last_30 | 0.5833 | 1 | 2 | 3 | — |
| preferential_attachment | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| preferential_attachment | inactive_last_30 | 0.5833 | 1 | 2 | 3 | — |
| demo_forecast_stub | active_last_30 | 0.3333 | 1 | 1 | 3 | — |
| demo_forecast_stub | inactive_last_30 | 0.6667 | 1 | 2 | 3 | — |

## Diagnostics and limitations

Repeated records can describe the same real-world incident. New recorded activity can include old events and repeat interactions. An inactive pair may have interacted before the last 30 days. The top-30 cohort favors well-observed countries.

Timestral was released in 2026, after the evaluation period. The study is retrospective and the extent of pretraining overlap is unknown. The numerical median forecast is a feature for supervised mapping. Empirical probability quality is assessed with Brier error and fixed reliability bins when probability outputs are available.

The 12 planned test windows share countries and news conditions. The paired differences are descriptive measures from those windows.

## Reproducibility

| Input identity | SHA-256 |
| --- | --- |
| config_sha256 | 5e6b6f7f9d7eb6ef5f8a876e7401a90b3247db91c50b119b75009c20989e0ac6 |
| data_sha256 | 5212d4926aff743ae8dff081d8368bffb8958f9281b281d8c963eaf8336945f2 |
| country_registry_sha256 | 530da1e94994e89098c7cbf91d8b525743142fb7deb689c594b4f57ce2129866 |
| cohort_sha256 | a6368d70e1ca5babab7f052a1f0a13c474f43fac9fb3358f9a4b281f1d05e930 |
| environment_lock_sha256 | 7395c8da2d0dcef1211b4fa42c8e1572415b965b3f0f24b87f4c3ed0c042a6cb |

| Environment | Recorded value |
| --- | --- |
| lock_sha256 | 7395c8da2d0dcef1211b4fa42c8e1572415b965b3f0f24b87f4c3ed0c042a6cb |
| logical_cpus | 12 |
| machine | arm64 |
| packages | {'cmdstanpy': '1.3.2', 'huggingface-hub': '2.4.0', 'matplotlib': '3.11.2', 'numpy': '2.5.5', 'pandas': '3.1.1', 'prophet': '1.5.0', 'pyarrow': '26.0.1', 'scikit-learn': '1.9.1', 'scipy': '1.18.1', 'statsmodels': '0.15.0', 'timestral': '1.0.0', 'torch': '2.15.0'} |
| platform | macOS-27.2.1-arm64-arm-64bit |
| processor | arm |
| python | 3.12.11 |

| Completion | Result |
| --- | --- |
| engineering_complete | False |
| demo_complete | True |
| research_complete | False |

| stage | code | detail |
| --- | --- | --- |
| research | synthetic_profile | Real GDELT source and genuine research model execution required |

```sh
cooperalink demo --config config/demo.json
```

## Response to TA feedback

| Feedback | Implemented definition | Evidence |
| --- | --- | --- |
| Define a link | One exact-061 record per pair suffices in the next 30 recorded days. | Target boundary and temporal contract tests. |
| Specify candidates | Frozen 2020 top-30 roster and every unordered pair for the main experiment. | Cohort and candidate artifacts, complete panel validation. |
| Explain negatives | Zero qualifying records in a verified window. Retain the full panel. | Coverage checks and origin-level positive and negative counts. |
| Include persistence | Binary recent activity over T−29 through T. | Persistence boundary tests, metric row and paired comparisons. |

## References

[GDELT Event Database v2.0 codebook](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf)

[CAMEO manual, version 1.1b3](https://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf)

[Timestral-209M model card](https://huggingface.co/mistralai/Timestral-209M)

[Official Timestral source](https://github.com/mistralai/timestral)
