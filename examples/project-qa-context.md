# Example application QA context

Synthetic context to adapt in an application's permitted QA documentation:

- Repository: the current local fixture application; record its real revision and dirty state.
- Requirements: `docs/qa/test-cases.md`, with referenced FRD/USS sections.
- Allowed writes: `tests/`, synthetic fixtures under `tests/fixtures/`, reports under
  `docs/qa/reports/`, raw evidence under ignored `.qa-output/`.
- Runtime: use the actual project's documented test runner and browser commands.
- Environment: isolated disposable local database, verified by the application's
  documented reset and fixture procedures. A local URL alone is insufficient proof.
- Identities: synthetic editor/viewer fixtures, never real customer accounts.
- Cleanup: delete only records and identities created by this run; record results.
- Integration: none unless an explicit OpenProject work-package ID is provided.

Do not copy credentials, production database settings or guessed test commands into
this file. Source files are readable for diagnosis; developers own application fixes.
