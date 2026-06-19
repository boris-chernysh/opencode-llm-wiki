# Refactor Plan

> **IMPORTANT:** Every step below must be discussed with the user and confirmed before implementation.
> The implementer MUST present the step details, ask for confirmation, and wait for explicit approval before making any changes.

---

## Phase 1: Rename `agent/` → `wiki/` directory

**Goal:** Rename the `agent/` directory to `wiki/` and update ALL references across the entire codebase (~25 files).

### Step 1.1 — Update Python scripts (7 files)
Each script has hardcoded paths like `os.path.join(PROJECT_ROOT, 'agent', ...)`. Change `'agent'` to `'wiki'`.
- `agent/scripts/index-tags.py:9-10`
- `agent/scripts/generate-tags-index.py`
- `agent/scripts/build-links-graph.py`
- `agent/scripts/graph-analyze.py`
- `agent/scripts/graph-suggest-links.py:18-21`
- `agent/scripts/tfidf-suggest.py:20-23`
- `agent/scripts/generate-moc-index.py`

### Step 1.2 — Rename the directory itself
`mv agent/ wiki/`

### Step 1.3 — Update SKILL.md
Replace all `agent/` with `wiki/`:
- Directory tree diagram (lines 17-37)
- Key principle (line 40)
- File schemas (`agent/tags/…`, `agent/data/…`, `agent/research/…`)
- Invariants (`agent/tags/`, `agent/LOG.md`)
- Safety rules tables
- Responsibility matrix
- Command contracts — ALL steps referencing scripts, tags, data, research, moc-index, tags-index, LOG
- Dry run / confirm policy table
- Failure recovery sections
- Anti-noise guardrails
- Config section
- Scripts reference table
- Search by Tag section
- Script dependencies section

### Step 1.4 — Update opencode-commands.json
Replace all `agent/` paths in descriptions and templates (6 commands).

### Step 1.5 — Update .gitignore
Replace `agent/` prefixes with `wiki/`:
```
wiki/tags/
wiki/data/
wiki/research/
wiki/moc-index.md
wiki/tags-index.md
wiki/LOG.md
```

### Step 1.6 — Update setup.sh
Replace all `agent/` references (lines 11-20, 36).

### Step 1.7 — Update README.md
Replace `agent/` → `wiki/` in installation steps and vault structure diagram.

### Step 1.8 — Update all test files (14 files)
Every test file references `agent/` via `os.path.join(TEST_VAULT, 'agent', ...)`. Replace with `'wiki'`.
- `tests/test_index_tags.py`
- `tests/test_tags_index.py`
- `tests/test_graph_build.py`
- `tests/test_graph_analyze.py`
- `tests/test_graph_suggest.py`
- `tests/test_tfidf_suggest.py`
- `tests/test_moc_create.py` → `tests/test_moc_index.py` (renamed in Phase 3)
- `tests/test_analyze_apply.py`
- `tests/test_process_note.py` → `tests/test_ingest.py` (renamed in Phase 2)
- `tests/test_research.py`
- `tests/test_lint.py`
- `tests/test_empty_vault.py`
- `tests/test_no_config.py`

### Step 1.9 — Update tests/run-tests.sh
Line 16: `cp -r "$REPO_ROOT/agent/" "$TEST_VAULT/agent/"` → use `wiki/`.

### Step 1.10 — Update tests/eval/eval-harness.py
Replace all `agent/` paths in the harness.

### Step 1.11 — Create migration script and guide
- `migrate.sh` — automates config migration, command rename, agent/ removal, setup re-run
- `MIGRATION.md` — migration guide (automatic + manual steps, breaking changes, new features)

---

## Phase 2: Rename `wiki-process-note` → `wiki-ingest`

**Goal:** Rename the command from `wiki-process-note` to `wiki-ingest`.

### Step 2.1 — Update SKILL.md
- Log entry format: `wiki-process-note` → `wiki-ingest`
- Destructive ops table: rename entry
- Command contract: rename header and body content
- Confirm policy table: rename entry

### Step 2.2 — Update opencode-commands.json
- Rename key `wiki-process-note` → `wiki-ingest`
- Update template text accordingly

### Step 2.3 — Update README.md
- Command table: `wiki-process-note` → `wiki-ingest`, update description

### Step 2.4 — Rename and update test file
- `mv tests/test_process_note.py tests/test_ingest.py`
- Update docstring and internal references

### Step 2.5 — Update tests/eval/eval-harness.py
- Rename command key in embedded opencode.json config

### Step 2.6 — Update eval scenario
- `tests/eval/scenarios/process-note-limit.yaml`: `command: wiki-process-note` → `wiki-ingest`

---

## Phase 3: `wiki-moc` → Read-Only Index Only

**Goal:** Remove MOC note creation flow. `wiki-moc` becomes read-only — it only generates `moc-index.md` via scripts and reports hub rankings.

### Step 3.1 — Update SKILL.md
- Scope: "MOC hub discovery/creation" → "MOC hub discovery"
- Invariants: remove "Every MOC note created by wiki-moc references notes…"
- Destructive ops table: REMOVE `wiki-moc` row
- Non-destructive ops table: ADD `wiki-moc` row ("Builds MOC index, never touches vault notes")
- Hard guardrails: remove MOC creation guardrail (cluster size limits for creation)
- Responsibility matrix: remove "Create MOC notes in atoms/" row
- Command contract: rewrite to be read-only:
  - Step 1: Run `build-links-graph.py && graph-analyze.py && generate-moc-index.py`
  - Step 2: Read `graph-stats.md` and `moc-index.md`
  - Step 3: Report hub rankings, cluster sizes, top tags to user
- Dry run table: `wiki-moc` → preview: No, confirm: No (safe)
- Failure recovery: remove "crashes during wiki-moc MOC creation" section
- Anti-noise guardrails: adjust MOC section (no creation limits, only index limits)

### Step 3.2 — Update opencode-commands.json
- Rewrite `wiki-moc` template: remove cluster identification, preview, creation, confirmation steps. Keep only: run scripts → read results → report → log.

### Step 3.3 — Update README.md
- "Поиск/создание MOC-хабов" → "Поиск MOC-хабов (read-only)"

### Step 3.4 — Update test files
- Update `tests/test_moc_index.py`: ensure docstring says "Test wiki-moc index generation (read-only)", update paths from `'agent'` to `'wiki'` if not already done in Phase 1
- Delete `tests/test_moc_create.py` (MOC creation test is no longer relevant)

### Step 3.5 — Update tests/eval/eval-harness.py
- Simplify `wiki-moc` eval template (no subtask, no confirm step)

---

## Phase 4: `wiki-analyze` — Configurable Exclude Tags

**Goal:** Add `exclude.tags_from_analyze` config field so the LLM filtering step uses config instead of hardcoded `#daily-note`.

### Step 4.1 — Update wiki/config.json
Add `"tags_from_analyze": ["daily-note"]` inside the `exclude` block:
```json
"exclude": {
    "tags": ["need-processing", "daily-note"],
    "tags_from_analyze": ["daily-note"],
    "dirs_from_suggestions": ["daily notes"],
    "dirs_from_graph": []
}
```

### Step 4.2 — Update SKILL.md
- Config schema: add `tags_from_analyze` field
- Anti-noise guardrails: mention `exclude.tags_from_analyze` for analyze
- Command contract step 3 (filtering): replace hardcoded `#daily-note` with reference to `wiki/config.json → exclude.tags_from_analyze`

### Step 4.3 — Update opencode-commands.json
- wiki-analyze template: step 3 filtering should reference `exclude.tags_from_analyze` from config instead of hardcoded `#daily-note`

---

## Phase 5: `wiki-reindex` — Date-Based Index

**Goal:** `wiki-reindex` creates a chronological index organized by year/month, with LLM-generated monthly summaries.

### Step 5.1 — Create new script: `wiki/scripts/index-dates.py`
- Scans `atoms/` for notes with `YYYYMMDDHHMM` prefix
- Scans `daily notes/` for date-based filenames
- Groups by year and month
- Creates directory: `wiki/dates/YYYY/`
- Writes `wiki/dates/YYYY/YYYY-MM.md` with:
  ```markdown
  ---
  description:
  ---

  # YYYY-MM

  - [[202401010930 заметка.md]]
  - [[202401021045 другая.md]]
  ```
- Notes sorted chronologically within each month
- Idempotent — regenerates all date files on each run

### Step 5.2 — Update SKILL.md
- Directory diagram: add `dates/YYYY/YYYY-MM.md` tree
- Key principle: add `dates/` to ephemeral artifacts
- wiki-reindex command contract: add step to run `index-dates.py`, then read monthly files — for any MISSING `description`, generate a short Russian summary (1-2 sentences) about that month. Do NOT overwrite existing descriptions.
- Scripts reference table: add `index-dates.py` row

### Step 5.3 — Update opencode-commands.json
- wiki-reindex template: add `index-dates.py` to script chain, add description generation step for monthly files

### Step 5.4 — Update .gitignore
- Add `wiki/dates/` to gitignored paths

### Step 5.5 — Update tests/eval/eval-harness.py
- wiki-reindex eval template: add `index-dates.py`

### Step 5.6 — Create test: `tests/test_dates_index.py`
- Runs `index-dates.py` against fixture vault
- Verifies `wiki/dates/` directory structure
- Verifies monthly files contain expected note entries

---

## Phase 6: Final Verification

### Step 6.0 — Update version
Bump `pyproject.toml` line 3: `version = "0.2.0"`.

### Step 6.1 — Run tests
```bash
./tests/run-tests.sh
```
All tests must pass.

### Step 6.2 — Lint Python code
```bash
ruff check wiki/scripts/ tests/
```

### Step 6.3 — Manual smoke test
- Run `./setup.sh /tmp/test-smoke-vault --copy`
- Verify `wiki/` directory structure (not `agent/`)
- Verify all commands listed correctly

---

## Summary of All Changes

| # | Change | Type | ~Files touched |
|---|--------|------|---------------|
| 1 | `agent/` → `wiki/` | Breaking rename | 25 |
| 2 | `wiki-process-note` → `wiki-ingest` | Breaking rename | 5 |
| 3 | `wiki-moc` read-only | Behavior change | 4 |
| 4 | analyze exclude config | Additive config | 3 |
| 5 | date-based index | New script + integration | 6 |
| 6 | Migration automation | New files | 2 (`migrate.sh`, `MIGRATION.md`) |
