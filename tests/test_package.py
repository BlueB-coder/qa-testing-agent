import hashlib
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_release.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def metadata(path):
    """Validate this kit's intentionally small YAML frontmatter subset."""
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError('Missing frontmatter: ' + str(path))
    header, body = text[4:].split('\n---\n', 1)
    values = {}
    list_key = None
    for line in header.splitlines():
        if line.startswith('  - ') and list_key:
            values[list_key].append(line[4:])
            continue
        match = re.fullmatch(r'([a-z-]+):(?: (.+))?', line)
        if not match or match[1] in values:
            raise ValueError('Invalid or duplicate metadata field: ' + line)
        key, value = match.groups()
        if value is None:
            values[key] = []
            list_key = key
        else:
            # Plain YAML scalars must not accidentally become nested mappings.
            if ': ' in value or value.startswith(('{', '[', '*', '&', '!', '#', '|', '>')):
                raise ValueError('Unsupported YAML scalar: ' + value)
            values[key] = value
            list_key = None
    if not body.strip():
        raise ValueError('Empty instructions')
    return values


class PackageTests(unittest.TestCase):
    def test_descriptor_metadata_and_generated_toml(self):
        skill = metadata(ROOT / 'skills/qa-testing/SKILL.md')
        self.assertEqual(set(skill), {'name', 'description'})
        self.assertEqual(skill['name'], 'qa-testing')
        self.assertTrue(skill['description'])
        claude = metadata(ROOT / 'agents/qa-tester.claude.md')
        self.assertEqual(set(claude), {'name', 'description', 'model', 'skills'})
        self.assertEqual(claude['name'], 'qa-tester')
        self.assertEqual(claude['model'], 'inherit')
        self.assertEqual(claude['skills'], ['qa-testing'])
        codex = tomllib.loads((ROOT / 'agents/qa-tester.codex.toml').read_text())
        self.assertEqual(set(codex), {'name', 'description', 'sandbox_mode', 'developer_instructions'})
        self.assertEqual(codex['name'], 'qa-tester')
        self.assertEqual(codex['sandbox_mode'], 'workspace-write')
        self.assertTrue(codex['developer_instructions'])
        for path in ('/tmp/app with spaces/SKILL.md', 'C:\\QA "demo"\\SKILL.md', '/tmp/測試 🧪/SKILL.md'):
            import json
            rendered = (ROOT / 'agents/qa-tester.codex.toml').read_text().replace(
                '@@SKILL_PATH@@', json.dumps(path, ensure_ascii=False)[1:-1])
            self.assertIn(path, tomllib.loads(rendered)['developer_instructions'])

    def test_relative_markdown_links_resolve_and_skill_is_self_contained(self):
        for name in builder.FILES:
            path = ROOT / name
            if path.suffix != '.md':
                continue
            content = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
                if '://' in link or link.startswith('#'):
                    continue
                destination = (path.parent / link.split('#', 1)[0]).resolve()
                self.assertTrue(destination.is_file(), '%s links to missing %s' % (path, link))
                if 'skills/qa-testing/' in name:
                    self.assertTrue(destination.is_relative_to(ROOT / 'skills/qa-testing'),
                                    'Skill-only installation would lose ' + link)

    def test_release_integrity_determinism_checksum_and_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            first, checksum = builder.build('v1.4.0', temp / 'first')
            second, _ = builder.build('v1.4.0', temp / 'second')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(checksum.read_text(), hashlib.sha256(first.read_bytes()).hexdigest()
                             + '  ' + first.name + '\n')
            with zipfile.ZipFile(first) as package:
                self.assertIsNone(package.testzip())
                self.assertEqual(set(package.namelist()),
                                 {'qa-testing-agent-v1.4.0/' + n for n in builder.FILES})
                self.assertFalse(any(n.endswith(('.zip', '.bak', '.pyc')) for n in package.namelist()))
                for name in builder.FILES:
                    self.assertEqual(package.read('qa-testing-agent-v1.4.0/' + name),
                                     (ROOT / name).read_bytes().replace(b'\r\n', b'\n'))

    def test_extracted_release_installs_equivalent_files(self):
        with tempfile.TemporaryDirectory(prefix='release checks ') as temp:
            temp = Path(temp)
            archive, _ = builder.build('v1.4.0', temp / 'dist')
            with zipfile.ZipFile(archive) as package:
                package.extractall(temp / 'extracted')
            project = temp / 'application'
            project.mkdir()
            def run(source):
                result = subprocess.run([sys.executable, str(source / 'install/install.py'),
                    '--target', 'both', '--project', str(project)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
            original = run(ROOT)
            for path in original:
                (project / path).unlink()
            released = run(temp / 'extracted/qa-testing-agent-v1.4.0')
            self.assertEqual(original, released)
            tomllib.loads((project / '.codex/agents/qa-tester.toml').read_text())

    def test_release_allowlist_excludes_gitignored_files(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            result = subprocess.run(['git', 'init', '--quiet', str(temp)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            (temp / '.gitignore').write_bytes((ROOT / '.gitignore').read_bytes())
            result = subprocess.run(['git', '-C', str(temp), 'check-ignore', '--no-index', '--stdin'],
                                    input='\n'.join(builder.FILES) + '\n', capture_output=True, text=True)
            self.assertEqual(result.returncode, 1,
                             'Release includes ignored files or ignore check failed:\n' + result.stdout + result.stderr)

    def test_invalid_version_and_missing_allowlist_source_fail_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            with self.assertRaises(ValueError):
                builder.build('../../oops', temp / 'dist')
            with self.assertRaises(ValueError):
                builder.build('v1.4.0', temp / 'dist', root=temp)
            self.assertFalse((temp / 'dist').exists())


if __name__ == '__main__':
    unittest.main()
