# Acceptance status

All three completion flags are true in `outputs/research_top30_final/completion.json`.

| Gate | Status | Evidence |
| --- | --- | --- |
| A Software and contracts | Complete | 78 tests and 11 subtests passed. The locked environment was verified with Python 3.12 on Apple silicon macOS. Core modules import without heavy backends. |
| B GDELT and cohort | Complete | The official 2020–2024 extract has 1,846,939 rows across all 1,827 UTC days. Local validation accepted 644,342 distinct events. The frozen 2020 cohort has 30 countries and 435 pairs. |
| C Models | Complete | Genuine Timestral-209M count-only and graph forecasts ran on CPU in float32. Real ARIMA and Prophet smoke checks passed. All four forecast mappers fit on all 5,220 rows in 2023. The same-model ARIMA optimizer retry converged on four calibration and six test rows. |
| D Evaluation | Complete | All ten models scored 435 pairs in each of twelve held-out 2024 windows. The final table has 52,200 real prediction rows. Independent calculations reconciled per-window AP, tie-aware precision, filtered MRR, supports and the rendered results tables. |
| E Reproducibility | Complete | Both demos and the final research run passed resume checks with identical prediction hashes. The final manifest, frozen mappers, metric exports and reports are in `outputs/research_top30_final/`. |

The first real attempt recorded four nonconvergent ARIMA calibration fits. Its checkpoints and report remain in `outputs/research_top30/`. The successful rerun used the same study configuration and a tested retry of the same state-space likelihood.

The official GDELT 2.0 query used a BigQuery Sandbox project with no linked billing account. Its estimated and actual processed data were both displayed as 29.04 GB. The complete local CSV matched the job's result count. The manifest in `data/input/source.json` records the exact query, completed job ID, UTC bounds and checksum. The coverage certificates attest to extraction from the queried source table.

The research results are in [the HTML report](outputs/research_top30_final/report.html) and [the Markdown report](outputs/research_top30_final/report.md). The engineering receipt is `outputs/verification/quality.json`, the test log is `outputs/verification/pytest.log`, and the completed model smoke evidence is `outputs/verification/models-smoke.json`. The independent research check is `outputs/verification/research-final-check.json`.

```bash
uv run --no-sync cooperalink resume --run-id research_top30_final
```
