#!/usr/bin/env python3
"""Generate date-based index files grouped by year/month.

Scans atoms/ for notes with YYYYMMDDHHMM prefix and daily notes/
for date-based filenames, groups by year and month,
and writes wiki/dates/YYYY/YYYY-MM.md files.

Idempotent — regenerates all date files on each run.
"""

import json
import os
import re
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATES_DIR = os.path.join(PROJECT_ROOT, 'wiki', 'dates')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'wiki', 'config.json')

ATOM_PATTERN = re.compile(r'^(\d{4})(\d{2})(\d{2})\d{4}')
DAILY_PATTERN = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')

SOURCE_DIRS = ['atoms', 'daily notes']


def load_config():
    global SOURCE_DIRS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            SOURCE_DIRS = cfg.get('source_dirs', {}).get('dates', SOURCE_DIRS)
        except (json.JSONDecodeError, KeyError):
            pass


def get_existing_description(index_path):
    if not os.path.exists(index_path):
        return None
    with open(index_path, encoding='utf-8') as f:
        content = f.read()
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.split('\n'):
                if line.startswith('description:'):
                    return line.split(':', 1)[1].strip()
    return None


def build_index():
    load_config()

    year_month = defaultdict(list)

    for src_dir in SOURCE_DIRS:
        full_dir = os.path.join(PROJECT_ROOT, src_dir)
        if not os.path.isdir(full_dir):
            continue
        for fname in os.listdir(full_dir):
            if not fname.endswith('.md'):
                continue

            if src_dir == 'atoms':
                m = ATOM_PATTERN.match(fname)
                if m:
                    year = m.group(1)
                    month = m.group(2)
                    key = (year, month)
                    year_month[key].append(fname)
            elif src_dir == 'daily notes':
                m = DAILY_PATTERN.match(fname)
                if m:
                    year = m.group(1)
                    month = m.group(2)
                    key = (year, month)
                    year_month[key].append(fname)

    for key in sorted(year_month.keys()):
        year, month = key
        dir_path = os.path.join(DATES_DIR, year)
        os.makedirs(dir_path, exist_ok=True)
        index_path = os.path.join(dir_path, f'{year}-{month}.md')

        description = get_existing_description(index_path)

        lines = []
        if description:
            lines.extend(['---', f'description: {description}', '---', ''])
        else:
            lines.extend(['---', 'description:', '---', ''])

        lines.append(f'# {year}-{month}')
        lines.append('')

        for fname in sorted(year_month[key]):
            lines.append(f'- [[{fname}]]')

        with open(index_path, 'w', encoding='utf-8') as out:
            out.write('\n'.join(lines) + '\n')

    # Remove stale directories
    if os.path.isdir(DATES_DIR):
        for ydir in os.listdir(DATES_DIR):
            ypath = os.path.join(DATES_DIR, ydir)
            if not os.path.isdir(ypath):
                continue
            for df in os.listdir(ypath):
                if df.endswith('.md') and os.path.isfile(os.path.join(ypath, df)):
                    y, m = df[:-3].split('-')
                    if (y, m) not in year_month:
                        os.remove(os.path.join(ypath, df))
                        print(f'Removed stale date index: {ydir}/{df}')

    total_files = sum(len(v) for v in year_month.values())
    print(f'Date index written: {len(year_month)} months, {total_files} notes.')


if __name__ == '__main__':
    build_index()
