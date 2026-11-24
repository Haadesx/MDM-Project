# Synthetic fixture provenance and hand calculations

These files contain **invented test records and scores**. They are not GDELT
observations, predictions from Timestral, or project results. The deliberately
invalid Geo country values make accidental use of Geo fields detectable.

- `gdelt_events_synthetic.json`: nine distinct invented `GlobalEventID` records,
  plus one exact duplicate of the first row. Reversed actors on event 1002 test
  undirected canonicalization. That event and event 1009 have occurrence dates
  earlier than their `DATEADDED` observation dates.
- `ranking_synthetic.json`: six unordered pairs of four artificial countries
  A/B/C/D, with a tie at score 0.7. Only AB is positive.
- `golden_expected.json`: independently specified expected values for review.
  The executable tests also assert the values explicitly, so a future agent
  cannot make tests pass merely by editing a golden file.

## Calendar and graph oracle

Origin **January 31, 2024** is the end of the UTC day. Its 90-day input is
November 3, 2023 through January 31, 2024. Thirty-day trailing graphs for every
input day require raw records beginning October 5, 2023: 119 days in total.
The future label period is February 1 through March 1, 2024 inclusive, because
2024 is a leap year.

The graph at origin uses January 2 through January 31. Its three edges are
AUS-CAN, CAN-IND and IND-USA. The January 1 AUS-IND record is too old; all
February/March records are in the future. Event multiplicity does not create
multiple graph edges.

For AUS and IND, the neighbor sets are `{CAN}` and `{CAN, USA}`. Therefore
common neighbors = 1, Jaccard = 1/2, and preferential attachment = 1*2 = 2.
For CAN and IND, the neighbor sets are `{AUS, IND}` and `{CAN, USA}`. Their
intersection is empty and degree product is 2*2 = 4. Existing candidate edges
are not deleted when computing historical features.

The next-30-day positive pairs are AUS-USA (March 1), CAN-USA (February 1),
and IND-USA (February 5). The last is positive by its observation date even
though its recorded occurrence date is January 10. AUS-IND on March 2 is
outside the horizon. AUS-CAN on January 31 is outside the future horizon.

## Ranking oracle

| Pair | Score | Label |
| --- | ---: | ---: |
| AD | 0.9 | 0 |
| AB | 0.7 | 1 |
| AC | 0.7 | 0 |
| BC | 0.6 | 0 |
| BD | 0.2 | 0 |
| CD | 0.1 | 0 |

- **ROC AUC = 0.7:** the positive beats three negatives, ties one, and loses
  to one, giving `(3 + 0.5) / 5`.
- **Average precision = 1/3:** at the threshold where the only positive is
  retrieved, three pairs have been retrieved. Equal scores form one threshold
  block; a lexical ordering must not raise AP to 1/2.
- **Expected precision at 2 = 0.25:** AD consumes the first position. One of
  AB/AC is uniformly selected for the second position, so expected hits = 0.5
  and expected precision = 0.5/2. Deterministic lexical sorting is for displayed
  tables only, never the primary metric.
- **Filtered endpoint MRR = 0.7:** for A->B, AD ranks above the target and AC
  ties it, giving mean rank 2.5 and reciprocal rank 0.4. For B->A the target is
  first, giving reciprocal rank 1. Their average is 0.7. There are two positive
  directed endpoint queries.

When two true counterparts share a focal country, the MRR calculation removes
the *other* positives for each target query. It never removes negatives. This
is a filtered link-completion metric, not the reciprocal rank of the first
positive in a global list.

## Intentional RED state

The package provides 43 behavioral tests and explicit `NotImplementedError`
algorithm stubs. These tests are meant to fail before implementation. They
exercise the contracts above without network access, a model download, pandas,
or a GPU. They are a starter, not the entire completion gate: adapter, full
pipeline, calibration isolation and artifact/provenance tests must be added
during implementation according to the test plan.

Run from the project root using only Python's standard test runner:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

After installing the optional test dependencies, `python -m pytest` runs the
same suite. Do not change expected scientific behavior, mark tests skipped, or
replace forecast outputs with fixtures to manufacture a successful project.
