# Migration Guide: v0.1.0 → v0.2.0

## Breaking Changes

| Change | Old | New |
|--------|-----|-----|
| Directory renamed | `agent/` | `wiki/` |
| Command renamed | `wiki-process-note` | `wiki-ingest` |
| `wiki-moc` behavior | Created MOC files in `atoms/` | Read-only, only builds `moc-index.md` |

## New Features

- `wiki-reindex` now creates a date-based index in `wiki/dates/`
- `wiki-analyze` supports `exclude.tags_from_analyze` in config for tag filtering

---

## Migration

### Automatic (recommended)

```bash
cd /path/to/opencode-llm-wiki
git pull
./migrate.sh /path/to/vault --copy
```

The script handles:
- Preserving custom `agent/config.json` settings into `wiki/config.json` with new fields
- Renaming `wiki-process-note` → `wiki-ingest` in `.opencode/opencode.json`
- Renaming `agent/` → `wiki/` (preserves existing `tags/`, `data/`, `research/` — only stale scripts are removed)
- Running `setup.sh` to install fresh scripts

### Manual steps

#### Step 1: Back up

```bash
cd /path/to/vault
git add -A && git commit -m "backup before llm-wiki migration"
```

#### Step 2: Rename `agent/` → `wiki/`

```bash
rm -rf /path/to/vault/agent/scripts/
mv /path/to/vault/agent /path/to/vault/wiki
```

This preserves existing `tags/`, `data/`, and `research/` — only stale scripts with old `agent` paths are removed.

#### Step 3: Pull the new version

```bash
cd /path/to/opencode-llm-wiki
git pull
```

#### Step 4: Re-run setup

```bash
./setup.sh /path/to/vault --copy
```

#### Step 5: Update config.json

If you customized `agent/config.json`, manually migrate your settings to `wiki/config.json` and add the new field:

```json
"exclude": {
    "tags": ["need-processing", "daily-note"],
    "tags_from_analyze": ["daily-note"],
    "dirs_from_suggestions": ["daily notes"],
    "dirs_from_graph": []
}
```

#### Step 6: Update custom aliases or scripts

Rename `wiki-process-note` to `wiki-ingest` in any aliases, shortcuts, or scripts.

### Verify

```bash
cd /path/to/vault
python3 wiki/scripts/index-tags.py && echo "OK"
```

Run `wiki-reindex` to rebuild all artifacts including the new date index.
