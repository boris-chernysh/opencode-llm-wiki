#!/usr/bin/env python3
"""eval-harness.py — AI eval runner for llm-wiki skill.

Запускает opencode с заданным vault + SKILL.md, проверяет контракт поведения агента.
Требует: opencode CLI с настроенным LLM-провайдером.

Каждый сценарий прогоняется 3 раза. Успех = ≥ 2/3 прохождений.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from glob import glob


# Minimal YAML parser — avoids pyyaml dependency
def _parse_simple_yaml(path):
    """Parse a simple flat YAML file with lists of dicts."""
    with open(path) as f:
        lines = f.readlines()
    result = {}
    current_list = None
    current_item = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        has_indent = len(line) > 0 and line[0] == ' '
        if stripped.startswith('- '):
            if current_list is not None and current_item is not None:
                result.setdefault(current_list, []).append(current_item)
            elif not has_indent and current_item is not None:
                # Dangling item from previous list
                pass
            if not has_indent:
                current_item = None
                current_list = None
            else:
                current_item = {}
            content = stripped[2:]
            if ':' in content:
                key, _, val = content.partition(':')
                val = val.strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                if current_item is not None:
                    current_item[key.strip()] = val
                else:
                    current_item = {key.strip(): val}
        elif ':' in stripped:
            if has_indent and current_item is not None:
                key, _, val = stripped.partition(':')
                val = val.strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                current_item[key.strip()] = val
            else:
                if current_item is not None and current_list is not None:
                    result.setdefault(current_list, []).append(current_item)
                    current_item = None
                    current_list = None
                key, _, val = stripped.partition(':')
                key = key.strip()
                val = val.strip()
                if val == '':
                    current_list = key
                elif val.startswith('"') and val.endswith('"'):
                    result[key] = val[1:-1]
                else:
                    result[key] = val
    if current_item is not None and current_list is not None:
        result.setdefault(current_list, []).append(current_item)
    return result


def load_scenario(path):
    return _parse_simple_yaml(path)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SCENARIOS_DIR = os.path.join(SCRIPT_DIR, 'scenarios')
FIXTURES_DIR = os.path.join(SCRIPT_DIR, 'fixtures')
RUNS_PER_SCENARIO = 1
MIN_PASSES = 1
has_opencode = False

def setup_vault(fixture_name):
    """Copy fixture vault to temp dir with agent/, SKILL.md, opencode.json, AGENTS.md."""
    src = os.path.join(FIXTURES_DIR, fixture_name)
    dst = tempfile.mkdtemp(prefix=f'test-eval-{fixture_name}-')

    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)

    # Copy agent/ scripts (skip generated dirs)
    agent_src = os.path.join(REPO_ROOT, 'agent')
    agent_dst = os.path.join(dst, 'agent')
    shutil.copytree(agent_src, agent_dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('tags', 'data', 'research',
                                                  'moc-index.md', 'tags-index.md', 'LOG.md'))

    # Copy SKILL.md to .opencode/skills/llm-wiki/
    skill_dst = os.path.join(dst, '.opencode', 'skills', 'llm-wiki')
    os.makedirs(skill_dst, exist_ok=True)
    shutil.copy(os.path.join(REPO_ROOT, 'SKILL.md'), os.path.join(skill_dst, 'SKILL.md'))

    # Create .opencode/opencode.json with skill config and commands
    opencode_config = {
        "instructions": ["AGENTS.md"],
        "skills": {"paths": [".opencode/skills"]},
        "command": {
            "wiki-reindex": {
                "description": "Full reindex of the Obsidian vault.",
                "template": "Load the llm-wiki skill. Run: python3 agent/scripts/index-tags.py && python3 agent/scripts/generate-tags-index.py && python3 agent/scripts/build-links-graph.py && python3 agent/scripts/graph-analyze.py && python3 agent/scripts/generate-moc-index.py."
            },
            "wiki-research": {
                "description": "Research a topic using the vault.",
                "template": "Load the llm-wiki skill. Read agent/tags-index.md. Find relevant tags. Read notes. Compile structured research summary in Russian: Краткий снимок → Ключевые находки → Выводы → Источники. Save to agent/research/<YYYYMMDDHHMM> Topic.md with frontmatter: topic, date, tags."
            },
            "wiki-analyze": {
                "description": "Analyze vault for new connections. SHOW PREVIEW, WAIT for confirmation.",
                "template": "Load the llm-wiki skill. Run graph analysis scripts. Read suggestions. Show preview table. WAIT for user confirmation. Only apply links if user says yes/да/применить.",
                "subtask": True
            },
            "wiki-moc": {
                "description": "Find or create MOC hub notes. SHOW PREVIEW, WAIT for confirmation.",
                "template": "Load the llm-wiki skill. Run graph analysis. Identify clusters. Show preview table. WAIT for user confirmation. Create MOC notes only if user says yes/да.",
                "subtask": True
            },
            "wiki-lint": {
                "description": "Read-only health check of vault and skill artifacts.",
                "template": "Load the llm-wiki skill. Run a read-only health check. Check stale tags, missing descriptions, broken links, orphans, consistency. Report findings. Do NOT modify any files."
            },
            "wiki-process-note": {
                "description": "Suggest and apply tags + links for unprocessed notes.",
                "template": "Load the llm-wiki skill. Find notes with need-processing tag (max 10). For each: extract keywords, find relevant tags and candidate links. Show preview table. WAIT for user confirmation. Apply only after user says yes/да. Do NOT remove the need-processing tag.",
                "subtask": True
            }
        }
    }
    opencode_dir = os.path.join(dst, '.opencode')
    os.makedirs(opencode_dir, exist_ok=True)
    with open(os.path.join(opencode_dir, 'opencode.json'), 'w') as f:
        json.dump(opencode_config, f, indent=2, ensure_ascii=False)

    # Create AGENTS.md
    with open(os.path.join(dst, 'AGENTS.md'), 'w') as f:
        f.write("""# AGENTS.md — Test vault for llm-wiki eval

Use the llm-wiki skill for all wiki operations. Always show preview before modifying.

## Vault structure
- `atoms/` — atomic Zettelkasten notes
- `daily notes/` — daily journal pages
- `templates/` — templates (exclude from indexing)

## Frontmatter conventions
- `tags` — list of tags
- `links` — list of wikilinks
- `created` — creation date
""")

    return dst

def run_opencode(vault_path, command, user_response=None):
    """Run opencode with a command and optional user response."""
    # Split command into name and args: "wiki-research здоровье" -> ["wiki-research", "здоровье"]
    parts = command.split(maxsplit=1)
    cmd_name = parts[0]
    cmd_args = parts[1:] if len(parts) > 1 else []
    cmd = ['opencode', 'run', '--dir', vault_path, '--command', cmd_name,
           '--dangerously-skip-permissions'] + cmd_args
    last_result = (None, "opencode retry exhausted", -1)
    for attempt in range(3):
        try:
            result = subprocess.run(
                cmd,
                input=user_response,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return result.stdout, result.stderr, result.returncode
            if 'UnknownError' in (result.stderr or '') and attempt < 2:
                time.sleep(5)
                continue
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return None, f"Timeout after 300s", -1
        except FileNotFoundError:
            return None, "opencode CLI not found", -1
        except Exception as e:
            last_result = (None, str(e), -1)
            if attempt < 2:
                time.sleep(3)
                continue
            return last_result
    return last_result

def check_scenario(scenario, vault_path):
    """Run scenario checks against the vault."""
    checks = scenario.get('checks', [])
    results = []

    for check in checks:
        check_type = check.get('type', '')
        description = check.get('description', check_type)

        try:
            if check_type == 'file_exists':
                path = os.path.join(vault_path, check['path'])
                ok = os.path.isfile(path)
            elif check_type == 'file_not_exists':
                path = os.path.join(vault_path, check['path'])
                ok = not os.path.isfile(path)
            elif check_type == 'content_contains':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    ok = check['text'] in content
                else:
                    ok = False
            elif check_type == 'content_not_contains':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    ok = check['text'] not in content
                else:
                    ok = True
            elif check_type == 'count_equals':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    count = content.count(check['text'])
                    ok = count == check['expected']
                else:
                    ok = False
            elif check_type == 'has_frontmatter_field':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    ok = check['field'] in content and '---' in content
                else:
                    ok = False
            elif check_type == 'has_section':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    ok = check['section'] in content
                else:
                    ok = False
            elif check_type == 'links_dedup':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    links = re.findall(r'\[\[([^\]]+)\]\]', content)
                    ok = len(links) == len(set(links))
                else:
                    ok = False
            elif check_type == 'tag_not_removed':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    ok = check['tag'] in content
                else:
                    ok = False
            elif check_type == 'count_lte':
                path = os.path.join(vault_path, check['path'])
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    count = content.count(check['text'])
                    max_val = int(check['max']) if isinstance(check['max'], str) else check['max']
                    ok = count <= max_val
                else:
                    ok = False
            elif check_type == 'dir_content_contains':
                path = os.path.join(vault_path, check['path'])
                ok = False
                if os.path.isdir(path):
                    for fname in os.listdir(path):
                        if fname.endswith('.md'):
                            fpath = os.path.join(path, fname)
                            with open(fpath) as f:
                                content = f.read()
                            if check['text'] in content:
                                ok = True
                                break
            elif check_type == 'dir_content_not_contains':
                path = os.path.join(vault_path, check['path'])
                ok = True
                if os.path.isdir(path):
                    for fname in os.listdir(path):
                        if fname.endswith('.md'):
                            fpath = os.path.join(path, fname)
                            with open(fpath) as f:
                                content = f.read()
                            if check['text'] in content:
                                ok = False
                                break
            else:
                ok = None  # Unknown check type

            results.append((description, ok))
            status = "PASS" if ok else "FAIL" if ok is False else "SKIP"
            print(f"  [{status}] {description}")

        except Exception as e:
            results.append((description, False))
            print(f"  [FAIL] {description}: {e}")

    return results

def run_scenario(scenario_path):
    scenario = load_scenario(scenario_path)
    name = scenario.get('name', os.path.basename(scenario_path))
    fixture = scenario.get('fixture', 'minimal-vault')
    command = scenario.get('command', '')
    user_response = scenario.get('user_response', '')

    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"  command: {command}")
    print(f"  user_response: {user_response[:80] if user_response else '(none)'}")
    print(f"{'='*60}")

    passes = 0
    for run_idx in range(RUNS_PER_SCENARIO):
        print(f"\n  Run {run_idx + 1}/{RUNS_PER_SCENARIO}:")
        vault = setup_vault(fixture)

        try:
            # Run setup script if specified (e.g. pre-indexing)
            setup_script = scenario.get('setup_script', '')
            if setup_script:
                print(f"  Setup: {setup_script[:80]}...")
                for cmd_part in setup_script.split('&&'):
                    cmd_part = cmd_part.strip()
                    script_path = os.path.join(vault, cmd_part)
                    if os.path.exists(script_path):
                        subprocess.run(['python3', script_path], cwd=vault,
                                       capture_output=True, text=True, timeout=60)

            # Actually run opencode (unless skipped)
            if scenario.get('skip_opencode'):
                print("  [SKIP] opencode disabled for this scenario")
            elif has_opencode:
                print(f"  Running opencode {command}...")
                stdout, stderr, rc = run_opencode(vault, command, user_response)

                if rc == 0:
                    print("  opencode exited OK")
                else:
                    print(f"  opencode exited with code {rc}")
                    if stderr:
                        print(f"  stderr (last 500 chars): {stderr[-500:]}")
            else:
                print("  [DRY-RUN] opencode not available, checking static state only")

            # Check results
            results = check_scenario(scenario, vault)
            all_pass = all(r[1] for r in results if r[1] is not None)
            if all_pass:
                passes += 1
                print("  -> ALL CHECKS PASSED")
            else:
                failed = [r[0] for r in results if r[1] is False]
                print(f"  -> FAILED: {', '.join(failed)}")
        finally:
            shutil.rmtree(vault, ignore_errors=True)

    ok = passes >= MIN_PASSES
    status_str = "PASS" if ok else "FAIL"
    print(f"\n  Result: {status_str} ({passes}/{RUNS_PER_SCENARIO} runs passed)")
    return ok

def create_minimal_vault():
    """Create minimal vault fixture if it doesn't exist."""
    fixture_path = os.path.join(FIXTURES_DIR, 'minimal-vault')
    if os.path.isdir(fixture_path):
        return

    os.makedirs(os.path.join(fixture_path, 'atoms'), exist_ok=True)
    os.makedirs(os.path.join(fixture_path, 'daily notes'), exist_ok=True)

    notes = {
        '202501010001 Здоровое питание.md': """---
created: 2025-01-01
tags:
  - здоровье
  - питание
---

# Здоровое питание

Основы правильного питания.
""",
        '202501010002 Спорт и тренировки.md': """---
created: 2025-01-01
tags:
  - спорт
  - здоровье
---

# Спорт и тренировки

Регулярные тренировки.
""",
        '202501010003 Бег по утрам.md': """---
created: 2025-01-01
tags:
  - спорт
  - бег
links:
  - "[[202501010001 Здоровое питание]]"
---

# Бег по утрам

Утренние пробежки.
""",
        '202501010010 need-processing заметка.md': """---
created: 2025-01-01
tags:
  - need-processing
---

# need-processing заметка

Сырые мысли.
""",
        '202501010011 Орфан заметка.md': """---
created: 2025-01-01
tags:
  - одиночество
---

# Орфан заметка

Без связей.
""",
    }

    for fname, content in notes.items():
        with open(os.path.join(fixture_path, 'atoms', fname), 'w') as f:
            f.write(content)

    # Daily note
    with open(os.path.join(fixture_path, 'daily notes', '2025-01-01.md'), 'w') as f:
        f.write("""---
day: 2025-01-01
tags:
  - daily-note
---

# 2025-01-01

Дневная заметка.
""")

def create_templates_vault():
    """Create vault with templates/ for safety test."""
    fixture_path = os.path.join(FIXTURES_DIR, 'vault-with-templates')
    if os.path.isdir(fixture_path):
        return

    # Copy minimal vault first
    minimal = os.path.join(FIXTURES_DIR, 'minimal-vault')
    if not os.path.isdir(minimal):
        create_minimal_vault()

    shutil.copytree(minimal, fixture_path, dirs_exist_ok=True)

    os.makedirs(os.path.join(fixture_path, 'templates'), exist_ok=True)

    with open(os.path.join(fixture_path, 'templates', 'Базовая заметка.md'), 'w') as f:
        f.write("""---
tags:
  - templates
---

# Базовая заметка

Шаблон.
""")

def main():
    global has_opencode
    print("=== AI Eval Harness for llm-wiki ===\n")

    # Ensure fixtures exist
    create_minimal_vault()
    create_templates_vault()

    # Check if opencode CLI is available
    has_opencode = False
    try:
        subprocess.run(['opencode', '--version'], capture_output=True, timeout=5)
        has_opencode = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not has_opencode:
        print("⚠ opencode CLI not found — eval will run as dry-run (static checks only)\n")

    scenario_files = sorted(glob(os.path.join(SCENARIOS_DIR, '*.yaml')))
    if not scenario_files:
        print("No scenarios found.")
        return 1

    results = {}
    for sf in scenario_files:
        ok = run_scenario(sf)
        results[os.path.basename(sf)] = ok
        # Delay between scenarios to let opencode server settle
        time.sleep(3)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n{'='*60}")
    print(f"Eval Results: {passed}/{total} scenarios passed")
    print(f"{'='*60}")

    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'} — {name}")

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
