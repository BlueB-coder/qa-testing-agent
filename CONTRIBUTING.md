# Contributing

Keep `skills/qa-testing/` the single canonical QA workflow. Native adapters should
load it, not maintain a separate workflow. Keep OpenProject optional and avoid
application fixes, orchestration services or new authentication code in this kit.

Use synthetic examples and no secrets, customer data, browser state or raw QA runs.
Preserve existing installer flags. Include meaningful regression checks for install,
backup, rollback or packaging behavior when changing those paths.

Git is required for the package ignore-rule check.
Run `python3 -m unittest discover -s tests -v` and
`python3 scripts/build_release.py --version v1.4.0`. Windows changes also need
`tests/test_install.ps1` in PowerShell 7 and Windows PowerShell 5.1 before claiming
support. Add new release files explicitly to `scripts/build_release.py`'s allowlist.

Report exact validation and remaining gaps. Installer CI is distinct from live host
and browser pilots. Use the PR template and review license/ownership before publication.
