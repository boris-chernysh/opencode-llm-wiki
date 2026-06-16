#!/usr/bin/env python3
import os
import re
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
TAGS_DIR = os.path.join(PROJECT_ROOT, 'agent', 'tags')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'agent', 'config.json')
SOURCE_DIRS = ['atoms', 'daily notes']
EXCLUDED_TAGS = {'need-processing', 'daily-note'}


def load_config():
    global SOURCE_DIRS, EXCLUDED_TAGS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            SOURCE_DIRS = cfg.get('source_dirs', {}).get('tags', SOURCE_DIRS)
            EXCLUDED_TAGS = set(cfg.get('exclude', {}).get('tags', list(EXCLUDED_TAGS)))
        except (json.JSONDecodeError, KeyError):
            pass


def is_valid_tag(tag):
    if re.match(r'^\d', tag):
        return False
    if re.match(r'^[0-9a-fA-F]{3,8}$', tag):
        return False
    return True


def parse_frontmatter_tags(lines):
    tags = set()
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('tags:'):
            value = stripped[5:].strip()
            if value.startswith('[') and value.endswith(']'):
                for t in value[1:-1].split(','):
                    t = t.strip().strip('"').strip("'").strip()
                    if t:
                        tags.add(t)
            elif value:
                tags.add(value)
            else:
                in_list = True
        elif in_list and stripped.startswith('-'):
            t = stripped[1:].strip().strip('"').strip("'").strip()
            if t:
                tags.add(t)
        elif in_list and stripped and not stripped.startswith('-'):
            in_list = False
    return tags


def extract_tags(filepath):
    tags = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    body = content
    fm_lines = []

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            fm_lines = fm_text.split('\n')

    fm_tags = parse_frontmatter_tags(fm_lines)
    tags.update(t for t in fm_tags if is_valid_tag(t))

    body_clean = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    body_clean = re.sub(r'\[\[.*?\]\]', '', body_clean)
    body_tags = set(re.findall(r'#([\w-]+)', body_clean))
    for tag in body_tags:
        if is_valid_tag(tag):
            tags.add(tag)

    return tags


def get_existing_description(index_path):
    if not os.path.exists(index_path):
        return None
    with open(index_path, 'r', encoding='utf-8') as f:
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
    tag_to_files = {}

    for src_dir in SOURCE_DIRS:
        full_dir = os.path.join(PROJECT_ROOT, src_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, dirs, files in os.walk(full_dir):
            for f in files:
                if not f.endswith('.md'):
                    continue
                filepath = os.path.join(root, f)
                rel_path = f
                tags = extract_tags(filepath)
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in EXCLUDED_TAGS:
                        continue
                    if tag_lower not in tag_to_files:
                        tag_to_files[tag_lower] = set()
                    tag_to_files[tag_lower].add(rel_path)

    os.makedirs(TAGS_DIR, exist_ok=True)

    existing_index_files = set(
        f for f in os.listdir(TAGS_DIR) if f.endswith('.md')
    )

    written_files = set()

    for tag, files in sorted(tag_to_files.items()):
        if not files:
            continue
        index_filename = f'{tag}.md'
        written_files.add(index_filename)
        index_path = os.path.join(TAGS_DIR, index_filename)

        description = get_existing_description(index_path)

        if description:
            lines = ['---', f'description: {description}', '---', '', f'# #{tag}', '']
        else:
            lines = [f'# #{tag}', '']
        for f in sorted(files):
            lines.append(f'- [[{f}]]')

        with open(index_path, 'w', encoding='utf-8') as out:
            out.write('\n'.join(lines) + '\n')

    for stale in sorted(existing_index_files - written_files):
        os.remove(os.path.join(TAGS_DIR, stale))
        print(f'Removed stale index: {stale}')

    print(f'Indexed {len(tag_to_files)} tags across {len(written_files)} files.')


if __name__ == '__main__':
    load_config()
    build_index()
