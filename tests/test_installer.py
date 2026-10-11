import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('installer', ROOT / 'install/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='qa kit tests ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'application with spaces'
        self.project.mkdir()
        self.home = self.base / 'user home'
        self.home.mkdir()

    def plan(self, target='both', scope='project', root=ROOT):
        with patch.dict(os.environ, {}, clear=True):
            return installer.installation_plan(target, scope, self.project, self.home, root)

    def test_fresh_all_targets_and_scopes(self):
        for target in ('codex', 'claude', 'both'):
            for scope in ('project', 'user'):
                with self.subTest(target=target, scope=scope):
                    entries = self.plan(target, scope)
                    installer.install(entries)
                    for path, content in entries:
                        self.assertEqual(path.read_bytes(), content)
                        self.assertNotIn(b'@@SKILL_PATH@@', content)
                    for path, _ in entries:
                        path.unlink()

    def test_templates_are_installed_and_descriptors_resolve_skill(self):
        installer.install(self.plan())
        for host in ('.agents', '.claude'):
            skill = self.project / host / 'skills/qa-testing'
            self.assertTrue((skill / 'templates/qa-report.md').is_file())
            self.assertTrue((skill / 'templates/defect-report.md').is_file())
        descriptor = self.project / '.codex/agents/qa-tester.toml'
        self.assertIn(str(self.project / '.agents/skills/qa-testing/SKILL.md'), descriptor.read_text())

    def test_repeat_refusal_force_and_collision_preserve_unrelated_files(self):
        unrelated = self.project / '.claude/notes.txt'
        unrelated.parent.mkdir()
        unrelated.write_bytes(b'keep me')
        entries = self.plan()
        installer.install(entries)
        before = snapshot(self.project)
        with self.assertRaisesRegex(ValueError, 'Existing file'):
            installer.install(entries)
        self.assertEqual(before, snapshot(self.project))
        changed = [(path, b'updated') for path, _ in entries]
        installer.install(changed, force=True)
        for path, old in entries:
            self.assertEqual(path.with_name(path.name + '.bak').read_bytes(), old)
        before = snapshot(self.project)
        with self.assertRaisesRegex(ValueError, 'Backup collision'):
            installer.install(entries, force=True)
        self.assertEqual(before, snapshot(self.project))
        self.assertEqual(unrelated.read_bytes(), b'keep me')

    def test_late_conflict_prevents_partial_install(self):
        entries = self.plan()
        destination = entries[-1][0]
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b'existing')
        before = snapshot(self.project)
        with self.assertRaises(ValueError):
            installer.install(entries)
        self.assertEqual(before, snapshot(self.project))
        self.assertFalse((self.project / '.agents').exists())

    def test_parent_file_prevents_partial_install(self):
        (self.project / '.claude').write_bytes(b'not a directory')
        before = snapshot(self.project)
        with self.assertRaisesRegex(ValueError, 'Parent is not a directory'):
            installer.install(self.plan())
        self.assertEqual(before, snapshot(self.project))

    def test_destination_directory_and_backup_directory_refused(self):
        entries = self.plan()
        path = entries[-1][0]
        path.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'not a file'):
            installer.install(entries, True)
        path.rmdir()
        path.write_bytes(b'old')
        path.with_name(path.name + '.bak').mkdir()
        with self.assertRaisesRegex(ValueError, 'Backup collision'):
            installer.install(entries, True)

    def test_missing_source_prevents_any_write(self):
        broken = self.base / 'incomplete kit'
        broken.mkdir()
        with self.assertRaisesRegex(ValueError, 'Incomplete kit'):
            self.plan(root=broken)
        self.assertEqual(snapshot(self.project), {})

    def test_symlink_parent_refused(self):
        try:
            (self.project / '.agents').symlink_to(self.home, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            installer.install(self.plan())
        self.assertEqual(snapshot(self.home), {})

    def test_write_failure_rolls_back_fresh_and_forced_install(self):
        entries = self.plan()
        original_open = Path.open
        for force in (False, True):
            with self.subTest(force=force):
                if force:
                    installer.install(entries)
                before = snapshot(self.project)
                failed = False

                def fail_once(path, mode='r', *args, **kwargs):
                    nonlocal failed
                    if path == entries[-1][0] and mode in ('wb', 'xb') and not failed:
                        failed = True
                        raise OSError('simulated full disk')
                    return original_open(path, mode, *args, **kwargs)

                with patch.object(Path, 'open', fail_once):
                    with self.assertRaisesRegex(OSError, 'full disk'):
                        installer.install(entries, force)
                self.assertEqual(snapshot(self.project), before)
                if not force:
                    self.assertEqual(list(self.project.iterdir()), [])

    def test_codex_home_and_current_user_skill_location(self):
        custom = self.home / 'custom codex'
        with patch.dict(os.environ, {'CODEX_HOME': str(custom)}):
            entries = installer.installation_plan('codex', 'user', self.project, self.home)
        installer.install(entries)
        self.assertTrue((custom / 'agents/qa-tester.toml').is_file())
        self.assertTrue((self.home / '.agents/skills/qa-testing/SKILL.md').is_file())
        self.assertFalse((self.home / '.codex/skills').exists())

    def test_existing_install_upgrade_adds_bundled_templates(self):
        # Existing installation with a customized skill and descriptor, without templates.
        skill = self.project / '.agents/skills/qa-testing/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_bytes(b'existing skill')
        agent = self.project / '.codex/agents/qa-tester.toml'
        agent.parent.mkdir(parents=True)
        agent.write_bytes(b'existing agent')
        installer.install(self.plan('codex'), True)
        self.assertEqual(skill.with_name('SKILL.md.bak').read_bytes(), b'existing skill')
        self.assertTrue((skill.parent / 'templates/qa-report.md').is_file())

    def test_cli_and_actionable_errors(self):
        command = [sys.executable, str(ROOT / 'install/install.py'), '--target', 'both',
                   '--scope', 'project', '--project', str(self.project)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        repeat = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(repeat.returncode, 0)
        self.assertIn('--force', repeat.stderr)


if __name__ == '__main__':
    unittest.main()
