#!/usr/bin/env python3
"""Offline full-kit installer; Python 3.8+, standard library only."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = (
    'SKILL.md', 'references/workflow.md', 'references/evidence.md',
    'references/openproject.md', 'references/model-selection.md',
    'templates/qa-report.md', 'templates/defect-report.md',
)


def installation_plan(target, scope, project, home=None, root=ROOT):
    home = Path.home() if home is None else Path(home)
    base = Path(project).expanduser().resolve() if scope == 'project' else home.resolve()
    if not base.is_dir():
        raise ValueError('Directory does not exist: ' + str(base))
    entries = []
    for host in ('codex', 'claude'):
        if target not in (host, 'both'):
            continue
        host_dir = base / ('.codex' if host == 'codex' else '.claude')
        if host == 'codex' and scope == 'user':
            host_dir = Path(os.environ.get('CODEX_HOME', str(host_dir))).expanduser().absolute()
        skill_dir = base / ('.agents/skills/qa-testing' if host == 'codex' else '.claude/skills/qa-testing')
        source_dir = root / 'skills/qa-testing'
        for name in SKILL_FILES:
            if not (source_dir / name).is_file():
                raise ValueError('Incomplete kit; missing source: ' + str(source_dir / name))
        for source in sorted(source_dir.rglob('*')):
            if source.is_symlink():
                raise ValueError('Source symlinks are unsupported: ' + str(source))
            if source.is_file():
                entries.append((skill_dir / source.relative_to(source_dir), source.read_bytes()))
        extension = 'toml' if host == 'codex' else 'md'
        source = root / ('agents/qa-tester.' + host + '.' + extension)
        if source.is_symlink():
            raise ValueError('Source symlinks are unsupported: ' + str(source))
        descriptor = source.read_text(encoding='utf-8')
        skill_path = str(skill_dir / 'SKILL.md')
        # TOML basic-string escaping also covers spaces, quotes and Windows paths.
        replacement = json.dumps(skill_path, ensure_ascii=False)[1:-1] if host == 'codex' else skill_path
        if '@@SKILL_PATH@@' not in descriptor:
            raise ValueError('Missing skill path marker: ' + str(source))
        entries.append((host_dir / ('agents/qa-tester.' + extension),
                        descriptor.replace('@@SKILL_PATH@@', replacement).encode('utf-8')))
    return entries


def preflight(entries, force):
    for destination, _ in entries:
        for path in (destination, *destination.parents):
            if path.is_symlink():
                raise ValueError('Refusing symlink destination or ancestor: ' + str(path))
            if path.exists() and path != destination and not path.is_dir():
                raise ValueError('Parent is not a directory: ' + str(path))
        if destination.exists():
            if not destination.is_file():
                raise ValueError('Destination is not a file: ' + str(destination))
            if not force:
                raise ValueError('Existing file; use --force to back up and replace: ' + str(destination))
            backup = destination.with_name(destination.name + '.bak')
            if backup.exists() or backup.is_symlink():
                raise ValueError('Backup collision; move the .bak file first: ' + str(backup))
            if not os.access(destination, os.W_OK):
                raise ValueError('Destination is not writable: ' + str(destination))
        parent = next(p for p in destination.parents if p.exists())
        if not os.access(parent, os.W_OK | os.X_OK):
            raise ValueError('Destination parent is not writable: ' + str(parent))


def install(entries, force=False):
    preflight(entries, force)
    changed, backups, directories = [], [], []
    try:
        for destination, content in entries:
            missing = []
            parent = destination.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                directories.append(directory)
            old = destination.read_bytes() if destination.exists() else None
            if old is not None:
                backup = destination.with_name(destination.name + '.bak')
                with backup.open('xb') as stream:
                    backups.append(backup)
                    stream.write(old)
            changed.append((destination, old))
            with destination.open('wb' if old is not None else 'xb') as stream:
                stream.write(content)
    except OSError as error:
        failures = []
        for destination, old in reversed(changed):
            try:
                if old is None:
                    destination.unlink(missing_ok=True)
                else:
                    destination.write_bytes(old)
            except OSError as cleanup:
                failures.append(str(cleanup))
        # Keep backups if restoration fails, so recovery remains possible.
        if not failures:
            for backup in backups:
                backup.unlink()
        for directory in reversed(directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        if failures:
            raise OSError('Install failed: %s; rollback failures: %s; retain .bak files for recovery'
                          % (error, '; '.join(failures))) from error
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('codex', 'claude', 'both'), default='both')
    parser.add_argument('--scope', choices=('project', 'user'), default='project')
    parser.add_argument('--project', default='.', help='Existing application directory for project scope')
    parser.add_argument('--force', action='store_true', help='Back up and replace kit files; refuse backup collisions')
    args = parser.parse_args(argv)
    try:
        entries = installation_plan(args.target, args.scope, args.project)
        install(entries, args.force)
    except (OSError, ValueError) as error:
        print('Installation failed: ' + str(error), file=sys.stderr)
        return 2
    for destination, _ in entries:
        print('Installed:', destination)
    print('Restart the host and verify qa-tester discovery. No host config was edited.')
    print('OpenProject is optional; install/authenticate its integration separately for task-ID mode.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
