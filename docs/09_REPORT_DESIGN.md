# 09. Report and output design

## Audience and format

Produce a course-project research report that a TA can inspect without reading code. Use the original title/authors, a neutral course-project heading, explicit date, and a visible run ID. Do not repeat the proposal's unrelated conference-template footer. Create `report.md` and a standalone `report.html` from the same immutable result objects, with PNG/SVG figures. PDF export is useful but optional for the implemented project.

Keep the design simple: white background, dark text, one blue for Timestral, neutral gray for simple baselines, and a distinct amber accent for incomplete or synthetic status. Use labels and patterns in addition to color. Tables should include denominators, units, year roles, and missing-value explanations. Reports should work offline; avoid external fonts/scripts or a live server.

The synthetic report must display `SYNTHETIC SOFTWARE DEMONSTRATION - NOT RESEARCH RESULTS` near the title and every exported metrics sheet. The final real report must identify the source interval, top-30 cohort, all-pairs candidate count, and extraction-coverage meaning.

## Required report sections

1. **Abstract and answer to the research question.** State the actual outcome versus persistence, with uncertainty and scope. Write this after evaluation, using measured results only.
2. **Problem definition.** Explain the observed 30-day link, undirected pairs, country roster, negatives, event date convention, and what is not being inferred about the real world.
3. **Data and coverage.** Show source/provenance, filtering and duplicate counts, cohort, date range, source gaps, and event/prevalence distribution.
4. **Method.** Describe daily counts, trailing graph features, 90-row inputs, Timestral past covariates, and the separate 2023 forecast-to-probability mapping.
5. **Protocol.** Show the 2020–2024 role timeline, exact 30-day windows, frozen global artifacts, allowed rolling ARIMA/Prophet fitting, and missing-data policy.
6. **Baselines and metrics.** Include every required model, genuine model provenance, constant-series shortcut usage, tie rules, and the MRR query/filter definition.
7. **Results.** Primary comparison table, per-window comparison against persistence, count-only ablation, and conditional active/inactive results.
8. **Diagnostics and limitations.** Probability quality, extraction noise, selection bias, training-overlap uncertainty, sparse counts, and the small number of evaluation windows.
9. **Reproducibility.** Exact commands, environment/model/data/config hashes, hardware, actual runtimes, completed gates and unresolved issues.
10. **References and TA-response mapping.** Cite primary data/model documentation and connect each TA comment to an implemented definition and test.

## Main comparison table

One row per canonical model ID, in a consistent order. Columns:

```text
model, macro_AP, macro_ROC_AUC, P_at_10, P_at_25, P_at_50,
filtered_MRR, valid_AP_windows, valid_AUC_windows,
candidate_rows, failed_rows, constant_shortcut_rows, runtime_seconds
```

Keep the binary persistence row plainly visible. Show undefined values as an em dash with an explicit reason/support note, never as zero. Do not rank a model with missing candidate rows alongside complete models without a clear incomplete status. Save the corresponding CSV and full machine-readable per-window records.

Add a paired comparison table with each window's `AP(timestral_graph) - AP(persistence_binary)`, sign, and the underlying two scores. A mean difference without its per-window variation is insufficient evidence. Do not claim significance from treating dyad rows as independent samples.

## Figures that earn their space

- **Timeline:** one row per year showing roster/fit/selection/mapping/test roles; label the omitted final five/six days.
- **Observed activity:** eligible record counts and positive-pair prevalence over time, using a common time axis and source-coverage markers.
- **Performance by origin:** AP for main Timestral, count-only Timestral, persistence, and the strongest prespecified/simple competitor. Other models remain in the table.
- **Ablation comparison:** paired main-versus-count-only window values with a reference line, not a cherry-picked average.
- **Probability diagnostic:** a reliability table/plot and Brier score for genuine probability outputs. Use fixed bins, show sample counts, and avoid pretending raw graph scores are probabilities.
- **Optional illustrative graph:** one predetermined historical graph from the cohort. Label it as an illustration; do not use a decorative network as evidence of predictive quality.

Export figures with axis names, units, readable text, run ID metadata, and descriptive filenames. Use vector exports when useful for the final paper. Do not generate quantitative figures with an image-generation model.

## Interpretation guardrails

A positive outcome is at least one observed `061` record, not the formation of a brand-new alliance or the start of a first-ever trade relationship. Pairs inactive for 30 days may have interacted earlier. State this in the conditional-slice analysis.

The top-30 cohort favors well-observed countries. Do not extrapolate its results to every country. The candidate panel includes all pairs in that cohort, but source observation remains incomplete in the real world.

The main graph-covariate model's 90 feature rows use up to 119 raw days because of the graph aggregation. The count-only ablation uses 90 count days. It tests the configured enriched pipeline, not an isolated causal effect of topology holding every aspect of information access constant. A 119-day count-only control is optional and must be separately named; it cannot replace the main proposal-aligned 90-day setting.

Timestral's median outputs are forecast features, not guaranteed event-count expectations. The logistic map produces predicted probabilities, but empirical probability calibration must be evaluated rather than assumed from its name. The model was released after the historical evaluation period; record the retrospective nature and unresolved training-data overlap.

If Timestral loses, report which simpler models win and what this suggests about sparse recorded-event prediction. Do not rewrite the target or change cohort selection after seeing the result.

## Report verification

Generate tables from exported metric objects, not manually copied values. Verify totals against prediction rows, compare report numbers with CSV, inspect figures and the HTML/PDF rendering, and check that all mandatory models and TA points appear. In an incomplete run, print the blocker and absent evidence instead of fabricating a finished abstract.
