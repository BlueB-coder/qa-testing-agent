# Evidence and verdicts

Record actual observations, not intentions. An exit code proves only the command's
outcome; static review does not prove browser behavior or vendor integration.

Each evidence manifest entry records: ID, requirement/case IDs, relative artifact
path, evidence kind, target/environment, revision, command and cwd (if applicable),
exit code, timestamp/timezone, capture status, actual inspection status and redaction
notes. Use a Markdown table or JSON; do not include secrets or private fixture manifests.
Store raw logs/screenshots in a project-approved ignored folder such as `.qa-output/`.
Sanitized reports may use `docs/qa/reports/` when project conventions permit.

Per-case statuses: Passed, Failed, Blocked, Not Tested. A case passes only when
its required expectations have been checked with the required evidence.

Overall verdict precedence:

1. **Failed**: a confirmed mandatory expectation fails, even if other cases are blocked.
2. **Blocked**: no mandatory failure is confirmed and required execution cannot proceed
   safely or meaningfully because of an environment or essential requirement blocker.
3. **Incomplete**: partial coverage or missing required evidence without a blocker
   preventing execution, including Not Tested mandatory cases.
4. **Passed**: all mandatory checks and evidence are complete, with no unresolved failure.

Report optional omissions, observations and coverage gaps separately. A test-harness
defect is not automatically an application failure. Captured-only screenshots cannot
support claims requiring visual inspection. Retain historical timestamps and revisions;
never reuse an old pass for a new revision without rerunning the relevant checks.
