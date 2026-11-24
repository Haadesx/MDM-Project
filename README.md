# Cooperalink: Codex implementation kit

**Forecasting International Economic Cooperation Links in Temporal Event Networks Using GDELT and Timestral**

Prepared for the attached Rutgers proposal and the TA's November 11 feedback. Version 1.0, November 20, 2026. `Cooperalink` is a working repository name; retain the proposal's title and authors in the academic report.

## Implementation status

The project includes a local forecasting pipeline, a locked environment, verified model adapters, and two offline demonstrations. The fixed GDELT experiment requires a certified local GDELT 2.0 Events export covering 2020–2024. See [PROGRESS.md](PROGRESS.md) for the executed checks and completed research run.

Open the [full interactive research report](outputs/research_top30_presentation/report.html) in a browser. Its Plotly figures are embedded in the HTML. Rebuild the presentation from the accepted run with:

```bash
uv run --no-project --with plotly==7.1.0 -- python scripts/render_research_report.py
```

For a readable ten-page overview, open [`cooperalink_blueprint.pdf`](cooperalink_blueprint.pdf). The detailed documents and machine-readable configuration below govern implementation.

The research question is: **within a fixed cohort of countries, which unordered pairs will have at least one newly recorded GDELT economic-cooperation event during the next 30 days?** The package preserves GDELT 2.0, exact CAMEO `061`, 2020–2024, 90-day model inputs, Timestral-209M, graph features, logistic mapping, the proposed baselines, and non-overlapping 30-day evaluations. It resolves the TA's missing definitions and adds the required persistence baseline.

## Team review

- [Final PDF report](output/pdf/cooperalink-research-report.pdf)
- [Full interactive HTML report](outputs/research_top30_presentation/report.html?raw=true). Download and open it locally to use the charts offline.
- [Final metrics summary](outputs/research_top30_final/metrics_summary.csv) and [paired comparisons](outputs/research_top30_final/paired_comparisons.csv)
- [Run manifest](outputs/research_top30_final/run_manifest.json) and [independent verification](outputs/verification/research-final-check.json)
- [Certified data export and coverage records](data/input/)

The source is the [GDELT Project](https://www.gdeltproject.org/), GDELT 2.0 Events. The bundled 2020–2024 CSV is the exact CAMEO 061 query result, with its checksum and receipt recorded in [source.json](data/input/source.json). [GDELT redistribution terms](https://www.gdeltproject.org/about.html)

The proposal in `references/` is the public copy with author contact addresses removed. The final research report retains the authorship and references.

## Setup and offline demonstrations

These commands were verified with Python 3.12 on Apple silicon macOS. Other platforms, including CUDA, are untested.

```bash
uv sync --locked --python 3.12 --extra test
uv run --no-sync cooperalink demo --config config/demo.json --output outputs/demo_local
uv run --no-sync cooperalink demo --config config/demo.json --multiyear --output outputs/demo_multiyear_local
uv run --no-sync python scripts/smoke_models.py
uv run --no-sync python -m pytest -q
```

The one-origin demo exercises the hand fixture on six pairs. The multi-year demo exercises time-isolated topology fitting and an explicitly synthetic forecast mapper. Their reports are `outputs/demo/report.html` and `outputs/demo_multiyear/report.html`. The genuine smoke command uses the cached, pinned checkpoint on small inputs.

## Run the fixed experiment

The certified export, coverage records, and official CAMEO lookup are included. For a new run, populate the pinned Timestral checkpoint from the [runbook](docs/10_RUNBOOK.md#model-and-hardware-prerequisites) and use a fresh output directory.

```bash
uv run --no-sync cooperalink doctor --config config/research.json
uv run --no-sync cooperalink validate-input --input data/input --config config/research.json
uv run --no-sync cooperalink run --config config/research.json --input data/input --output outputs/research_top30_rerun
uv run --no-sync cooperalink resume --run-id research_top30_rerun
uv run --no-sync cooperalink report --run-id research_top30_rerun
```

The run directory records completion, provenance, reports, and forecast checkpoints. Use the same directory to resume compatible work after interruption. Use a separate output directory for changed inputs or code. The BigQuery adapter uses existing access for dry runs only.

## Read order and ownership of decisions

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Working rules, autonomy, worker budget, scientific invariants |
| `CODEX_PROMPT.md` | One-paste implementation mission |
| `docs/01_SPECIFICATION.md` | Product/research specification and requirement IDs |
| `docs/02_ARCHITECTURE.md` | Modules, interfaces, storage, execution boundaries |
| `docs/03_DATA_CONTRACT.md` | GDELT extraction, cleaning, coverage, schemas |
| `docs/04_DECISIONS.md` | Explicit architecture and methodology decisions |
| `docs/05_EXPERIMENT_PROTOCOL.md` | Splits, candidates, negatives, metrics, leakage rules |
| `docs/06_MODELS_AND_CALIBRATION.md` | Exact forecast adapters, baselines, mapping rules |
| `docs/07_TDD_GUIDE.md` | Red/green workflow, test layers, missing integration tests |
| `docs/08_IMPLEMENTATION_PLAN.md` | Ordered work packages and worker ownership |
| `docs/09_REPORT_DESIGN.md` | Report layout, figures, scientific claims |
| `docs/10_RUNBOOK.md` | Target CLI, environments, data access, recovery, budgets |
| `docs/11_TA_FEEDBACK_RESPONSE.md` | Proposed clarification addressing each TA comment |
| `docs/12_ACCEPTANCE.md` | Engineering and scientific completion gates |
| `docs/13_SOURCES.md` | Primary sources, verified facts, limits of this package |
| `config/research.json` | Locked research defaults; not measured results |
| `config/demo.json` | Explicitly synthetic development profile |
| `schemas/` | Persisted output contracts |
| `sql/` | Bounded extraction templates; not executed here |
| `src/`, `tests/`, `fixtures/` | Implementation, contract and integration tests, and synthetic fixtures |
| `references/` | Original proposal and verbatim supplied TA feedback |

The written scientific specification and `config/research.json` must agree. Tests encode selected invariants; they are not permission to ignore the rest of the specification. When a genuine contradiction is found, record a decision and change the conflicting artifacts together. Do not weaken tests to hide broken behavior.

## Verification evidence

Use `uv run --no-sync python -m pytest -q` for the software suite. The original kit's checksums and red-phase evidence in [KIT_VALIDATION.md](KIT_VALIDATION.md) document the handoff. Current logs and the verification receipt are under `outputs/verification/`.

## Locked main design

| Decision | Main experiment |
| --- | --- |
| Observation | A distinct GDELT event record with exact code `061` |
| Time index | UTC day of `DATEADDED`; retain `SQLDATE` for audit |
| Link | At least one record for the unordered pair during days `T+1` through `T+30` |
| Countries | Top 30 valid country affiliations by 2020 eligible-record incidence |
| Candidates | All 435 unordered pairs at every evaluated origin |
| Negatives | No observed qualifying record in a complete future window; no sampling |
| History | Exactly 90 daily target/covariate rows, ending on `T` |
| Graph | Trailing 30-day graph updated daily; 119 raw days support 90 feature rows |
| Years | 2020 roster; 2021 fit; 2022 selection; 2023 mapping; 2024 final test |
| Mandatory simple comparator | Binary interaction persistence over `T-29` through `T` |
| Evaluation | ROC-AUC, AP, tie-aware P@10/25/50, explicitly defined filtered MRR |

The 30-country cohort is a deliberate resource-limited study, not a claim of worldwide coverage. An all-country expansion is optional and must retain all required baselines. Model superiority is a research question, not an acceptance criterion.
