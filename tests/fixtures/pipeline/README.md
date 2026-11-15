# Pipeline integration test

From the repository root, run `python -m pytest -q -rxX tests/test_pipeline_integration.py`.
The GitHub Actions workflow **Pipeline tests** also runs this check on pull requests targeting
`main`, on pushes to `main`, and on demand.

The test copies the tracked three-tile Earth sample, lunar reference data and the inputs
required by the atlas to a temporary checkout. It uses the real `sites`, `validate-enrichment`
and `app/build_data.py` entry points. The ranking stage fetches the same checksum-verified
Natural Earth country outlines as a normal fresh checkout. The test does not run the cloud
scan or download any elevation or satellite data. Other validation reports supply precomputed
inputs the atlas expects, and context tables contain headers only.

The test asserts that the ranking, site geometry records, validation report and atlas export
agree. It also checks that removing the scored cells or ranking CSV fails at the consumer
and leaves its previous output available. The synthetic reference list includes lunar,
Mars-only and operational rows. The Mars-only assertion is marked as an expected failure
until the known enrichment issue is fixed. Strict mode turns an unexpected pass red, so
the fix can remove the marker in the same change.

## Update an expected result

`expected.json` holds the sample tile IDs, counts, ordered ranking rows, a numeric tolerance
for the best-window area and the water filter cases. When a deliberate algorithm or fixture
change alters an expected result, run the test, inspect the output difference, and update
the applicable value and the reason in the same pull request. Keep the assertions that compare
the generated files with each other. Test outputs stay in the temporary directory.

Written with SI assistance (Codex).
