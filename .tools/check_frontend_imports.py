import re
import os
from pathlib import Path

root = Path('frontend/src')
if not root.exists():
    print('No frontend folder found')
    raise SystemExit(1)

import_pattern = re.compile(r"import\s+(?:[^'\"]+from\s+)?['\"](\./[^'\"]+)['\"]")

errors = []

for p in root.rglob('*.js*'):
    text = p.read_text(encoding='utf8')
    for m in import_pattern.finditer(text):
        imp = m.group(1)
        # resolve relative to file
        target = (p.parent / imp)
        found = False
        # possible extensions
        exts = ['.js', '.jsx', '.ts', '.tsx', '.css', '/index.js', '/index.jsx']
        # if import already has extension, try directly
        if target.exists():
            found = True
        else:
            for ext in exts:
                t = Path(str(target) + ext)
                if t.exists():
                    found = True
                    break
        if not found:
            # Now attempt case-sensitive check by listing directory
            rel = os.path.relpath(target, start=root)
            parts = rel.split(os.sep)
            cur = root
            mismatch = False
            for part in parts:
                if part == '.' or part == '':
                    continue
                candidates = [c.name for c in cur.iterdir()]
                if part in candidates:
                    cur = cur / part
                    continue
                # try case-insensitive match
                lower = part.lower()
                match = None
                for c in candidates:
                    if c.lower() == lower:
                        match = c
                        break
                if match:
                    mismatch = True
                    detail = f"Case mismatch: expected '{part}' but actual '{match}' in {cur} (import from {p})"
                    errors.append(detail)
                    # advance
                    cur = cur / match
                else:
                    errors.append(f"Missing import target: {imp} referenced in {p}")
                    mismatch = True
                    break

if not errors:
    print('No missing or mismatched imports found')
else:
    print('Found issues:')
    for e in errors:
        print('-', e)
