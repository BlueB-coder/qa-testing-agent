# Compatibility and validation record

Validation recorded: 11 October 2026 (Asia/Kuala_Lumpur). Native adapters
target Codex and Claude Code. A portable skill is not a universal native-agent adapter.

## Recorded checks

| Check | Environment/version | Result |
| --- | --- | --- |
| Python installer/package tests | Linux, Python 3.12.3 | 18 tests passed |
| Canonical skill/adapters | Current official documentation | Sources and schema reviewed; package tests parse descriptors |
| Local Codex executable | codex-cli 0.159.2 | Version observed only; no discovery/invocation pilot |
| PowerShell installer | Linux, PowerShell 7.6.6 | 76 assertions passed; both scopes/targets, overwrite/backup/preflight/rollback, broken backup links |
| Windows/macOS installation | CI configured | Not an executed result |
| Native QA behavior / browser / OpenProject | No provider/customer run used | Unverified live pilots |
| Optional skills CLI discovery | Downloaded npm package execution | Automatic approval review rejected execution; unverified, no CLI installation command advertised |
| Release package | Python 3.12.3 | Integrity, deterministic contents, SHA-256, allowlist and extracted-install equivalence passed |
| Skill frontmatter / relative links | Canonical skill and source package | Skill validator passed; all packaged relative Markdown links resolve |
| YAML / TOML metadata | Installed local PyYAML and standard-library tomllib | Frontmatter and GitHub YAML parsed; source/generated TOML passed |

Automated packaging tests prove installation and artifact invariants, not model
behavior. The optional skills CLI was not executed: automatic review rejected
downloading/executing third-party npm code with repository access. Local schema and
link validation completed; remote skill discovery remains a release gate.
Python 3.8 syntax was checked locally; runtime support is covered by a dedicated CI job;
full schema tests use Python 3.11+ for standard-library TOML parsing.

Reproduce the checks from kit root:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --version v1.4.0
pwsh -NoProfile -File tests/test_install.ps1
```

For local PowerShell validation, the official 7.6.6 Linux archive was downloaded to
`/tmp`, verified against the [publisher's SHA-256](https://github.com/PowerShell/PowerShell/releases/tag/v7.6.6),
and used with cache/config/data directories under `/tmp` to respect the workspace
sandbox. No system PowerShell installation or user-profile change was made. Windows
PowerShell 5.1 and Windows/macOS filesystem behavior remain unexecuted locally.

## CI scope

Validation jobs run Python installer/package tests on Ubuntu, macOS and Windows.
Windows runs the standalone PowerShell suite under PowerShell 7 and Windows
PowerShell 5.1 separately. The PowerShell user-scope test substitutes only the home
resolver in a temporary installer copy, isolating writes while exercising the same
scope/destination logic. CI contains no provider credentials or customer application.

## Live pilot release gates

Before claiming runtime support or publishing v1.4.0, record:

- Actual Codex and Claude versions, agent discovery and native invocation.
- Standalone file and FRD/USS reports with source traceability and no OpenProject calls.
- OpenProject retrieval of the intended task with exact unposted drafts and project status names.
- Synthetic passing, mandatory failing and inaccessible-environment scenarios with correct verdicts.
- Application diff compared to initial state, executed commands/exit codes, fixture cleanup
  and actually inspected responsive screenshots.
- Skills CLI discovery against the published repository, fresh-clone installation and
  release-download installation. Local discovery does not prove a remote URL exists.

Record evidence, versions, limitations and date. Do not upgrade pending checks to
passed because installer tests passed. The release workflow creates a draft on a
valid tag for review before publication.
