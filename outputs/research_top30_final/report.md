# Forecasting International Economic Cooperation Links in Temporal Event Networks Using GDELT and Timestral

Urvi Desai, Sinchana Arun, and Varesh Patel

Rutgers course project. Recorded 2026-11-20. Run research_top30_final.

## Abstract

Timestral with graph covariates had a mean paired AP difference of +0.0674 against binary persistence over 12 defined windows. Window differences ranged from +0.0310 to +0.1070.

## Problem definition

An economic-cooperation link is at least one distinct GDELT 2.0 event ID with exact CAMEO 061 for an unordered pair during UTC days T+1 through T+30. The endpoints are actor-country affiliations. Observations enter the history on their UTC DATEADDED day, with SQLDATE retained for audit.

A negative is a candidate pair with zero qualifying records in a fully covered target window. Every selected pair is retained, including pairs with no previous record. Missing extraction coverage invalidates the affected origin.

## Data and coverage

Extraction interval 2020-01-01 through 2025-01-01 (exclusive). Coverage complete: True. Evidence kind: bigquery_completed_query_full_result.

The fixed cohort contains the top 30 countries by 2020 eligible endpoint incidence, with ties resolved by code. Its 435 unordered pairs appear at every test origin. Coverage describes the extraction from the recorded source snapshot. News access and selection can still vary.

| country_code | incidence | rank | selection_year | selected | synthetic |
| --- | --- | --- | --- | --- | --- |
| CHN | 37191 | 1 | 2020 | True | False |
| USA | 27000 | 2 | 2020 | True | False |
| RUS | 9777 | 3 | 2020 | True | False |
| GBR | 8276 | 4 | 2020 | True | False |
| AUS | 8103 | 5 | 2020 | True | False |
| CAN | 7241 | 6 | 2020 | True | False |
| JPN | 6445 | 7 | 2020 | True | False |
| TUR | 6402 | 8 | 2020 | True | False |
| IRN | 6090 | 9 | 2020 | True | False |
| DEU | 5386 | 10 | 2020 | True | False |
| VNM | 4454 | 11 | 2020 | True | False |
| MEX | 4395 | 12 | 2020 | True | False |
| KOR | 4264 | 13 | 2020 | True | False |
| IDN | 3976 | 14 | 2020 | True | False |
| BRA | 3920 | 15 | 2020 | True | False |
| FRA | 3784 | 16 | 2020 | True | False |
| ISR | 3457 | 17 | 2020 | True | False |
| ITA | 3372 | 18 | 2020 | True | False |
| SAU | 3175 | 19 | 2020 | True | False |
| MYS | 3060 | 20 | 2020 | True | False |
| PAK | 2989 | 21 | 2020 | True | False |
| THA | 2810 | 22 | 2020 | True | False |
| EGY | 2693 | 23 | 2020 | True | False |
| TWN | 2646 | 24 | 2020 | True | False |
| ESP | 2504 | 25 | 2020 | True | False |
| SGP | 2472 | 26 | 2020 | True | False |
| UKR | 2361 | 27 | 2020 | True | False |
| NZL | 2005 | 28 | 2020 | True | False |
| BGD | 1900 | 29 | 2020 | True | False |
| AZE | 1853 | 30 | 2020 | True | False |
| NLD | 1693 | 31 | 2020 | False | False |
| ARG | 1681 | 32 | 2020 | False | False |
| IRQ | 1656 | 33 | 2020 | False | False |
| KEN | 1617 | 34 | 2020 | False | False |
| BLR | 1614 | 35 | 2020 | False | False |
| IRL | 1506 | 36 | 2020 | False | False |
| PHL | 1482 | 37 | 2020 | False | False |
| VEN | 1474 | 38 | 2020 | False | False |
| IND | 1413 | 39 | 2020 | False | False |
| AFG | 1309 | 40 | 2020 | False | False |
| GRC | 1281 | 41 | 2020 | False | False |
| NGA | 1266 | 42 | 2020 | False | False |
| ARE | 1203 | 43 | 2020 | False | False |
| KAZ | 1152 | 44 | 2020 | False | False |
| CHL | 1122 | 45 | 2020 | False | False |
| NOR | 1067 | 46 | 2020 | False | False |
| KHM | 1043 | 47 | 2020 | False | False |
| CHE | 1035 | 48 | 2020 | False | False |
| POL | 1003 | 49 | 2020 | False | False |
| COL | 998 | 50 | 2020 | False | False |
| UGA | 992 | 51 | 2020 | False | False |
| BEL | 977 | 52 | 2020 | False | False |
| QAT | 882 | 53 | 2020 | False | False |
| JOR | 775 | 54 | 2020 | False | False |
| PER | 740 | 55 | 2020 | False | False |
| LKA | 734 | 56 | 2020 | False | False |
| TZA | 728 | 57 | 2020 | False | False |
| MAR | 723 | 58 | 2020 | False | False |
| PSE | 723 | 59 | 2020 | False | False |
| ECU | 712 | 60 | 2020 | False | False |
| DNK | 695 | 61 | 2020 | False | False |
| UZB | 684 | 62 | 2020 | False | False |
| AUT | 652 | 63 | 2020 | False | False |
| PRK | 649 | 64 | 2020 | False | False |
| SYR | 648 | 65 | 2020 | False | False |
| SWE | 626 | 66 | 2020 | False | False |
| NPL | 625 | 67 | 2020 | False | False |
| LBY | 550 | 68 | 2020 | False | False |
| MMR | 547 | 69 | 2020 | False | False |
| BGR | 519 | 70 | 2020 | False | False |
| CUB | 518 | 71 | 2020 | False | False |
| GHA | 505 | 72 | 2020 | False | False |
| KWT | 500 | 73 | 2020 | False | False |
| ARM | 488 | 74 | 2020 | False | False |
| PRT | 481 | 75 | 2020 | False | False |
| ZWE | 481 | 76 | 2020 | False | False |
| TKM | 471 | 77 | 2020 | False | False |
| CZE | 468 | 78 | 2020 | False | False |
| LBN | 462 | 79 | 2020 | False | False |
| LTU | 439 | 80 | 2020 | False | False |
| DZA | 437 | 81 | 2020 | False | False |
| ETH | 436 | 82 | 2020 | False | False |
| FIN | 425 | 83 | 2020 | False | False |
| KGZ | 391 | 84 | 2020 | False | False |
| RWA | 372 | 85 | 2020 | False | False |
| URY | 368 | 86 | 2020 | False | False |
| AGO | 358 | 87 | 2020 | False | False |
| MNG | 354 | 88 | 2020 | False | False |
| BHR | 337 | 89 | 2020 | False | False |
| OMN | 337 | 90 | 2020 | False | False |
| BOL | 336 | 91 | 2020 | False | False |
| LAO | 329 | 92 | 2020 | False | False |
| ZAF | 328 | 93 | 2020 | False | False |
| HUN | 321 | 94 | 2020 | False | False |
| SRB | 314 | 95 | 2020 | False | False |
| SDN | 310 | 96 | 2020 | False | False |
| BRN | 288 | 97 | 2020 | False | False |
| MOZ | 288 | 98 | 2020 | False | False |
| PRY | 284 | 99 | 2020 | False | False |
| GTM | 283 | 100 | 2020 | False | False |
| TJK | 281 | 101 | 2020 | False | False |
| TUN | 271 | 102 | 2020 | False | False |
| YEM | 235 | 103 | 2020 | False | False |
| SOM | 225 | 104 | 2020 | False | False |
| ZMB | 225 | 105 | 2020 | False | False |
| SEN | 224 | 106 | 2020 | False | False |
| PAN | 222 | 107 | 2020 | False | False |
| NAM | 220 | 108 | 2020 | False | False |
| LVA | 213 | 109 | 2020 | False | False |
| CRI | 206 | 110 | 2020 | False | False |
| NER | 201 | 111 | 2020 | False | False |
| BEN | 196 | 112 | 2020 | False | False |
| HND | 194 | 113 | 2020 | False | False |
| MDV | 192 | 114 | 2020 | False | False |
| HRV | 179 | 115 | 2020 | False | False |
| EST | 178 | 116 | 2020 | False | False |
| JAM | 173 | 117 | 2020 | False | False |
| MDA | 173 | 118 | 2020 | False | False |
| CYP | 171 | 119 | 2020 | False | False |
| CMR | 167 | 120 | 2020 | False | False |
| NIC | 164 | 121 | 2020 | False | False |
| SVK | 163 | 122 | 2020 | False | False |
| ISL | 161 | 123 | 2020 | False | False |
| TTO | 160 | 124 | 2020 | False | False |
| BTN | 148 | 125 | 2020 | False | False |
| COD | 141 | 126 | 2020 | False | False |
| MDG | 135 | 127 | 2020 | False | False |
| TGO | 124 | 128 | 2020 | False | False |
| CPV | 119 | 129 | 2020 | False | False |
| FJI | 115 | 130 | 2020 | False | False |
| ALB | 113 | 131 | 2020 | False | False |
| CIV | 110 | 132 | 2020 | False | False |
| MUS | 103 | 133 | 2020 | False | False |
| BWA | 97 | 134 | 2020 | False | False |
| GUY | 97 | 135 | 2020 | False | False |
| BFA | 96 | 136 | 2020 | False | False |
| MLT | 90 | 137 | 2020 | False | False |
| MKD | 87 | 138 | 2020 | False | False |
| MWI | 86 | 139 | 2020 | False | False |
| COG | 83 | 140 | 2020 | False | False |
| DOM | 83 | 141 | 2020 | False | False |
| BDI | 81 | 142 | 2020 | False | False |
| MLI | 77 | 143 | 2020 | False | False |
| LBR | 76 | 144 | 2020 | False | False |
| SLV | 71 | 145 | 2020 | False | False |
| TCD | 68 | 146 | 2020 | False | False |
| BRB | 67 | 147 | 2020 | False | False |
| LUX | 67 | 148 | 2020 | False | False |
| GMB | 64 | 149 | 2020 | False | False |
| DJI | 61 | 150 | 2020 | False | False |
| BLZ | 58 | 151 | 2020 | False | False |
| MRT | 58 | 152 | 2020 | False | False |
| PNG | 58 | 153 | 2020 | False | False |
| SLB | 58 | 154 | 2020 | False | False |
| GAB | 57 | 155 | 2020 | False | False |
| GIN | 55 | 156 | 2020 | False | False |
| BMU | 54 | 157 | 2020 | False | False |
| LSO | 51 | 158 | 2020 | False | False |
| MCO | 47 | 159 | 2020 | False | False |
| HTI | 46 | 160 | 2020 | False | False |
| SUR | 42 | 161 | 2020 | False | False |
| ATG | 40 | 162 | 2020 | False | False |
| GRD | 39 | 163 | 2020 | False | False |
| VUT | 39 | 164 | 2020 | False | False |
| SYC | 35 | 165 | 2020 | False | False |
| BHS | 33 | 166 | 2020 | False | False |
| SLE | 31 | 167 | 2020 | False | False |
| TMP | 30 | 168 | 2020 | False | False |
| VCT | 27 | 169 | 2020 | False | False |
| LIE | 26 | 170 | 2020 | False | False |
| WSM | 26 | 171 | 2020 | False | False |
| GNQ | 24 | 172 | 2020 | False | False |
| CAF | 22 | 173 | 2020 | False | False |
| GNB | 20 | 174 | 2020 | False | False |
| ERI | 15 | 175 | 2020 | False | False |
| HKG | 15 | 176 | 2020 | False | False |
| CYM | 13 | 177 | 2020 | False | False |
| LCA | 13 | 178 | 2020 | False | False |
| TON | 13 | 179 | 2020 | False | False |
| COK | 12 | 180 | 2020 | False | False |
| SWZ | 10 | 181 | 2020 | False | False |
| MAC | 9 | 182 | 2020 | False | False |
| VAT | 8 | 183 | 2020 | False | False |
| COM | 7 | 184 | 2020 | False | False |
| FSM | 7 | 185 | 2020 | False | False |
| AND | 6 | 186 | 2020 | False | False |
| KNA | 5 | 187 | 2020 | False | False |
| MHL | 5 | 188 | 2020 | False | False |
| ABW | 4 | 189 | 2020 | False | False |
| NRU | 4 | 190 | 2020 | False | False |
| PLW | 3 | 191 | 2020 | False | False |
| SMR | 3 | 192 | 2020 | False | False |
| AIA | 1 | 193 | 2020 | False | False |
| DMA | 1 | 194 | 2020 | False | False |
| WLF | 1 | 195 | 2020 | False | False |

| Cleaning audit | Observed value |
| --- | --- |
| blank_country | 1050530 |
| cohort_retained | 356464 |
| cohort_retained_share | 0.5532217362829056 |
| conflicts | 0 |
| duplicate | 0 |
| eligible_by_year | {'2020': 122445, '2021': 103882, '2022': 138417, '2023': 150656, '2024': 128942} |
| eligible_copies | 644342 |
| eligible_unique | 644342 |
| excluded_country_codes | {'AFR': 24630, 'ASA': 151, 'CAS': 85, 'CRB': 62, 'EAF': 74, 'EUR': 76797, 'LAM': 2, 'MEA': 96, 'NMR': 5378, 'PGS': 446, 'SAF': 130, 'SAM': 14, 'SAS': 789, 'SCN': 1, 'SEA': 7111, 'SSD': 949, 'WAF': 233, 'WST': 1127} |
| lag_days_histogram | {'0': 615253, '1': 1237, '30': 3016, '365': 20153, '3650': 348, '36525': 1420, '7': 2915} |
| malformed | 0 |
| relation | 0 |
| self_pair | 39372 |
| source_rows | 1846939 |
| unknown_country | 112695 |

| Origin | Candidates | Positives | Negatives | Positive prevalence | Active last 30 days | Eligible cohort records | Extraction coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-12-31 | 435 | 287 | 148 | 0.6598 | 0.5954 | 5771 | complete |
| 2024-01-30 | 435 | 282 | 153 | 0.6483 | 0.6598 | 5464 | complete |
| 2024-02-29 | 435 | 297 | 138 | 0.6828 | 0.6483 | 6452 | complete |
| 2024-03-30 | 435 | 275 | 160 | 0.6322 | 0.6828 | 6399 | complete |
| 2024-04-29 | 435 | 285 | 150 | 0.6552 | 0.6322 | 5826 | complete |
| 2024-05-29 | 435 | 277 | 158 | 0.6368 | 0.6552 | 5528 | complete |
| 2024-06-28 | 435 | 255 | 180 | 0.5862 | 0.6368 | 4629 | complete |
| 2024-07-28 | 435 | 283 | 152 | 0.6506 | 0.5862 | 4939 | complete |
| 2024-08-27 | 435 | 274 | 161 | 0.6299 | 0.6506 | 5759 | complete |
| 2024-09-26 | 435 | 289 | 146 | 0.6644 | 0.6299 | 5338 | complete |
| 2024-10-26 | 435 | 274 | 161 | 0.6299 | 0.6644 | 5246 | complete |
| 2024-11-25 | 435 | 272 | 163 | 0.6253 | 0.6299 | 6665 | complete |

![Observed link prevalence and activity](figures/observed_activity.svg)

## Methods and temporal protocol

A rolling 30-day graph includes an edge for any recorded pair activity by each day's cutoff. Timestral-209M uses 90 daily count rows and, for the graph variant, historical Jaccard and preferential attachment. Graph aggregation extends raw input support to 119 days. The count-only variant uses 90 days of counts. Its comparison with the enriched variant reflects both topology and the larger effective raw history.

2020 establishes the cohort. The topology logistic scaler and classifier train on 2021, select regularization by 2022 macro AP, and refit on both years. Four separate forecast-to-link logistic heads train on 2023 only. Pretrained Timestral inference is zero-shot and its forecast-to-link mapping is supervised. Frozen global artifacts score 2024. ARIMA and Prophet may fit local rolling histories under their fixed specifications.

The fixed calendar uses 12 full 30-day blocks starting January 1 of each evaluated year. The final five days of non-leap years and six days of leap years remain available as history after their observations mature.

## Baselines and metrics

Binary persistence is 1 when the pair has a record from T−29 through T and 0 otherwise. Recent count and the graph scores use that same cutoff. ARIMA and Prophet repeat an observed constant history with an explicit constant-series status.

Each metric is calculated by origin. Macro averages weight defined windows equally. Equal scores receive half credit in ROC-AUC and enter AP as a single threshold group. Precision uses expected hits across cutoff ties. Filtered MRR keeps each positive target and every negative, removes other same-origin positive targets, and averages reciprocal mean ranks across both endpoints.

![Registered research year roles](figures/timeline.svg)

| model_id | backend_kind | status | library | version | source_revision | weights_revision | device | dtype |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | deterministic_rule | complete | — | — | — | — | — | — |
| recent_count30 | deterministic_rule | complete | — | — | — | — | — | — |
| jaccard | deterministic_rule | complete | — | — | — | — | — | — |
| common_neighbors | deterministic_rule | complete | — | — | — | — | — | — |
| preferential_attachment | deterministic_rule | complete | — | — | — | — | — | — |
| static_logistic_topology | real | complete | scikit-learn | 1.9.1 | — | — | — | — |
| arima | real | complete | statsmodels | 0.15.0 | — | — | — | — |
| prophet | real | complete | prophet | 1.5.0 | — | — | — | — |
| timestral_count_only | real | complete | timestral | 1.0.0 | a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff | 9874d252ab0aae16f7f7c999f98f98d6ad7d8365 | cpu | torch.float32 |
| timestral_graph | real | complete | timestral | 1.0.0 | a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff | 9874d252ab0aae16f7f7c999f98f98d6ad7d8365 | cpu | torch.float32 |

## Results

| Model | Macro AP | Macro ROC-AUC | P@10 | P@25 | P@50 | Filtered MRR | Brier error | AP windows | AUC windows | Scored rows | Failures | Constant shortcuts | Runtime (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | 0.7607 | 0.7099 | 0.7925 | 0.7925 | 0.7925 | 0.3820 | — | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| recent_count30 | 0.8699 | 0.7902 | 1.0000 | 1.0000 | 0.9967 | 0.6245 | — | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| jaccard | 0.7958 | 0.6903 | 0.9583 | 0.9306 | 0.8895 | 0.4691 | — | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| common_neighbors | 0.8231 | 0.7300 | 0.9986 | 0.9876 | 0.9596 | 0.5132 | — | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| preferential_attachment | 0.8340 | 0.7266 | 1.0000 | 0.9975 | 0.9702 | 0.5209 | — | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| static_logistic_topology | 0.8513 | 0.7468 | 1.0000 | 0.9992 | 0.9750 | 0.5339 | 0.1948 | 12/12 | 12/12 | 5220 | 0 | 0 | 0.00 |
| arima | 0.9107 | 0.8409 | 1.0000 | 0.9967 | 0.9950 | 0.6760 | 0.1608 | 12/12 | 12/12 | 5220 | 0 | 853 | 13.12 |
| prophet | 0.8755 | 0.7805 | 1.0000 | 1.0000 | 0.9900 | 0.6282 | 0.1780 | 12/12 | 12/12 | 5220 | 0 | 853 | 145.90 |
| timestral_count_only | 0.8485 | 0.7492 | 0.9917 | 0.9867 | 0.9683 | 0.5702 | 0.2186 | 12/12 | 12/12 | 5220 | 0 | 0 | 27.82 |
| timestral_graph | 0.8281 | 0.6905 | 0.9833 | 0.9867 | 0.9633 | 0.5421 | 0.2193 | 12/12 | 12/12 | 5220 | 0 | 0 | 84.99 |

An em dash marks an undefined or unavailable value. Null reasons and query supports are recorded by origin in metrics_by_origin.csv.

![Average precision by origin](figures/performance_by_origin.svg)

## Paired average precision

| Origin | Model | Reference | AP | Reference AP | Difference | Sign |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-12-31 | timestral_graph | persistence_binary | 0.8110 | 0.7669 | 0.0440 | 1 |
| 2023-12-31 | timestral_graph | timestral_count_only | 0.8110 | 0.8388 | -0.0279 | -1 |
| 2024-01-30 | timestral_graph | persistence_binary | 0.8319 | 0.7698 | 0.0621 | 1 |
| 2024-01-30 | timestral_graph | timestral_count_only | 0.8319 | 0.8583 | -0.0264 | -1 |
| 2024-02-29 | timestral_graph | persistence_binary | 0.8575 | 0.8086 | 0.0489 | 1 |
| 2024-02-29 | timestral_graph | timestral_count_only | 0.8575 | 0.8815 | -0.0241 | -1 |
| 2024-03-30 | timestral_graph | persistence_binary | 0.8477 | 0.7579 | 0.0898 | 1 |
| 2024-03-30 | timestral_graph | timestral_count_only | 0.8477 | 0.8562 | -0.0086 | -1 |
| 2024-04-29 | timestral_graph | persistence_binary | 0.8348 | 0.7670 | 0.0678 | 1 |
| 2024-04-29 | timestral_graph | timestral_count_only | 0.8348 | 0.8660 | -0.0312 | -1 |
| 2024-05-29 | timestral_graph | persistence_binary | 0.8091 | 0.7312 | 0.0779 | 1 |
| 2024-05-29 | timestral_graph | timestral_count_only | 0.8091 | 0.8339 | -0.0247 | -1 |
| 2024-06-28 | timestral_graph | persistence_binary | 0.8204 | 0.7134 | 0.1070 | 1 |
| 2024-06-28 | timestral_graph | timestral_count_only | 0.8204 | 0.8326 | -0.0122 | -1 |
| 2024-07-28 | timestral_graph | persistence_binary | 0.8243 | 0.7754 | 0.0489 | 1 |
| 2024-07-28 | timestral_graph | timestral_count_only | 0.8243 | 0.8348 | -0.0106 | -1 |
| 2024-08-27 | timestral_graph | persistence_binary | 0.8154 | 0.7450 | 0.0704 | 1 |
| 2024-08-27 | timestral_graph | timestral_count_only | 0.8154 | 0.8531 | -0.0377 | -1 |
| 2024-09-26 | timestral_graph | persistence_binary | 0.8277 | 0.7967 | 0.0310 | 1 |
| 2024-09-26 | timestral_graph | timestral_count_only | 0.8277 | 0.8379 | -0.0102 | -1 |
| 2024-10-26 | timestral_graph | persistence_binary | 0.8307 | 0.7419 | 0.0887 | 1 |
| 2024-10-26 | timestral_graph | timestral_count_only | 0.8307 | 0.8500 | -0.0193 | -1 |
| 2024-11-25 | timestral_graph | persistence_binary | 0.8274 | 0.7548 | 0.0726 | 1 |
| 2024-11-25 | timestral_graph | timestral_count_only | 0.8274 | 0.8384 | -0.0110 | -1 |

![Graph versus count-only paired AP](figures/ablation_by_origin.svg)

## Prior activity strata

| Model | Stratum | Macro AP | Valid windows | Positives | Scored rows | Null reasons |
| --- | --- | --- | --- | --- | --- | --- |
| persistence_binary | active_last_30 | 0.7925 | 12 | 2643 | 3337 | — |
| persistence_binary | inactive_last_30 | 0.3737 | 12 | 707 | 1883 | — |
| recent_count30 | active_last_30 | 0.9306 | 12 | 2643 | 3337 | — |
| recent_count30 | inactive_last_30 | 0.3737 | 12 | 707 | 1883 | — |
| jaccard | active_last_30 | 0.8973 | 12 | 2643 | 3337 | — |
| jaccard | inactive_last_30 | 0.4861 | 12 | 707 | 1883 | — |
| common_neighbors | active_last_30 | 0.8975 | 12 | 2643 | 3337 | — |
| common_neighbors | inactive_last_30 | 0.4942 | 12 | 707 | 1883 | — |
| preferential_attachment | active_last_30 | 0.8941 | 12 | 2643 | 3337 | — |
| preferential_attachment | inactive_last_30 | 0.5059 | 12 | 707 | 1883 | — |
| static_logistic_topology | active_last_30 | 0.9110 | 12 | 2643 | 3337 | — |
| static_logistic_topology | inactive_last_30 | 0.5212 | 12 | 707 | 1883 | — |
| arima | active_last_30 | 0.9535 | 12 | 2643 | 3337 | — |
| arima | inactive_last_30 | 0.5740 | 12 | 707 | 1883 | — |
| prophet | active_last_30 | 0.9354 | 12 | 2643 | 3337 | — |
| prophet | inactive_last_30 | 0.4517 | 12 | 707 | 1883 | — |
| timestral_count_only | active_last_30 | 0.9030 | 12 | 2643 | 3337 | — |
| timestral_count_only | inactive_last_30 | 0.5302 | 12 | 707 | 1883 | — |
| timestral_graph | active_last_30 | 0.8940 | 12 | 2643 | 3337 | — |
| timestral_graph | inactive_last_30 | 0.5072 | 12 | 707 | 1883 | — |

![Reliability of scored link probabilities](figures/reliability.svg)

Fixed bins have width 0.1. Bin frequencies and observed link rates are in reliability.csv.

## Diagnostics and limitations

Repeated records can describe the same real-world incident. New recorded activity can include old events and repeat interactions. An inactive pair may have interacted before the last 30 days. The top-30 cohort favors well-observed countries.

Timestral was released in 2026, after the evaluation period. The study is retrospective and the extent of pretraining overlap is unknown. The numerical median forecast is a feature for supervised mapping. Empirical probability quality is assessed with Brier error and fixed reliability bins when probability outputs are available.

The 12 planned test windows share countries and news conditions. The paired differences are descriptive measures from those windows.

## Reproducibility

| Input identity | SHA-256 |
| --- | --- |
| config_sha256 | d1dba68f782e8f0cf883b1a6c951d8d6d4fb63940c9d81cfff8fb3a2751d2890 |
| data_sha256 | acc63e07ff1a75f9864964ce2e10c04851a72f8465c6e15a735b306585abff1a |
| country_registry_sha256 | adb6bd5cebd93f6d540a3949d5b29110d843d5cef857ccbfc1ee9d00a6d3a99b |
| cohort_sha256 | df70def4c173aef833a14ed1469e1ed457a96c42aacf96e4968b920b3cd58d2c |
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
| engineering_complete | True |
| demo_complete | True |
| research_complete | True |

```sh
cooperalink run --config config/research.json --input data/input --output outputs/research_top30_final
cooperalink resume --run-id outputs/research_top30_final
cooperalink report --run-id outputs/research_top30_final
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
