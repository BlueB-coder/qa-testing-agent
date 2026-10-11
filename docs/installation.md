# Installation and recovery

Full-kit installers are offline and write only the selected kit artifacts. Run from
a clone or extracted release root with an existing application directory. They neither
install dependencies nor authenticate integrations, run tests or change host configuration.

```sh
python3 install/install.py --target codex --scope project --project "/path/with spaces/app"
python3 install/install.py --target claude --scope user
python3 install/install.py --target both --scope project --project /path/to/app --force
```

```powershell
.\install\install.ps1 -Target codex -Scope project -ProjectPath "C:\path with spaces\app"
.\install\install.ps1 -Target claude -Scope user
.\install\install.ps1 -Target both -Scope project -ProjectPath "C:\app" -Force
```

Defaults: both hosts, project scope, current directory, no overwrite.
Options: Python `--target`, `--scope`, `--project`, `--force`; PowerShell `-Target`,
`-Scope`, `-ProjectPath`, `-Force`. User scope ignores the project argument.

| Host | Project skill | User skill | Native agent |
| --- | --- | --- | --- |
| Codex | `<project>/.agents/skills/qa-testing/` | `~/.agents/skills/qa-testing/` | `<project>/.codex/agents/qa-tester.toml` or `$CODEX_HOME/agents/qa-tester.toml` (default `~/.codex`) |
| Claude Code | `<project>/.claude/skills/qa-testing/` | `~/.claude/skills/qa-testing/` | `<project>/.claude/agents/qa-tester.md` or `~/.claude/agents/qa-tester.md` |

Installed descriptors contain the absolute installed skill path, with TOML escaping
for Windows paths. Reinstall after moving an installation. Copying raw descriptor
templates directly will leave unresolved markers; use the installer for a full kit.
Skill-only copying does not require descriptor generation.

Destination paths follow the documentation checked on 11 October 2026:
[Codex skill locations](https://learn.chatgpt.com/docs/build-skills),
[Codex agents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Claude skills](https://code.claude.com/docs/en/skills) and
[Claude agents](https://code.claude.com/docs/en/sub-agents).
Current Codex documents agent-file discovery; older config-layer implementations
may require manual role registration. Check installed-version documentation. Do not
assume an arbitrary old CLI or hosted client supports these local files. Restart
the host after installing into a newly created agent directory and verify `qa-tester`.

## Overwrite and recovery

All sources and destinations are preflighted before writes. Existing kit files cause
refusal unless force is explicit. Force makes one `.bak` per replaced file; backup
files or directories cause refusal. Symlink/reparse destinations and ancestors are
refused to avoid writing outside the intended location. Unrelated files are preserved.
Do not edit destinations concurrently with an installation.

Write failures trigger restoration of previous contents and removal of newly created
files/directories. If rollback also fails, the error names failures and retains backups
for recovery. Filesystem ACLs and concurrent changes cannot be fully predicted by
preflight; check actionable errors and final state. This is not an atomic filesystem
transaction and does not promise preservation of all filesystem metadata.

To revert a successful forced upgrade, inspect each `.bak` and manually restore the
selected kit files. Archive existing backups outside the installed skill before the
next force operation. No uninstall command deletes unrelated or legacy files.

## Operating environments

Windows and WSL have separate home directories, credentials and tool installations.
Install and authenticate in the environment that runs the host; shared project paths
must be intentionally chosen. Full-kit Python requires 3.8+; the PowerShell script
is independent of Python. Platform execution status is in [compatibility](compatibility.md).
