# Authoring-time validation of this implementation kit

Prepared and checked on November 20, 2026. These checks concern the supplied specification and intentional red starter, not a completed application or scientific experiment.

## Executed starter check

From the extracted project root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Actual execution used Python 3.12.14. The package targets Python 3.11+; no claim is made that a finished ML dependency lock was tested on every version/platform.

| Observation | Actual result |
| --- | --- |
| Behavioral test cases executed | 43 |
| Reported errors, including subtests | 48 |
| Error cause | All intentionally unimplemented functions raised NotImplementedError |
| Assertion failures | 0 |
| Skips | 0 |
| Accidental import/syntax failures in the project-root invocation | 0 |
| Application algorithms implemented | No |
| Real-data/model experiment executed | No |

The normal test command exits unsuccessfully in this red starter. That is expected. It must become a genuinely passing implementation suite during Codex's work; no xfail/skip or fake-backend shortcut counts as completion. Machine-readable evidence is in `validation/starter_red_run.json`.

## Package and specification checks

- Numbered documents 01-13, source materials, configuration, schemas, interfaces, fixtures, and prompt/working rules are present.
- Configuration consistency checks reconcile 30 countries, 435 pairs, 90 input rows, 119 raw support days, 30-day horizons, year roles, and all ten required model IDs.
- Python sources parse. Work-package dependencies form an acyclic graph.
- The four JSON schemas pass Draft 2020-12 meta-validation. Representative invalid probability/support/completion examples are rejected.
- Model documentation, machine configuration, and acceptance inventory were reconciled in an independent focused review.
- Synthetic metric/calendar expectations were independently reviewed, including isolated lower-bound tests added to prevent masked off-by-one errors.
- The source PDF is preserved byte-for-byte. The ten-page companion PDF was rendered and visually inspected for readable tables, figures, page breaks, and absence of clipping/overlap.
- The archive is checked for integrity and includes a SHA-256 manifest of its contents.

Run `python3 scripts/verify_kit.py` once on receipt to verify the intact package. Deliberate implementation edits will change the original hashes; use `--structure-only` for an optional structure check thereafter. Do not use this package-integrity checker as a substitute for application tests.

## Remaining execution prerequisites

The implementation must acquire/validate real GDELT data and extraction coverage, retrieve/classify the official country registry, resolve actual package/model revisions, implement the application, execute genuine backend smoke tests, and run the complete experiment. The official country lookup's bytes were not available to the authoring research tool. Nothing in the kit fabricates that lookup, a final country roster, or a model-performance result.
