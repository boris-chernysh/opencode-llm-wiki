---
description: "Research a given topic using the vault. Searches tag indices in wiki/tags/ for relevant notes and compiles findings. Read-only on vault."
---

Load the llm-wiki skill.

Research the topic: **$ARGUMENTS**

1. Read `wiki/tags-index.md`. Find relevant tags by keyword match on tag names and descriptions (max 10 tags).
2. For each relevant tag, read `wiki/tags/<tag>.md` to discover connected notes.
3. Read the actual notes (max 50 total).
4. Compile a structured research summary in Russian:
   - **Краткий снимок** — 2–3 sentence situation summary.
   - **Ключевые находки** — bullet list of findings with `[[wikilinks]]`.
   - **Выводы** — 2–3 actionable conclusions.
   - **Источники** — list of notes consulted as wikilinks.
5. Save to `wiki/research/<YYYYMMDDHHMM> Topic.md` with frontmatter:
   ```yaml
   ---
   topic: "Exact research topic"
   date: "YYYY-MM-DD"
   tags:
     - used_tag1
     - used_tag2
   ---
   ```
6. Return the summary to the user.
7. Log to `wiki/LOG.md`.

**Safety:** Read-only on vault. Writes only to `wiki/research/`.
