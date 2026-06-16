#!/usr/bin/env python3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
TAGS_DIR = os.path.join(PROJECT_ROOT, 'agent', 'tags')
INDEX_PATH = os.path.join(PROJECT_ROOT, 'agent', 'tags-index.md')

def extract_description(filepath):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.split('\n'):
                if line.startswith('description:'):
                    return line.split(':', 1)[1].strip()
    return None

def generate():
    entries = []

    for f in sorted(os.listdir(TAGS_DIR)):
        if not f.endswith('.md'):
            continue
        tag = f[:-3]
        tag_path = os.path.join(TAGS_DIR, f)
        desc = extract_description(tag_path)
        if desc:
            entries.append((tag, desc))

    lines = ['# Tags index', '']
    for tag, desc in entries:
        lines.append(f'- #{tag} — {desc}')

    with open(INDEX_PATH, 'w', encoding='utf-8') as out:
        out.write('\n'.join(lines) + '\n')

    print(f'Tags index written: {len(entries)} tags.')

if __name__ == '__main__':
    generate()
