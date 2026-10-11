# QA execution workflow

1. Read applicable project instructions, including `.codex/AGENTS.md` when present.
   Respect restrictions on configuration and sensitive files. Resolve explicit
   sources, referenced ACs and affected implementation before diagnosing behavior.
2. Record repository path, branch, revision, dirty-worktree state, requirement source
   revisions, timestamp with timezone, runtime, tool versions and permitted write paths.
   Inspect manifests and existing runners; do not assume a framework or copy commands
   from another project. Preserve unrelated edits.
3. Map every source case and mandatory AC to coverage. Include source location,
   exact expected result, derived-scenario label where applicable, test path and
   required evidence. Flag contradictions and missing expected outcomes.
4. Verify target URL/environment/database, isolated test identities, fixture scope
   and cleanup before mutation. Do not infer isolation from a hostname alone.
   If unsafe or inaccessible, retain a coverage plan and report the blocker.
5. Reuse existing tests. Write missing tests only in project-permitted test/fixture
   directories. Record QA modifications separately from the initial worktree state.
6. Run focused tests, then regression justified by affected dependencies and risks.
   Record actual cwd, command, target, timestamps, exit status and redacted log path.
   Distinguish assertion failures from runner crashes and setup problems.
7. For UI cases, exercise real interactions, negative states and persisted behavior
   where required. Capture representative desktop/mobile viewports, console/network
   failures and keyboard/accessibility behavior relevant to requirements. State whether
   each screenshot was captured only or actually inspected.
8. Classify findings as application defect, test defect, environment blocker or
   coverage gap. Report reproduction, expected/actual, impact and evidence. Never
   modify product code to turn a failure into a pass.
9. Clean up only owned fixtures and test identities. Report cleanup failures and
   pending manual steps without exposing credentials. Compare the application diff
   against the recorded initial state; report accidental source changes immediately.
10. Produce the QA report and evidence manifest. OpenProject mode additionally
    prepares exact unposted drafts; standalone mode ends with local deliverables.
    Retest fixes against the new revision and preserve older results as historical.
