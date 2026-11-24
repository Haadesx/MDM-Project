# 08. Implementation plan and delegation

## Operating rule

Keep one orchestrator responsible for contracts, integration, and conclusions. Prefer Sol for that role. Use up to two independent workers, preferably Terra for substantive data/model code and Luna for constrained support work. Do not spawn a second team for the same modules. Model selectors are environment-dependent; record an available fallback instead of failing the project because a preferred model name is unavailable.

Each worker receives one bounded task: owning files, read-only dependencies, public interfaces, tests to make pass, and a concise return format. The orchestrator integrates sequentially at dependency boundaries. A worker must not alter the locked scientific configuration to make its task easier.

## Work packages

| ID | Work and ownership | Dependencies | Gate |
| --- | --- | --- | --- |
| W00 | Orchestrator: repository inspection, environment, plan/status files, actual dependency lock | None | Starter tests collect; red reason verified; input/model availability recorded |
| W01 | Terra: ingestion, source readers, country registry, coverage and cohort | W00 | Cleaning/universe tests green; real-data import path documented |
| W02 | Terra: calendars, daily panels, graph and feature assembly | W01 | Boundary/graph tests green; 119-day support and leakage guard proved |
| W03 | Sol or second worker: ranking metrics and direct baselines | W00 shared domain types | Golden metrics green; exact persistence included |
| W04 | Orchestrator: offline pipeline and synthetic generator; Luna: artifact/report skeleton after interfaces freeze | W02,W03 | Offline demo with six candidates and synthetic banner |
| W05 | Terra: Timestral adapter, genuine smoke and classical adapters | W02, dependency lock | Shape tests and genuine backend smoke results recorded |
| W06 | Sol: topology logistic selection and forecast mappings | W03,W05 | Fit-role isolation tests; serialized fitted-artifact provenance |
| W07 | Sol: source preparation and fixed scientific inputs | W01,W02 | Full source coverage, registry, 30-country roster, all folds validated |
| W08 | Sol: calibration and untouched final evaluation | W06,W07 | Required predictions/metrics complete on all final origins |
| W09 | Luna: report/figures/README from immutable outputs; Sol reviews conclusions | W04,W08 | Report values reconcile; limitations and TA response included |
| W10 | Sol: final acceptance, reproducibility run/resume check, handoff | All independent completed work | Engineering/demo/research statuses explicit |

W01/W03 are the first useful parallel split. W05 and report scaffolding can be parallel after features and artifact contracts stabilize. Do not ask two workers to edit `domain.py`, `config/research.json`, the same shared schemas, or pipeline orchestration simultaneously. The orchestrator owns those changes.

If W07 is blocked by data access, complete W00–W06, the synthetic versions of W09/W10, all source adapters, and the exact resume instructions. Do not substitute synthetic scores into W08. If model weights are blocked, continue baseline and reporting implementation while keeping the genuine inference gate unmet.

## Handoff template for a worker

```text
Task: Wxx and concrete outcome
Owned paths: ...
Read-only dependencies: ...
Contract: scientific definitions and function/schema versions
Acceptance: named tests plus one interface example
Limits: no shared-config edits, no further delegates, no external spending
Return: changed files; commands and actual results; assumptions; blockers
```

## Definition of a completed vertical slice

Before expensive downloads or full model evaluation, one command should process the hand fixture, produce the complete six-pair panel, calculate historical features and future labels, score persistence/topology, compute the known metric example, and render a clearly synthetic report. This establishes that the plumbing and semantics work together. It is not the real experiment.

Next, add a deterministic multi-year synthetic generator for fitting/mapping integration. Make it small enough for ordinary development, with complete coverage metadata and enough variation for both outcome classes. Keep generated data visibly synthetic in every artifact.

## Durable work state

Create these working documents during W00:

- `TASKS.md`: one row per W00–W10 package with dependencies, owner, state, and evidence path.
- `PROGRESS.md`: latest successful gate, running/resumable command, pending independent tasks, and actual blockers.
- `DECISIONS_LOG.md`: configuration-neutral implementation decisions and any carefully justified scientific amendments.

For runtime state use machine-readable task/checkpoint files, not prose parsing. Save the next `(model, origin, pair batch)` and immutable run identity. Do not depend on an agent remembering state after its context or process restarts.

## Cost controls that preserve the study

Reuse data and weight caches. Initialize Timestral once. Compute each graph snapshot once, reuse it across pairs, and batch tensor inference. Run classical fits with bounded workers. The main forecast workloads only require 2023 mapping contexts and 2024 final contexts; do not generate expensive forecasts for every day of five years.

Do not launch hyperparameter sweeps beyond the specified three C values for the topology classifier. Do not fine-tune the foundation model or download alternative families. Use stronger-model consultation only for a precise unresolved scientific or integration issue, with the evidence already collected.

Local computation may continue to completion with checkpoints. If the owner sets a time cap, preserve progress and report an incomplete run at the cap. A cap does not authorize changing the candidate universe or dropping Prophet.

## Expected final response from the implementation agent

Lead with what actually works. State the three completion flags and provide real commands and output paths. Summarize actual tests, candidate/data coverage, model versions, per-window comparisons against persistence, and any remaining limitations. Include the simplest full rerun/resume command. Do not declare success from a green mock test alone.
