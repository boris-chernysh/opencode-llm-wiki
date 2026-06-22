---
description: "Analyze the vault for new Zettelkasten connections. Runs graph + TF-IDF analysis, generates link suggestions, validates them by reading note content, then SHOWS A PREVIEW and WAITS for user confirmation before applying any links to notes."
---

Load the llm-wiki skill.

**Step 1 — generate suggestions:**
```
python3 wiki/scripts/build-links-graph.py && \
python3 wiki/scripts/graph-suggest-links.py && \
python3 wiki/scripts/tfidf-suggest.py
```

**Step 2 — read** `wiki/data/link-suggestions.md` and `wiki/data/semantic-suggestions.md`.

**Step 3 — FILTER:**
- Exclude pairs where BOTH notes are from `daily notes/`.
- Exclude pairs where either note has ONLY tags listed in `wiki/config.json → exclude.tags_from_analyze` (default `#daily-note`).
- Exclude graph pairs with `jaccard == 0` AND no `shared_tags`.
- Exclude semantic pairs with `similarity < min_tfidf_similarity` (config).

**Step 4 —** take top `max_suggestions_to_validate` (default 20) from the filtered list.

**Step 5 — VALIDATE (read-only):** For each suggestion, read both notes. Assess semantic relevance. Classify each as accepted or rejected with a one-sentence reason in Russian.

**Step 6 — PREVIEW** — present to the user:

```
| # | Источник | Цель | Тип | Причина |
|---|----------|------|-----|---------|
| 1 | [[note_a]] | [[note_b]] | graph | 3 общих соседа, тема: здоровье |
| 2 | [[note_c]] | [[note_d]] | tfidf | similarity 0.45, тема: управление |
```

**WAIT for explicit user confirmation** ("да", "yes", "применить"). Do NOT apply without explicit approval. Ambiguous responses ("maybe", "I guess", silence) → abort.

**Step 7 — APPLY (only after confirmation):** For each accepted suggestion:
1. Read source note frontmatter.
2. If `links:` exists as YAML list → append `"[[target]]"` to the list (dedup against the quoted form).
3. If `links:` absent → create as YAML list, first item being `"[[target]]"`.
4. If `links:` is a string → convert to list, then append `"[[target]]"`.
5. **Format rule:** every `links:` list item MUST be `"[[filename]]"` — wikilink wrapped in double quotes. Never write `[[filename]]` unquoted (YAML parses it as a flow sequence, not a string) and never put quotes inside the brackets (`[["filename"]]` parses as a nested list). Correct:

   ```yaml
   links:
     - "[[filename.md]]"
   ```

6. Log each edit immediately after applying.

**Step 8 — re-run:**
```
python3 wiki/scripts/build-links-graph.py && \
python3 wiki/scripts/graph-analyze.py
```

**Step 9 — log** to `wiki/LOG.md` with accepted/rejected counts.

**Safety:** Steps 1–5 are automatic and safe. Step 7 requires user confirmation after preview.
