# Implementation work packages

| Work | Depends on | Owner | State and evidence |
| --- | --- | --- | --- |
| W00 Environment and red baseline | — | Orchestrator | Local Python 3.12 lock and starter failure log |
| W01 Ingestion, coverage and registry | W00 | Orchestrator | Typed local imports, official lookup and classification, data-pipeline tests |
| W02 Causal features | W01 | Orchestrator | Daily counts and graph snapshots, 119-day support and future-injection tests |
| W03 Baselines and metrics | W00 | Evaluation worker | Golden metric fixtures and full-panel contract tests |
| W04 Offline demo | W02, W03 | Orchestrator | Six-pair fixture and multi-year synthetic pipeline |
| W05 Model adapters | W02 | Terra | Genuine cached Timestral-209M, ARIMA and Prophet smoke evidence |
| W06 Fitting and mappers | W03, W05 | Terra and orchestrator | Frozen scaler/classifier parameters and role-isolated CLI fitting |
| W07 Fixed GDELT input | W01, W02 | Orchestrator | Complete. Certified BigQuery export, 1,827 covered UTC days, 30 countries and 435 pairs |
| W08 2024 evaluation | W06, W07 | Orchestrator | Complete. Four fitted 2023 mappers and 52,200 held-out scores |
| W09 Report and figures | W04, W08 | Evaluation worker | Complete. Demo and research reports reconcile with immutable metric exports |
| W10 Acceptance and recovery | W00–W09 | Orchestrator | Complete. Research, demo and engineering flags true. Final resume retained the prediction checksum |
