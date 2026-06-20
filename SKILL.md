# Skill: llm-wiki

LLM Wiki — personal skill for Obsidian vault knowledge management: tag indexing, graph analysis, link suggestions, MOC hubs, research, and health checks. Designed for a single-owner Zettelkasten+Dataview vault with Russian-language content.

## Purpose

Enable an AI agent to navigate, analyze, and safely maintain an Obsidian vault. Destructive actions (modifying notes, creating files) always require explicit user confirmation after a preview.

## Scope

**In scope:** tag index, consolidated tag index, graph build/analysis, link suggestions (graph + TF-IDF), MOC hub discovery (read-only), topic research, health/lint checks, note tagging/linking.

**Out of scope:** external databases, vector stores, embeddings, real-time sync, full-text search engine, multi-user collaboration.

## Directory Contracts

```
wiki/                          # Skill root — all artifacts are regenerable
├── config.json                 # Thresholds, limits, exclusions (created with defaults)
├── tags/                       # Per-tag index files: tags/<tagname>.md
├── tags-index.md               # Consolidated tag index with descriptions
├── moc-index.md                # MOC hub index
├── data/
│   ├── links-graph.json        # Adjacency graph + node metadata + clusters
│   ├── graph-stats.md          # Human-readable graph analysis report
│   ├── link-suggestions.md     # Graph-based link suggestions
│   └── semantic-suggestions.md # TF-IDF based link suggestions
├── research/                   # Research outputs: YYYYMMDDHHMM Topic.md
├── dates/                       # Date-based index: dates/YYYY/YYYY-MM.md
├── LOG.md                       # Operation log
└── scripts/                    # Python 3 stdlib scripts
    ├── index-tags.py
    ├── generate-tags-index.py
    ├── build-links-graph.py
    ├── graph-analyze.py
    ├── graph-suggest-links.py
    ├── tfidf-suggest.py
    └── generate-moc-index.py
    └── index-dates.py
```

**Key principle:** `wiki/` artifacts are ephemeral — fully regenerable from vault source of truth (`atoms/`, `daily notes/`). `dates/` adds a chronological index view. If anything breaks, delete affected files and re-run scripts.

## File Schemas

### Tag index file: `wiki/tags/<tagname>.md`

```markdown
---
description: Одно предложение на русском, описывающее что объединяет заметки с этим тегом. Без двоеточий.
---

# #tagname

- [[filename1.md]]
- [[filename2.md]]
```

- Filename is lowercase tag name.
- `description` — single Russian sentence, no colons, no markdown.
- Wikilinks sorted alphabetically.

### links-graph.json

```json
{
  "nodes": {
    "filename.md": {
      "tags": ["tag1"],
      "links_out": ["target.md"],
      "links_in": ["source.md"],
      "degree_out": 1,
      "degree_in": 0,
      "cluster": 42,
      "path": "atoms/filename.md",
      "source_dir": "atoms"
    }
  },
  "edges": [["source.md", "target.md"]],
  "stats": {
    "total_nodes": 100,
    "total_edges": 200,
    "orphan_nodes": 10,
    "tags_indexed": 30,
    "avg_degree": 2.0
  },
  "clusters": {
    "42": ["file1.md", "file2.md"]
  }
}
```

### Link suggestion (in suggestions files)

| Field | Type | Description |
|-------|------|-------------|
| `a` | string | Source note filename |
| `b` | string | Target note filename |
| `common` | int | Shared neighbours count (graph only) |
| `jaccard` | float | Jaccard index (graph only) |
| `similarity` | float | Cosine similarity (TF-IDF only) |
| `shared_tags` | list | Tags present in both notes |
| `tags_a`, `tags_b` | list | All tags of each note |

### Research output: `wiki/research/<YYYYMMDDHHMM> Topic.md`

```yaml
---
topic: "Exact research topic"
date: "YYYY-MM-DD"
tags:
  - used_tag1
  - used_tag2
---
```

Body structure:
1. `# Topic Title`
2. `## Краткий снимок` — 2-3 sentence situation summary
3. `## Ключевые находки` — bullet list of findings with `[[wikilinks]]`
4. `## Выводы` — 2-3 actionable conclusions
5. `## Источники` — list of notes consulted as wikilinks

### Log entry: `wiki/LOG.md`

```markdown
## YYYY-MM-DD HH:MM

**Command:** wiki-reindex | wiki-research | wiki-analyze | wiki-lint | wiki-ingest

Описание задачи и выполненных изменений. Конкретные цифры: сколько тегов, узлов, связей, заметок.

### Changes
- atoms/file1.md: added links: [[target.md]]
- atoms/file2.md: added links: [[target2.md]]
```

- New entries **prepended** (newest at top).
- `### Changes` section **required** for any vault-modifying command.
- Each line: exact file path + what was modified.

## Invariants

After any successful operation these hold:

1. Every non-excluded tag in vault → index file in `wiki/tags/`.
2. No stale index files (tag vanished from vault → index deleted).
3. Every graph node → existing `.md` in vault. Every edge → wikilink in source note.
4. Every vault-modifying operation → logged in `wiki/LOG.md` with `### Changes`.
5. Every tag index file has `description` frontmatter field (may be blank, but present).

## Safety Rules

### Destructive operations — require user confirmation

| Operation | What it modifies | Gate |
|---|---|---|
| `wiki-analyze` apply links | `links:` in vault notes | **Preview → confirm** |
| `wiki-ingest` apply | `tags:`, `links:` in vault notes, `wiki/tags/*.md` | **Preview → confirm** |
| Mass description update | `wiki/tags/*.md` frontmatter | Auto only for **missing** descriptions, batch-limited |

### Non-destructive operations — automatic

| Operation | What it does |
|---|---|
| `wiki-reindex` scripts | Rebuilds `wiki/` artifacts, never touches vault notes |
| `wiki-research` | Reads vault, writes only to `wiki/research/` |
| `wiki-lint` | Read-only analysis |

### Hard guardrails

- **Never** delete or modify files in `atoms/` or `daily notes/` without explicit user confirmation.
- **Never** touch `templates/`, `.obsidian/`, `.trash/`, `.smtcmp_json_db/`.
- **Never** add duplicate `links:` entries (dedup before writing).
- **Never** apply more than `max_suggestions_to_validate` link suggestions per `wiki-analyze` run.

## Responsibility Matrix

| Action | Who | Auto? |
|---|---|---|
| Build tag indexes | `index-tags.py` | Yes |
| Build link graph | `build-links-graph.py` | Yes |
| Analyze graph | `graph-analyze.py` | Yes |
| Generate link suggestions | `graph-suggest-links.py`, `tfidf-suggest.py` | Yes |
| Generate MOC index | `generate-moc-index.py` | Yes |
| Consolidate tag index | `generate-tags-index.py` | Yes |
| Generate tag descriptions | Agent (LLM) | Yes, only for missing, batch-limited |
| **Suggest & apply tags/links** | Agent | **NO — requires confirmation** |
| **Modify note `links:`** | Agent | **NO — requires confirmation** |
| Search tags, read notes | Agent | Yes |
| Research a topic | Agent | Yes |
| Lint / health check | Agent | Yes (read-only) |

## Command Contracts

### `wiki-reindex`

Full rebuild of all agent artifacts from vault source.

**Steps:**
1. Run: `python3 wiki/scripts/index-tags.py && python3 wiki/scripts/generate-tags-index.py && python3 wiki/scripts/build-links-graph.py && python3 wiki/scripts/graph-analyze.py && python3 wiki/scripts/generate-moc-index.py && python3 wiki/scripts/index-dates.py`
2. Read tag index files in `wiki/tags/`.
3. For any tag index file **missing** a `description` field — generate one. Do NOT overwrite existing descriptions.
4. Re-run `generate-tags-index.py` to update consolidated index.
5. Read monthly date index files in `wiki/dates/`. For any monthly file **missing** a `description` field — generate a short Russian summary (1-2 sentences) about that month's notes. Do NOT overwrite existing descriptions.
6. Read `wiki/data/graph-stats.md` and `wiki/moc-index.md`. Report hub rankings, cluster sizes, and top tags to user.
7. Log to `wiki/LOG.md`.

**Safety:** Read-only on vault. All writes go to `wiki/`.
**Duration:** 5–30 seconds for a ~2000-note vault.

### `wiki-research <topic>`

Research a topic using tag indices.

**Steps:**
1. Read `wiki/tags-index.md`. Find relevant tags by keyword match on tag names and descriptions.
2. For each relevant tag, read `wiki/tags/<tag>.md` to discover connected notes.
3. Read notes.
4. Compile structured research summary following research output schema.
5. Save to `wiki/research/<YYYYMMDDHHMM> Topic.md`.
6. Return summary to user and log.

**Safety:** Read-only on vault. Writes only to `wiki/research/`.

### `wiki-analyze`

Find and validate missing Zettelkasten links between notes.

**Steps:**
1. Run: `python3 wiki/scripts/build-links-graph.py && python3 wiki/scripts/graph-suggest-links.py && python3 wiki/scripts/tfidf-suggest.py`
2. Read `link-suggestions.md` and `semantic-suggestions.md`.
3. **FILTER suggestions:**
   - Exclude pairs where BOTH notes are from `daily notes/` source dir.
   - Exclude pairs where either note has ONLY tags from `exclude.tags_from_analyze` (config, e.g. `#daily-note`).
   - Exclude graph suggestions with `jaccard == 0` AND no `shared_tags`.
   - Exclude semantic suggestions with `similarity < min_tfidf_similarity` (config).
4. Take top `max_suggestions_to_validate` (default 20) from filtered list.
5. **VALIDATION (read-only):** For each suggestion, read both notes. Assess semantic relevance. Classify each as accepted or rejected with one-sentence reason in Russian.
6. **PREVIEW — present to user:**

   ```
   | # | Источник | Цель | Тип | Причина |
   |---|----------|------|-----|---------|
   | 1 | [[note_a]] | [[note_b]] | graph | 3 общих соседа, тема: здоровье |
   | 2 | [[note_c]] | [[note_d]] | tfidf | similarity 0.45, тема: управление |
   ```
   **WAIT for user confirmation.** Do not apply without explicit approval.

7. **APPLY (only after confirmation):** For each accepted suggestion:
   - Read source note frontmatter.
   - If `links:` exists as list → append target (if not already present).
   - If `links:` absent → create as YAML list with the target.
   - If `links:` is string → convert to list, append.
   - Log each edit immediately after applying.
8. Re-run: `python3 wiki/scripts/build-links-graph.py && python3 wiki/scripts/graph-analyze.py`
9. Log to `wiki/LOG.md` with accepted/rejected counts.

**Safety:** Steps 1–5 automatic and safe. Step 7 requires user confirmation after preview.

### `wiki-lint`

Read-only health check of vault and skill artifacts.

**Checks:**
1. **Stale tag indexes:** `wiki/tags/<tag>.md` exists but tag not in vault → report.
2. **Missing descriptions:** Tag index files without `description` frontmatter → report count.
3. **Broken wikilinks:** `links:` pointing to non-existent files → report.
4. **Graph orphans:** Notes with degree 0, excluding daily notes → report count.
5. **Artifact consistency:** `tags-index.md` entries match `wiki/tags/*.md` → report drift.
6. **Orphan MOC notes:** MOC notes referencing deleted notes → report.
7. **Malformed links:** `links:` entries not in `[[wikilink]]` format → report.

**Output:** Structured checklist to user. No files modified.

### `wiki-ingest [filename]`

Suggest and apply tags + links for unprocessed notes or a specific note.

**Steps:**
1. Find target notes:
   - If `filename` provided → single note.
   - Otherwise → all notes with `need-processing` tag (max 10 per run).
2. For each note:
   - Read note content and existing frontmatter.
   - **Find relevant tags:**
     - Extract keywords from note title (strip ZK prefix, remove stopwords).
     - Match against `wiki/tags-index.md` tag names and descriptions.
     - Exclude already-assigned tags and excluded tags (`need-processing`, `daily-note`).
     - Take top 5 most relevant tags.
   - **Find candidate links:**
     - For each relevant tag, read `wiki/tags/<tag>.md` → candidate notes.
     - Grep vault `atoms/` and `daily notes/` for key phrases from note title.
     - Exclude already-linked notes, self, and notes with ONLY `daily-note` tag.
     - Score by common tags + keyword matches. Take top 5.
   - `need-processing` tag is NOT removed. It stays as a marker.
3. **PREVIEW** — present to user as a table:

   ```
   | # | Заметка | Текущие теги | Предлагаемые теги | Предлагаемые связи |
   |---|---------|-------------|-------------------|-------------------|
   | 1 | [[note]] | task | career, … | [[a]], [[b]] |
   ```

   **WAIT for user confirmation.** Do not apply without explicit approval.

4. **APPLY (only after confirmation):**
   - Update note frontmatter: merge new tags into `tags:` list (dedup), merge new links into `links:` list (dedup).
   - Update `wiki/tags/<tag>.md` for each tag — add note wikilink if not already present.
   - Never remove existing tags or links.
5. Log to `wiki/LOG.md` with `### Changes`.

**Safety:** Requires user confirmation. Max 10 notes, 5 tags, 5 links per note. Never removes existing links or tags.

## Dry Run / Preview / Confirm Policy

| Command | Preview required? | Confirm required? |
|---|---|---|
| `wiki-reindex` | No | No (safe) |
| `wiki-research` | No | No (safe) |
| `wiki-analyze` | **Yes** — before applying links | **Yes** |
| `wiki-ingest` | **Yes** — before applying | **Yes** |
| `wiki-lint` | No (always read-only) | No |

The agent must present changes in a table and wait for explicit user approval. Ambiguous responses ("maybe", "I guess", silence) → abort destructive step.

## Failure Recovery

### Agent crashes during wiki-analyze link application
1. Check `wiki/LOG.md` → most recent `### Changes` section.
2. Each applied link is individually logged with file path.
3. Re-run `wiki-analyze` from step 1. Agent deduplicates already-applied links.

### Script produces corrupted output
1. Delete the affected file in `wiki/data/` or `wiki/tags/`.
2. Re-run the script. All agent artifacts are regenerable from vault source.

### Cluster labels changed after re-run (expected)
MOC notes reference cluster members by `[[wikilink]]`, not by cluster ID. The MOC note remains valid even if the numeric cluster ID changes in `graph-stats.md`.

## Anti-Noise Guardrails

### Tags
- Excluded from index: `need-processing`, `daily-note` (configurable).
- Excluded: hex colors (3–8 hex chars), tags starting with digits.
- Config: `config.exclude.tags`.

### Link Suggestions
- Exclude pairs where BOTH notes are from `daily notes/`.
- Exclude pairs where either note has ONLY tags listed in `exclude.tags_from_analyze` (config, default `#daily-note`).
- Minimum content length for TF-IDF: `min_content_tokens` tokens (config, default 50).
- Minimum TF-IDF similarity: `min_tfidf_similarity` (config, default 0.20).

### MOC Index
- Minimum cluster size for reporting: `min_cluster_size_for_moc` (config, default 5).
- Read-only — only generates `wiki/moc-index.md`, never creates vault notes.

### Tag Descriptions
- Only generated when **missing** (absent field in frontmatter), never overwritten.
- Format: one Russian sentence, no colons, no markdown.

## Config

`wiki/config.json`:

```json
{
  "thresholds": {
    "min_cluster_size_for_moc": 5,
    "min_tag_coherence_for_moc": 3,
    "max_moc_per_run": 5,
    "max_link_suggestions": 50,
    "max_suggestions_to_validate": 20,
    "min_tfidf_similarity": 0.20,
    "min_content_tokens": 50
  },
  "exclude": {
    "tags": ["need-processing", "daily-note"],
    "tags_from_analyze": ["daily-note"],
    "dirs_from_suggestions": ["daily notes"],
    "dirs_from_graph": []
  },
  "source_dirs": {
    "tags": ["atoms", "daily notes"],
    "graph": ["atoms"]
  }
}
```

Scripts fall back to hardcoded defaults if `config.json` is missing or unparseable.

## Performance / Scaling

- Tested: ~2200 notes, ~2800 edges. Full reindex < 30s, graph build < 10s.
- TF-IDF capped at 1500 notes (MAX_NOTES in script). Skips notes with < `min_content_tokens` tokens.
- Label propagation converges quickly on sparse graphs.
- All scripts use Python 3 stdlib only — no dependencies.

## Obsidian Compatibility

- Wikilinks: `[[filename]]` format. `.md` extension normalized during graph build.
- Frontmatter: YAML-like (simple key: value, YAML lists via `-` prefix).
- Dataview: MOC notes include Dataview queries compatible with community plugin.
- Zettelkasten: atomic notes in `atoms/` with timestamp prefixes. Links stored in `links:` frontmatter.
- Templates in `templates/` always excluded from all indices and queries.

## Scripts Reference

| Script | Input | Output | Idempotent? |
|--------|-------|--------|-------------|
| `index-tags.py` | `atoms/`, `daily notes/` | `wiki/tags/*.md` | Yes |
| `generate-tags-index.py` | `wiki/tags/*.md` | `wiki/tags-index.md` | Yes |
| `build-links-graph.py` | `atoms/` | `wiki/data/links-graph.json` | Yes |
| `graph-analyze.py` | `wiki/data/links-graph.json` | `wiki/data/graph-stats.md`, updates `links-graph.json` | Approx* |
| `graph-suggest-links.py` | `wiki/data/links-graph.json` | `wiki/data/link-suggestions.md` | Yes |
| `tfidf-suggest.py` | `wiki/data/links-graph.json`, vault notes | `wiki/data/semantic-suggestions.md` | Yes |
| `generate-moc-index.py` | `wiki/data/links-graph.json` | `wiki/moc-index.md` | Yes |
| `index-dates.py` | `atoms/`, `daily notes/` | `wiki/dates/YYYY/YYYY-MM.md` | Yes |

*Cluster labels from label propagation may shift between runs — this is cosmetic.

## Search by Tag

When the user asks to search notes by tag, read `wiki/tags/<tag>.md` and return the list of wikilinks. If the file doesn't exist, suggest running `wiki-reindex`.

## Script Dependencies

Scripts assume they are run from the project root (e.g., `python3 wiki/scripts/index-tags.py`). They resolve paths relative to the script location. All scripts require Python 3.6+ with stdlib only.
