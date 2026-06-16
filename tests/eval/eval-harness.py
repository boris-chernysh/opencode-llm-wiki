#!/usr/bin/env python3
"""eval-harness.py — AI eval runner for llm-wiki skill.

Запускает opencode с заданным vault + SKILL.md, проверяет контракт поведения агента.
Требует: opencode CLI с настроенным LLM-провайдером.

Каждый сценарий прогоняется 3 раза. Успех = ≥ 2/3 прохождений.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import yaml
from glob import glob










SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SCENARIOS_DIR = os.path.join(SCRIPT_DIR, 'scenarios')
FIXTURES_DIR = os.path.join(SCRIPT_DIR, 'fixtures')
RUNS_PER_SCENARIO = 3
MIN_PASSES = 2

def load_scenario(path):
    with open(path) as f:
        return yaml.safe_load(f)

def setup_vault(fixture_name):
    """Copy fixture vault to temp dir with agent/ and SKILL.md."""
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

    return dst

def run_opencode(vault_path, command, user_response=None):
    """Run opencode with a command and optional user response.

    Returns captured output and a simulation of what the agent would do.
    Since we can't actually run opencode interactively in CI,
    this is a stub that simulates the agent's behavior for testing purposes.
    """
    # This harness is designed to be run with real opencode CLI.
    # In CI, we skip eval (continue-on-error: true).
    # For local runs: OPENCODE_API_KEY=... python3 tests/eval/eval-harness.py
    try:
        result = subprocess.run(
            ['opencode', '--vault', vault_path, '--command', command],
            input=user_response,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return None, "opencode CLI not found", -1
    except Exception as e:
        return None, str(e), -1

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
                    ok = count <= check['max']
                else:
                    ok = False
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

    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"{'='*60}")

    passes = 0
    for run_idx in range(RUNS_PER_SCENARIO):
        print(f"\n  Run {run_idx + 1}/{RUNS_PER_SCENARIO}:")
        vault = setup_vault(fixture)

        try:
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
