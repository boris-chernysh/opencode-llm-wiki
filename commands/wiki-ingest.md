---
description: "Suggest and apply tags + links + project for unprocessed notes (with #need-processing tag) in atoms/ or a specific note. Reads tag index, finds relevant tags and candidate links, presents a preview table, and applies only after user confirmation."
---

Load the llm-wiki skill.

**Step 1 — find target notes:**
- If a filename is provided as `$ARGUMENTS` → use that single note.
- Otherwise → find all notes with the `need-processing` tag in `atoms/` (max 10 per run).

**Step 2 — for each note:**

1. Read note content and existing frontmatter.

2. **Find relevant tags:**
   - Extract keywords from note title (strip ZK prefix, remove stopwords).
   - Match against `wiki/tags-index.md` tag names and descriptions.
   - Exclude already-assigned tags and excluded tags (`need-processing`, `daily-note`).
   - Take top 5 most relevant tags.

3. **Find candidate links:**
   - For each relevant tag, read `wiki/tags/<tag>.md` → candidate notes.
   - Grep vault `atoms/` and `daily notes/` for key phrases from note title.
   - Exclude already-linked notes, self, and notes with ONLY `daily-note` tag.
   - Score by common tags + keyword matches. Take top 5.

4. **Find most relevant project (SKIP if note already has `project:` field set):**
   - Read `wiki/tags/project.md` to get the list of all project notes.
   - For each project note, read its title.
   - Match ingested note title/keywords against project titles.
   - Select the single best match. If no good match, show `—`.

5. `need-processing` tag is **NOT** removed. It stays as a marker.

**Step 3 — PREVIEW** — present to the user as a table:

```
| # | Заметка | Текущие теги | Предлагаемые теги | Предлагаемые связи | Проект |
|---|---------|-------------|-------------------|-------------------|--------|
| 1 | [[note]] | task | career, … | [[a]], [[b]] | [[Сайт-портфолио]] |
```

**WAIT for explicit user confirmation** ("да", "yes", "применить"). Do NOT apply without explicit approval. Ambiguous responses → abort.

**Step 4 — APPLY (only after confirmation):**
- Update note frontmatter: merge new tags into `tags:` list (dedup), merge new links into `links:` list (dedup).
- If project was suggested and `project:` field is absent → set `project: "[[project-note.md]]"`. If `project:` already set → skip.
- Update `wiki/tags/<tag>.md` for each new tag — add note wikilink if not already present.
- **Never** remove existing tags, links, or project.

**Step 5 — log** to `wiki/LOG.md` with `### Changes` section.

**Safety:** Requires user confirmation. Max 10 notes, 5 tags, 5 links, 1 project per note. Never removes existing links, tags, or project assignments.
