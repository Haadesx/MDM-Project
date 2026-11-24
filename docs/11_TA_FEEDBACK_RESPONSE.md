# Proposed clarification responding to TA feedback

Status: ready-to-adapt proposal addendum. This is a recommended design clarification, not a statement that the TA has reviewed or approved it. It supplements the original proposal in [`references/original_proposal.pdf`](../references/original_proposal.pdf). The executable implementation must follow the more detailed [experiment protocol](05_EXPERIMENT_PROTOCOL.md).

## Suggested addendum

**Prediction target and definition of a link.** We define an economic-cooperation link as the occurrence of at least one eligible GDELT Event Database record with exact CAMEO code `061` for a pair of countries during the next 30 days. We use `Actor1CountryCode` and `Actor2CountryCode` to identify the countries. We model the pair as unordered because the research question concerns economic exchange between countries; actor roles remain available for audit. We exclude same-country records, missing affiliations, and identifiers outside a versioned country-code allowlist. Distinct `GLOBALEVENTID` values are counted once each.

We index observations by the UTC day of `DATEADDED`, the time the record entered GDELT, and retain the occurrence date for audit. Thus the task predicts newly recorded cooperation, including recurring activity; it does not claim to identify the first real-world formation of an economic relationship. At cutoff day `T`, the target is 1 if one or more eligible records appear from `T+1` through `T+30`, inclusive.

**Candidate country pairs.** To make the full comparison feasible, we select the 30 countries with the highest eligible event incidence during 2020, break ties by country code, and freeze that roster before evaluation. Every origin includes all 435 distinct unordered country pairs from this roster, whether or not the pair has appeared previously. We do not choose countries or candidate pairs using later activity. This defines a study of a fixed, active-country cohort rather than a claim of coverage of every country.

**Handling of negatives.** A candidate pair is labeled 0 when no eligible record appears in its complete next-30-day target window. These are observed non-events in GDELT, not evidence that cooperation was impossible or absent in the world. We retain all positive and negative pairs; we do not sample evaluation negatives. Missing extraction coverage is treated as missing information, not zero activity. The report will include class prevalence and coverage for every evaluation window.

**Persistence baseline.** We include the required last-30-day persistence baseline. It scores a pair 1 if it has at least one eligible record from `T-29` through `T`, inclusive, and 0 otherwise. It uses exactly the same candidates, future targets, and evaluation windows as every other model. Precision@K and MRR will use explicit tie handling because the binary persistence score produces many ties.

**Temporal evaluation and calibration.** We use 2020 to define the roster and provide warm-up history, 2021 for fitting, 2022 for model selection, 2023 for fitting the forecast-to-link probability mappings, and 2024 for final evaluation. Each year contains 12 non-overlapping 30-day target blocks anchored on January 1; the five- or six-day year-end remainder is disclosed and omitted as a target block. Features at each origin use only observations available by that cutoff. Global learned models and calibration layers are frozen before the 2024 test; ARIMA and Prophet may fit local series parameters to their designated rolling history at each origin under fixed configurations.

We retain the proposed Jaccard, common-neighbor, ARIMA, Prophet, and static-logistic baselines, alongside persistence. We retain ROC-AUC, Precision@K, and MRR, and add average precision as the primary comparison measure for the full candidate panel. We will report per-window and macro results, the number of windows on which each metric is defined, and model failures or fallbacks. We will also distinguish pairs active in the previous 30 days from inactive pairs as a diagnostic, without redefining the primary task.

## Additional implementation clarifications

The numerical context is exactly 90 daily rows. Each day's topology comes from a simple graph of the previous 30 days, inclusive of that day, so 119 days of raw history are required at a forecast origin. This trailing-window graph is an explicit refinement of the proposal's daily-snapshot description.

The Timestral checkpoint, its documented input interface, and its availability must be verified before claiming a completed Timestral experiment. A numerical forecasting backbone may be zero-shot while its logistic link-probability mapping is supervised. Because the cited model is newer than the historical evaluation period, the final paper must describe a retrospective evaluation and disclose any unknown pretraining overlap.

No requirement assumes that Timestral will outperform persistence. A fair, reproducible result showing no improvement still answers the research question.

## Feedback traceability

| TA concern | Concrete resolution | Evidence in final report |
| --- | --- | --- |
| Definition of a link is missing | At least one exact-061 record for an unordered pair in the next 30 recorded days | Target equation, date boundaries, event filters |
| Candidate country pairs are missing | Fixed top-30 cohort from 2020; all 435 unordered pairs at every origin | Frozen roster, selection counts, candidate-count checks |
| Handling of negatives is missing | Complete candidate panel; zero eligible future records means an observational negative; no negative sampling | Prevalence by origin, coverage audit, complete prediction tables |
| Persistence baseline must be included | Binary indicator of any record in the prior 30 days | Named baseline row, tests of window boundaries, paired test-window comparisons |

## Source notes

The data-field interpretation follows the [GDELT 2.0 event codebook](https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf). The relation interpretation follows code 061 in the [CAMEO v1.1b3 codebook](https://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf), printed page 34 / PDF page 40. The cohort size, temporal split, graph width, and metric conventions are proposed project decisions, not claims that those choices were specified by GDELT or already approved by the TA.
