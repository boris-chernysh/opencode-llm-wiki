---
description: "Full reindex of the Obsidian vault: rebuilds tag indexes (wiki/tags/), consolidated tag index (wiki/tags-index.md), link graph (wiki/data/links-graph.json), graph analysis (wiki/data/graph-stats.md), MOC index (wiki/moc-index.md), and date-based index (wiki/dates/). Safe — only writes to wiki/ artifacts, never touches vault notes."
---

Load the llm-wiki skill.

Run:
```
python3 wiki/scripts/index-tags.py && \
python3 wiki/scripts/generate-tags-index.py && \
python3 wiki/scripts/build-links-graph.py && \
python3 wiki/scripts/graph-analyze.py && \
python3 wiki/scripts/generate-moc-index.py && \
python3 wiki/scripts/index-dates.py
```

After all scripts complete:

1. Read tag index files in `wiki/tags/`. For any index file **MISSING** a `description` field in its frontmatter, generate a one-sentence Russian description based on the note titles with that tag. **Do NOT overwrite existing descriptions.** Generate descriptions for ALL missing tags (no per-run limit).
2. Re-run `python3 wiki/scripts/generate-tags-index.py` to update the consolidated index.
3. Read monthly date index files in `wiki/dates/`. For any monthly file **MISSING** a `description` field, generate a short Russian summary (1–2 sentences) about that month's notes. **Do NOT overwrite existing descriptions.**
4. Read `wiki/data/graph-stats.md` and `wiki/moc-index.md`. Report hub rankings, cluster sizes, and top tags to the user.
5. Log to `wiki/LOG.md`.

**Safety:** Read-only on vault. All writes go to `wiki/`. Expected duration: 5–30 seconds for a ~2000-note vault.
