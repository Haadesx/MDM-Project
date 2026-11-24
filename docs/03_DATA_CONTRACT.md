# 03. Data acquisition, cleaning, and storage contract

## Scope and verified source semantics

Use the **GDELT 2.0 Event Database**, not the news-search API, GKG, GDELT 1.0, or the EventMentions table. The official GDELT 2.0 codebook defines actor affiliations, unique event IDs, occurrence dates, and the UTC `DATEADDED` timestamp. The CAMEO manual defines `061` as economic cooperation. These facts are sourced in `docs/13_SOURCES.md`; the operational filtering and coverage policies below are project decisions.

The full source interval is `2020-01-01T00:00:00Z <= DATEADDED < 2025-01-01T00:00:00Z`. Use local cached extracts first. The delivered kit contains only synthetic fixtures, not this real dataset.

## Raw columns

| Field | Required representation | Use |
| --- | --- | --- |
| `GLOBALEVENTID` | Integer or digit string, normalized to a canonical decimal string | Record identity and deduplication |
| `SQLDATE` | Exactly eight digits `YYYYMMDD`, parsed as a real calendar date | Occurrence-date audit only |
| `DATEADDED` | Exactly fourteen digits `YYYYMMDDHHMMSS`, strict UTC timestamp | Primary observation time |
| `Actor1CountryCode` | String preserving the source affiliation code | Endpoint before canonicalization |
| `Actor2CountryCode` | Same | Endpoint before canonicalization |
| `EventCode` | **String**, exact `061` after trimming surrounding whitespace | Relation filter |

Column names in raw export formats may differ in case. A source adapter may use a documented, unambiguous rename map; it must not guess between `Actor1CountryCode` and `Actor1Geo_CountryCode`. The starter accepts `GlobalEventID`; official exports/queries commonly use `GLOBALEVENTID`. Normalize this declared alias at the adapter boundary (or accept both), and reject conflicting simultaneous values. Keep raw actor order in an audit table if the canonical Event record stores only sorted endpoints. `SOURCEURL` is optional audit metadata; its contents are not fetched or used as features. Mention/article/source counts and `AvgTone` are not primary features or weights.

Read tab-delimited GDELT raw files using the official 2.0 field order and explicit types. Their `.CSV` suffix does not imply comma separation. For a user-exported CSV, require its declared delimiter and header/schema. Parquet should retain `EventCode` as a string. If a supplied export has already converted `061` to numeric `61`, reject the broken schema and request/recreate an explicitly typed export; do not apply zero-padding that could alter other CAMEO codes.

## Cleaning order and rejection semantics

1. Validate source schema and raw event-code type. Select exact `061`; other valid strings are counted as excluded relation rows.
2. Read actor affiliations. Exclude blank affiliations, unrecognized/disallowed country entries, and same-country pairs; count each reason.
3. Strictly parse required timestamps and event IDs for remaining eligible rows. A malformed eligible row is a `DataContractError`, not a silent omission. Keep a diagnostic file with counts and a small safe sample of row IDs.
4. Canonicalize the pair by sorting accepted country codes. The raw direction remains available for audit.
5. Deduplicate by event ID. Repeated copies with the same immutable normalized identity become one record. If the same ID has conflicting pair, `SQLDATE`, or `DATEADDED`, fail the data-validation gate. Differences only in unused mutable mention metadata are not conflicts in this normalized identity.
6. Verify the declared extraction interval and coverage before daily aggregation.

Different IDs describing the same real-world incident remain different records. Different actor-direction records with distinct IDs also remain distinct. Do not claim real-world incident deduplication.

## Country registry

Retrieve or reuse the official CAMEO country lookup linked from GDELT's data page. Save its original bytes, source URL, retrieval date, and SHA-256. Create `country_registry.csv` with `code`, `label`, `eligible`, `entity_kind`, `reason`, and `source_version`. Allow genuine country/territorial country entries; exclude regional aggregates, cities, supranational organizations, and unresolved identifiers. Review the entries that can affect the top-30 roster using source labels/codebook evidence. Do not use a model's geographic guesses to manufacture a registry.

A generic ISO library may help flag mismatches, but is not authoritative for the CAMEO actor field. Keep CAMEO identifiers stable. Do not silently rewrite older codes to ISO aliases or merge distinct raw codes. If source aliases would represent the same entity more than once, document and test an explicit normalization map before cohort selection, and freeze it with the registry. If the original official lookup is temporarily inaccessible, retain the blocker or use an already verified cached copy; do not label an unverified third-party copy as official.

The agent should resolve routine, evidence-backed registry entries itself. An unresolved code may be excluded with a recorded reason; the report must quantify any discarded records and disclose this limitation. A change to the registry after looking at final outcomes invalidates the original cohort/configuration hash.

## Acquisition routes

### Route A: existing local export (default)

Accept CSV/TSV/Parquet and a coverage manifest. Record path-relative identities, sizes, hashes, source query/interval, extraction time, and whether the export was complete. A list of event rows without any extraction coverage evidence cannot certify zero-event days. It can be used for input debugging, but not a research-complete evaluation.

### Route B: BigQuery, only with existing access and an explicit budget

Use the official public Events dataset and inspect the actual schema/partition metadata before querying. The templates under `sql/` use named parameters, select only needed columns, retain unique event IDs, and filter exact `061` and bounded `DATEADDED`.

Do a dry run first, record estimated bytes, and use `maximum_bytes_billed` for any authorized execution. Filtering an event code or adding `LIMIT` does not by itself guarantee a cheap scan. Partition pruning is allowed only after verifying the table's actual partition type and its relationship to the chosen time field. Do not assume an ingestion partition always equals the event occurrence or first-added day.

No BigQuery query has been executed or cost-estimated for this handoff. Defaults disable execution of billable queries. If the user later provides an already authorized source/budget, the coder can proceed within it; otherwise produce a ready export request without blocking offline software implementation.

A successful complete query of a daily/quarterly interval can certify **extraction completeness relative to the queried public table at extraction time**. It cannot prove that GDELT's upstream news coverage was exhaustive. Keep those meanings separate.

### Route C: bounded official raw-file import

The optional importer can consume already downloaded official 15-minute export ZIPs. Select filenames through the official inventory, validate archive integrity, parse the Event schema, and track every expected inventory item. For new downloads, use bounded concurrency, retries, byte caps, and checkpoints. Do not automatically download the complete five-year raw archive. A missing expected file leaves that interval incomplete unless an authoritative source explicitly establishes that no file was published.

## Coverage manifest

Save one row per UTC day in the requested interval, including days with zero qualifying events. Required fields:

```text
date, status, evidence_kind, evidence_id, extraction_start_utc,
extraction_end_utc, source_row_count, eligible_row_count,
expected_parts, received_parts, source_snapshot_id, notes
```

`status` is `complete`, `missing`, or `failed`. Expected/received counts can be null for a successful full-table query whose completion receipt is the evidence; record the query job/export identifier instead. A manually supplied dataset must describe the export scope. The word complete refers to extraction, never complete global observation of economic relations.

For an origin T, require full extraction coverage for raw history `[T-118,T]` and labels `[T+1,T+30]`. Validate history and label coverage separately so prediction can run prospectively without future observations. Research evaluation requires both. A known coverage gap invalidates the whole origin for every model; do not drop individual negative rows.

The registered main research run expects all 12 final-year origins. If a gap cannot be repaired, produce an explicitly incomplete/reduced-coverage analysis with counts and reasons; do not set the fixed main study's `research_complete=true`. Complete the other engineering outputs and make the recovery task explicit.

## Normalized and derived tables

| Table | Primary key | Fields and invariants |
| --- | --- | --- |
| `events` | `event_id` | `country_a < country_b`, `event_day` (SQLDATE), `added_at_utc`, `observed_day`, `event_code='061'` |
| `country_registry` | `code` | Immutable source/version classification |
| `cohort` | `country_code` | Incidence count, selection rank/year, selected flag |
| `candidate_pairs` | `(country_a,country_b)` | Full combination set, sorted, fixed hash |
| `daily_counts` | `(observed_day,country_a,country_b)` | Nonnegative integer count; only certified days zero-filled |
| `daily_graph_features` | `(day,country_a,country_b)` | Jaccard, common neighbors, PA, endpoint degrees, graph window |
| `origins` | `(role,origin)` | Label start/end, raw support, context bounds, coverage status |
| `labels` | `(origin,country_a,country_b)` | Binary observed outcome, future count, completeness |
| `forecasts` | `(model_id,origin,country_a,country_b)` | Exactly 30 ordered point values, status, metadata |
| `predictions` | `(model_id,origin,country_a,country_b)` | Finite ranking score, optional probability, status, hashes |

The small starter `Event.event_day` specifically means **SQLDATE**. Its `observed_day` property derives the UTC day from `added_at`. Do not accidentally aggregate on the first field because its name looks convenient.

Use Parquet for research tables; JSON schemas describe run/prediction metadata. CSV is a human-readable export. Convert NaN/Infinity to an explicit error or documented null metric; never write invalid JSON. Sorting and hashing rules must be deterministic.

## Audit outputs

Produce totals by year, relation exclusions, country exclusions, self-pairs, malformed rows, duplicate IDs, conflicts, eligible record counts, retained cohort share, lag between SQLDATE and DATEADDED, and date coverage. A negative lag should be flagged for audit, not repaired by moving the observation timestamp. Since the main target uses recorded time, it remains distinct from claims about occurrence-date accuracy.

The final report should show what the data extraction establishes and what it cannot establish: language/media selection, observation noise, late reports, record multiplicity, and restricted country coverage remain limitations.
