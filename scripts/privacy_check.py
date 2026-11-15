"""A narrow release hygiene check; not a substitute for human review."""
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
          r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',
          r'(?i)\b(?:api_key|password|secret)\s*[:=]\s*[\"\'][^\"\']{12,}[\"\']']
errors=[]
for path in root.rglob('*'):
    if not path.is_file() or any(x in path.parts for x in ('.git','__pycache__','data','build','dist')):
        continue
    if path.name=='privacy_check.py':continue
    if path.suffix in ('.sqlite3','.db','.zip','.b64'):
        errors.append(f'Unexpected data/archive: {path.relative_to(root)}');continue
    if path.suffix in ('.png','.jpg','.webp'):continue
    try:source=path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        errors.append(f'Unreviewed binary: {path.relative_to(root)}');continue
    for pattern in patterns:
        if re.search(pattern,source):errors.append(f'Potential sensitive content: {path.relative_to(root)}')
if errors:raise SystemExit('\n'.join(errors))
print('Release hygiene patterns passed. Human review still required.')
