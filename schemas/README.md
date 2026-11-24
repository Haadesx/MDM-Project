# Persisted artifact schemas

Schemas use JSON Schema draft 2020-12. They establish row/run shape, required provenance, supported statuses, nullable metric semantics, and the fixed study's completion flags. Validate individual JSON rows directly; validate matching Parquet columns/types and then apply the same semantic checks to the table.

JSON schemas do not prove temporal causality, finite-number serialization, country ordering, equality of candidate panels, exact required model inventory, learned-parameter provenance, or artifact correctness. Implement those as explicit cross-row/run acceptance validators and tests. Use strict JSON serialization with NaN/Infinity disabled. A schema-valid fake result is not a research result.

`completion.schema.json` intentionally describes the registered top30/12-test-window study. Optional expansions need an explicit new profile/schema version. A raw prediction table contains no future label; evaluation joins the separate labels table after scores are persisted.
