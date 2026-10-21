"""Verify the clean package's recorded inventory, hashes, markers and local links.

Standard library only; reads only the explicit package root; never installs/runs imports.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'PACKAGE-MANIFEST.json').read_text())
    expected = manifest['sha256']
    required = {'LICENSE', 'PROVENANCE.json', 'plugin.json', 'README.md',
                'skills/workflow-portable/SKILL.md',
                'skills/workflow-portable/references/diagrams/ORIGINAL-TEMPLATES-LICENSE.txt'}
    if not required <= set(expected):
        raise ValueError('Missing required license/provenance/core files')
    files = [p for p in root.rglob('*') if p.is_file() or p.is_symlink()]
    actual = {p.relative_to(root).as_posix() for p in files}
    if actual != set(expected) | {'PACKAGE-MANIFEST.json'}:
        raise ValueError('Unlisted or missing package files')
    bad = re.compile(r'(?i)(/Users/|[A-Z]:\\Users\\|plugins_[a-f0-9]{20,}|pluginrel_|drive\.google\.com/(?:file|drive)/|[\w.+-]+@[\w.-]+\.[A-Z]{2,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})')
    for p in files:
        name = p.relative_to(root).as_posix()
        q = PurePosixPath(name)
        if p.is_symlink() or any(x in ('.git', '__pycache__', 'project-experience') for x in q.parts):
            raise ValueError('Forbidden path or symlink')
        raw = p.read_bytes()
        if name in expected and hashlib.sha256(raw).hexdigest() != expected[name]:
            raise ValueError('Hash mismatch: '+name)
        text = raw.decode('utf-8')
        # The scanner's own pattern literals intentionally name forbidden markers.
        if name != 'verify_package.py' and bad.search(text):
            raise ValueError('Private marker: '+name)
        if p.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if re.match(r'^[a-z]+:',link) or link.startswith('#'):
                    continue
                target = (p.parent/link.split('#')[0]).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    raise ValueError('Broken/escaping link: '+name)
    return {'passed': True, 'files': len(files), 'scope': 'recorded inventory, hashes, known markers and local links; not absolute privacy/security proof'}


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else '.')))
