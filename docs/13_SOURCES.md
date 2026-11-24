# 13. Sources, provenance, and verified limits

Sources below were inspected on **November 20, 2026**. URLs that contain `main` or `stable` are documentation references, not immutable experiment revisions. The implementation must resolve actual source/checkpoint/package versions and retain their hashes.

## User-provided sources

- `references/original_proposal.pdf`: two-page proposal, *Forecasting International Economic Cooperation Links in Temporal Event Networks Using GDELT and Timestral*, by Urvi Desai, Sinchana Arun, and Varesh Patel. Supplied by the user in this conversation.
- `references/ta_feedback.md`: exact feedback supplied by the user, marked November 11 at 3:21pm. No year or course deadline is inferred from that timestamp.

## Primary technical sources

| Source | URL | What it supports |
| --- | --- | --- |
| GDELT Event Codebook v2.0 | https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf | Record fields, IDs, actor affiliations, timestamp semantics, raw-file conventions |
| CAMEO Manual 1.1b3 | https://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf | Meaning of 061 and actor/event coding context |
| GDELT data/documentation index | https://gdeltproject.org/data.html | Official lookup links and data access routes; actor-country versus Geo code distinction |
| GDELT partitioned-table announcement | https://blog.gdeltproject.org/announcing-partitioned-gdelt-bigquery-tables/ | Existence and rationale of partitioned public tables; actual current schema still requires inspection |
| Google BigQuery cost controls | https://docs.cloud.google.com/bigquery/docs/best-practices-costs | Dry runs, scan estimation and maximum-byte controls |
| Timestral-209M model card | https://huggingface.co/mistralai/Timestral-209M | Checkpoint identity, numerical inputs/covariates, forecasting capabilities |
| Official Timestral code | https://github.com/mistralai/timestral | Supported package/repository, examples and code license |
| Timestral forecast interface | https://raw.githubusercontent.com/mistralai/timestral/main/src/timestral/forecaster.py | Input/output axes, median access, clipping/inference flags |
| Timestral checkpoint loader | https://raw.githubusercontent.com/mistralai/timestral/main/src/timestral/loading.py | Revision/cache loading and precision contract |
| Timestral release | https://mistral.ai/news/timestral/ | October 2026 release and published training description |
| Timestral weight license | https://huggingface.co/mistralai/Timestral-209M/blob/main/LICENSE | Weight-specific terms, distinct from code license |
| Statsmodels ARIMA | https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html | Official classical-model interface |
| Prophet quick start | https://meta.github.io/prophet/docs/quick_start.html | Official ds/y input and fit/predict workflow |
| Scikit-learn LogisticRegression | https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html | Current regularization/constructor semantics |
| Scikit-learn average precision | https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html | Step-wise AP definition, distinct from trapezoidal PR area |

## What was and was not verified for this kit

The proposal was extracted and visually inspected. The Timestral reference is real and its official interface supports the proposed context/horizon and past covariates. Core data semantics were checked against official documentation. Synthetic calendar/metric examples were independently reviewed. The delivered test suite was run to verify its intentional red state and absence of accidental import/syntax errors.

No five-year GDELT extraction, BigQuery scan/cost benchmark, genuine Timestral inference, model fitting, or real predictive experiment was performed while creating this specification. The kit does not contain measured scientific results, downloaded model weights, a verified final country roster, or a solved dependency lock for the future implementation. Those outputs require executing the project against actual inputs.

The linked official CAMEO country lookup could not be fetched by the research tool during authoring. Its official location is discoverable from the GDELT data page, but its bytes and a final allowlist are not invented here. Registry acquisition/classification is an explicit first data task. Model source/checkpoint full revisions similarly must be resolved during installation rather than fabricated.

## Research interpretation and reuse

The target/time/country/split/baseline choices are this kit's recommended design decisions, not claims made by GDELT or Mistral and not evidence of TA approval. Factual API descriptions should be rechecked against the exact locked revisions during implementation.

The official model code and model weights use different licenses; keep source links and downloaded license files with runtime provenance, and do not redistribute weights in the course handoff by default. The original proposal remains the users' document. This kit makes no claim that the proposal's conference-style template denotes publication.

Academic authors should understand and be able to explain the definitions, tests, and results. Record external-source and AI assistance as required by the actual course policy; no particular undisclosed course rule is assumed here.
