# Source-query template

`extract_061.sql` is a GoogleSQL starting point, not an executed or cost-verified query. It deliberately keeps event IDs and raw actor order so the local validator can detect duplicate/conflicting identities.

1. Inspect the current official Events table schema and partition metadata using an authorized source client.
2. Confirm `EventCode` is textual, DATEADDED representation, and required column names. Preserve leading zeroes. The exported ID alias matches the starter's `GlobalEventID` key.
3. Set explicit UTC start/end parameters. For the complete study the conceptual interval is `[20200101000000, 20250101000000)`, but execute bounded chunks only after estimating scan cost.
4. Prefer a verified partitioned table/pruning predicate when available. Derive partition bounds from its actual semantics. Never assume `_PARTITIONTIME`, SQLDATE, and DATEADDED are interchangeable, and never narrow a partition range in a way that can omit eligible recorded-time rows.
5. Dry-run the rendered query, retain estimated bytes, and honor the existing user-approved maximum-byte budget. A filtered code or LIMIT does not guarantee a cheap scan. Default execution is disabled.
6. Export every result page, retain the job/query/snapshot/interval metadata, and certify complete extraction for each day only after the whole interval succeeds. A query yielding zero eligible rows can certify a zero relative to the source table; an interrupted export cannot.
7. Normalize/filter countries and deduplicate locally under the supplied contract. Do not use SQL row-number deduplication that silently hides conflicting IDs.

The 2020 extraction must include the whole valid actor-country population before top-30 selection. Later extraction can use a documented frozen-cohort filter, but it must preserve every eligible pair in that cohort. Such a filter may reduce result size without reducing scanned bytes.
