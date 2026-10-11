#!/usr/bin/env python3
"""Build a deterministic ZIP and SHA-256 using an explicit source allowlist."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    'README.md', 'LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
    '.gitignore', '.gitattributes',
    'skills/qa-testing/SKILL.md',
    'skills/qa-testing/references/workflow.md',
    'skills/qa-testing/references/evidence.md',
    'skills/qa-testing/references/openproject.md',
    'skills/qa-testing/references/model-selection.md',
    'skills/qa-testing/templates/qa-report.md',
    'skills/qa-testing/templates/defect-report.md',
    'agents/qa-tester.codex.toml', 'agents/qa-tester.claude.md',
    'install/install.py', 'install/install.ps1',
    'examples/standalone-test-cases.md', 'examples/frd-uss-handoff.md',
    'examples/openproject-invocation.md', 'examples/project-qa-context.md',
    'docs/installation.md', 'docs/compatibility.md',
    'tests/test_installer.py', 'tests/test_install.ps1', 'tests/test_package.py',
    'scripts/build_release.py',
    '.github/workflows/validate.yml', '.github/workflows/release.yml',
    '.github/ISSUE_TEMPLATE/bug_report.yml', '.github/ISSUE_TEMPLATE/feature_request.yml',
    '.github/pull_request_template.md',
)


def build(version, output, root=ROOT):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', version):
        raise ValueError('Version must be a stable tag such as v1.4.0')
    # Validate all sources before creating output. Nothing is collected recursively.
    for name in FILES:
        path = root / name
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('Missing or linked release source: ' + name)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / ('qa-testing-agent-' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as package:
        for name in sorted(FILES):
            info = zipfile.ZipInfo('qa-testing-agent-' + version + '/' + name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            # Normalize Git's platform-specific checkout line endings.
            content = (root / name).read_bytes().replace(b'\r\n', b'\n')
            package.writestr(info, content)
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix('.zip.sha256')
    checksum.write_bytes((digest + '  ' + archive.name + '\n').encode('ascii'))
    return archive, checksum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='v1.4.0')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        for path in build(args.version, args.output):
            print(path)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
