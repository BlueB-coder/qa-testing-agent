# Portable QA Testing Agent

One reusable `qa-testing` skill, native `qa-tester` adapters for Codex and Claude
Code, and offline installers. Test from OpenProject task IDs, Markdown requirements,
FRD/USS documents or inline cases; produce traceable reports and evidence. QA authors
tests and reports defects while developers own application fixes.

## Install the complete kit

Clone the repository or extract a tagged release, inspect it, then run from its root.

```sh
git clone https://github.com/BlueB-coder/qa-testing-agent.git
cd qa-testing-agent
python3 install/install.py --target both --scope project --project /path/to/application
```

Windows PowerShell (no Python required):

```powershell
.\install\install.ps1 -Target both -Scope project -ProjectPath "C:\path\to\application"
```

Choose `codex`, `claude` or `both`, and `project` or `user` scope. Restart the host
after the first installation and verify agent discovery. Installers refuse existing
files by default. Explicit `--force` / `-Force` creates `.bak` backups and refuses
backup collisions. See [installation and upgrades](docs/installation.md).

## How to use

Open your application repository in a host that has discovered the native agent.
Its test runtime and isolated QA environment must be available.

### OpenProject

```text
Delegate QA testing for OpenProject task #1234 to the qa-tester agent.
```

Install and authenticate the separate [OpenProject integration](https://github.com/yungts97/openproject-skill)
in the same operating environment first. QA reads cases and referenced ACs, executes
safe tests and prepares an unposted report. Task retrieval is read-only; every external
write requires explicit approval of exact content and actions.

### Standalone Markdown

```text
Delegate QA testing to the qa-tester agent using docs/qa/test-cases.md.
```

No OpenProject integration is needed or contacted. Local reports follow project
conventions, defaulting to `docs/qa/reports/` when permitted. See the
[synthetic cases](examples/standalone-test-cases.md).

### FRD / USS

```text
Delegate QA testing to the qa-tester agent using docs/FRD.md and docs/USS.md.
Derive test cases from the acceptance criteria and prepare a QA report.
```

Use actual filenames. FRD normally means Functional Requirements Document; if your
project uses `RFD.md`, pass that path. Derived scenarios are labeled and linked to
their source ACs. Combined sources retain provenance and unresolved conflicts.
See the [handoff example](examples/frd-uss-handoff.md).

### Inline cases

```text
Delegate QA testing to the qa-tester agent.
Test cases:
1. Valid credentials allow login.
2. Incorrect passwords are rejected.
3. Unauthenticated users cannot access protected pages.
4. Logout invalidates the session.
```

## Skill-only installation

Copy the complete `skills/qa-testing/` directory into a supported host skill location
listed in [installation](docs/installation.md). Keep `references/` and `templates/`.
This installs the workflow; it does not install or register `qa-tester`.

```text
Use the qa-testing skill to test docs/qa/test-cases.md and prepare a QA report.
```

This fallback runs in the main agent when native delegation is unavailable. The
optional skills CLI discovery status and publishing prerequisites are recorded in
[compatibility](docs/compatibility.md); Node/npm is unnecessary for full-kit installers.

## Prerequisites and compatibility

| Component | Requirement | Validation |
| --- | --- | --- |
| Python installer | Python 3.8+; no third-party dependencies | Tested locally on Linux with Python 3.12.3 |
| PowerShell installer | Standalone script; Windows support awaits CI | 76 assertions passed on Linux, PowerShell 7.6.6; Windows 5.1/7 jobs configured |
| Codex native adapter | Custom TOML agents and local skills support | Format checked against current documentation; live discovery/invocation pending |
| Claude Code native adapter | Markdown subagents and skills support | Format checked against current documentation; live discovery/invocation pending |
| QA runtime | Application's test tools and isolated environment | Supplied by target project |
| OpenProject | Separate integration/authentication for explicit task-ID mode | Live pilot pending; unnecessary for standalone QA |

CI definitions are not executed CI results. See [recorded validation and pilot gates](docs/compatibility.md).
Other compatible skill hosts may work after testing; no native adapter is provided
for them. Models inherit by default; overrides require real host-supported identifiers.

## Outputs and verdicts

Every run produces a [QA report](skills/qa-testing/templates/qa-report.md) and evidence
manifest: sources, revision, initial dirty state, environment, exact commands and
exit codes, per-case results, screenshot inspection state, defects and fixture cleanup.

- **Passed**: all mandatory checks and required evidence are complete.
- **Failed**: a confirmed mandatory failure, even when other checks are blocked.
- **Blocked**: no confirmed mandatory failure, but required execution cannot proceed safely or meaningfully.
- **Incomplete**: partial unverified coverage or missing evidence without such a blocker.

Per-case statuses are Passed, Failed, Blocked or Not Tested. Written tests and saved
screenshots alone do not establish a pass. External comment approval does not authorize
attachments, defect creation or status changes; each needs explicit approval and
revalidation before submission. Standalone reports contain no OpenProject draft.

The kit's test-only instructions are behavioral restrictions. Stronger source access
protection needs host permissions or isolated mounts; Codex workspace-write permits
workspace writes. No model runtime, framework installer, service or scheduling is included.

## Updates, validation and troubleshooting

Inspect the new version before forcing an upgrade. Preserve and move existing `.bak`
files before another forced installation. See [installation](docs/installation.md)
for overwrite and recovery behavior; unrelated files are preserved.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --version v1.4.0
```

PowerShell checks: `pwsh -NoProfile -File tests/test_install.ps1`, or run the same
test with `powershell.exe` for Windows PowerShell 5.1. ZIP and SHA-256 outputs go to
ignored `dist/`. Release packaging includes only the explicit source allowlist.

If an agent is missing, restart and check the installed destinations and host version.
Older Codex releases may need manual registration; follow that version's official
documentation, or use the skill-only fallback. The installers do not edit host configuration.
If QA lacks an isolated runtime, expect a blocker report instead of a pass.

## License and contributions

This kit is provided under [MIT](LICENSE).
Read [contribution guidance](CONTRIBUTING.md), [security guidance](SECURITY.md) and
[changes](CHANGELOG.md).

Host and integration documentation:
[OpenProject skill](https://github.com/yungts97/openproject-skill),
[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Claude subagents](https://code.claude.com/docs/en/sub-agents) and
[Claude skills](https://code.claude.com/docs/en/skills).
