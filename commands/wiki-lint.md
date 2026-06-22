---
description: "Read-only health check of vault and skill artifacts. Checks stale tag indexes, missing descriptions, broken wikilinks, graph orphans, artifact consistency, orphan MOC notes, malformed links."
---

Load the llm-wiki skill.

Run a read-only health check of the vault and skill artifacts.

1. **Stale tag indexes:** Compare `wiki/tags/*.md` against actual tags in vault. Run `python3 wiki/scripts/index-tags.py` and check whether any files in `wiki/tags/` were deleted by the re-run — report those as stale tags previously not removed.

2. **Missing descriptions:** Read files in `wiki/tags/`. Report the count of files without a `description` frontmatter field.

3. **Broken wikilinks:** Spot-check `wiki/tags/*.md` — sample 10+ index files, verify each linked note exists in `atoms/` or `daily notes/`. Report any missing targets.

4. **Graph orphans:** Read `wiki/data/graph-stats.md`. Report the orphan count (notes with degree 0, excluding daily notes).

5. **Artifact consistency:** Count tags in `wiki/tags/` vs entries in `wiki/tags-index.md`. Report any drift.

6. **Orphan MOC notes:** Read `wiki/moc-index.md`. Check whether any hub notes reference files that don't exist. Report findings.

7. **Malformed links:** Spot-check `atoms/` for `links:` frontmatter entries not in `[[wikilink]]` format. Report any malformed entries.

Report findings as a structured checklist to the user. Do **NOT** modify any files. Log findings to `wiki/LOG.md`.
