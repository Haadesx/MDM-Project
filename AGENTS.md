# Project instructions for coding agents

## Mission

Implement the attached research proposal completely under the definitions in this kit. Treat the user as the project owner. Make routine engineering choices and continue through the work plan without repeatedly requesting confirmation. Keep the original scientific scope and all mandatory comparators.

Read `README.md`, `docs/01_SPECIFICATION.md`, `docs/03_DATA_CONTRACT.md`, `docs/05_EXPERIMENT_PROTOCOL.md`, `docs/06_MODELS_AND_CALIBRATION.md`, `docs/07_TDD_GUIDE.md`, `docs/12_ACCEPTANCE.md`, and `config/research.json` before implementing scientific logic. Read other documents when taking their work package. Preserve original authorship from `references/original_proposal.pdf`.

## Resource policy and delegation

- Prefer Sol as orchestrator. If available through the current environment, prefer 6.1 Terra for scientific/data code and Luna for constrained boilerplate/reporting. Never invent or force unsupported model IDs or configuration keys.
- Maximum: one orchestrator plus two concurrent workers. Workers do not spawn additional workers. Use a worker only for an independent bounded task with named files, interfaces, tests, and acceptance criteria.
- Sol owns integration, shared contracts, final evaluation, and final claims. Expensive model escalation is a focused review of a concrete unresolved issue, not a default second implementation.
- Return compact handoffs: changed files, commands/results, assumptions, unresolved issues. Do not send whole logs or repeatedly reread the full repository.
- Prefer local cached data and weights. Do not use paid model APIs, create cloud resources, enable billing, publish a repository, submit coursework, or send messages on the user's behalf.
- The project's conservative default disables billable data queries and caps large downloads. If an external prerequisite is missing, finish every independent local task and leave a precise blocker with a ready command/configuration.

## Scientific invariants

1. Exact string event code `061`; actor-country affiliations, not event geography.
2. Undirected sorted pair; exclude same-country rows; count unique GDELT event IDs.
3. Use first-added UTC day for the main observational target. Do not backfill into the historical occurrence date.
4. Select the cohort from 2020 only and evaluate every candidate pair, including never-observed pairs. Do not sample negatives.
5. Missing source coverage is not zero activity. A window with missing required input cannot silently produce negatives.
6. Features use only information available by their cutoff. Forecasting code never receives future labels or future realized graph features.
7. Keep training, selection, calibration, and final evaluation separate. Freeze global mappings before the final year. Classical rolling-context fits remain allowed as specified.
8. Implement the exact 30-day binary persistence baseline and every comparator promised in the proposal.
9. Preserve tie-aware metrics, the defined MRR query population, undefined-metric reasons, and all candidate counts.
10. A real Timestral-209M run is required for scientific completion. Mocks, another model, or a synthetic dataset cannot satisfy that gate.
11. Report negative or inconclusive findings honestly. Never alter labels, candidates, data, or metrics to manufacture a win.

## TDD and change discipline

The starter contains intentionally unimplemented functions. First demonstrate relevant tests fail for the intended reason. Implement a small behavior, rerun its tests, then refactor. Keep pure transforms separate from I/O and model loading. Add meaningful adapter/integration tests before completing those layers; the delivered starter is not the entire future test suite.

Do not delete tests, mark them skipped/xfail, stub out a real backend in research mode, or weaken completion requirements to turn the suite green. An erroneous test may be corrected only with a written explanation and an independent expected result in the decision log. Do not require scientific metrics to exceed a target score.

Use a reproducible environment lock after verifying actual package compatibility. Record full model/source revisions and input hashes. Never fabricate dependency pins, data coverage, runtime estimates, source citations, or results.

## Files and recovery

- Use the module ownership in `docs/08_IMPLEMENTATION_PLAN.md`; workers must not overwrite each other's files.
- Keep `TASKS.md`, `PROGRESS.md`, and `DECISIONS_LOG.md` current. Update at each completed gate or material blocker, not after every trivial action.
- Make small local commits if working in a Git repository. Never overwrite unrelated user changes.
- Cache by inputs and configuration, checkpoint completed `(model, origin, batch)` units atomically, and resume only compatible runs.
- A time or resource cap pauses the remaining research work with a resumable state; it does not change the experiment or mark it complete.

## Completion response

Separate `engineering_complete`, `demo_complete`, and `research_complete`. Report tests actually run, real-data interval and candidate count, actual model backends/revisions, comparisons against persistence, artifact paths, and remaining blockers. If the environment prevents the real experiment, deliver the working system and exact resumable commands without claiming scientific completion.
