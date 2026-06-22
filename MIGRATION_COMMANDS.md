# Migration Guide: v0.2.0 → v0.3.0 — Commands as Markdown Files

## Overview

Per-command contracts are extracted from `SKILL.md` into individual `commands/wiki-*.md` files. Opencode now loads them natively from `<vault>/.opencode/commands/`. The old `opencode-commands.json` + `merge-commands.sh` flow is removed.

## What Changed

| Aspect | v0.2.0 | v0.3.0 |
|---|---|---|
| Command source | `opencode-commands.json` (JSON) | `commands/wiki-*.md` (markdown) |
| Loading mechanism | `merge-commands.sh` injects into `opencode.json` `command:` block | Opencode reads `<vault>/.opencode/commands/*.md` natively |
| `opencode-commands.json` | exists | **deleted** |
| `merge-commands.sh` | exists | **deleted** |
| `SKILL.md` size | 434 lines | 319 lines (Command Contracts section replaced by a 7-row index table) |
| Runtime behavior | 5 commands: `wiki-reindex`, `wiki-research`, `wiki-analyze`, `wiki-lint`, `wiki-ingest` | **Identical** — same names, same arguments, same outputs |
| Agent prompt per command | Inlined in JSON `template` | Body of `commands/wiki-*.md` |

## Why

- **Single source of truth** — one `.md` per command; no parallel JSON that can drift.
- **No install-time merge step** — opencode loads `.md` files directly.
- **Smaller `SKILL.md`** — schemas, safety rules, and responsibility matrix stay; command contracts move out.
- **Easier maintenance** — edit a command in one place, see a clean diff in a single file.

## Breaking Changes

- **None for end users.** Same five commands, same arguments, same outputs.
- **Yes for maintainers:** edit `commands/*.md`, not `opencode-commands.json`. The `command:` block in `opencode.json` is no longer used by the skill.

## Automatic (recommended)

```bash
cd /path/to/opencode-llm-wiki
git pull
./migrate-commands.sh /path/to/vault
```

The script:

1. Backs up `.opencode/opencode.json` → `.opencode/opencode.json.bak-v0.2.0` (only if the old `command:` block is present).
2. Removes the `command:` block from `.opencode/opencode.json`.
3. Creates `<vault>/.opencode/commands/`.
4. Symlinks each `commands/wiki-*.md` from the repo into the vault's commands dir (or copies with `--copy`).
5. Idempotent — safe to re-run.

For Windows (no Developer Mode / no symlinks):

```bash
./migrate-commands.sh /path/to/vault --copy
```

## Manual Steps

If you prefer to do it by hand:

### 1. Back up

```bash
cd /path/to/vault
cp .opencode/opencode.json{,.bak-v0.2.0}
```

### 2. Strip the `command:` block

```bash
python3 -c "
import json
p='.opencode/opencode.json'
d=json.load(open(p))
d.pop('command', None)
json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)
print('OK')
"
```

### 3. Pull the new version

```bash
cd /path/to/opencode-llm-wiki
git pull
```

### 4. Install the command files

```bash
mkdir -p /path/to/vault/.opencode/commands
for c in reindex research analyze lint ingest; do
  ln -sf "$PWD/commands/wiki-$c.md" "/path/to/vault/.opencode/commands/wiki-$c.md"
done
```

On Windows (or if you prefer copies):

```bash
mkdir -p /path/to/vault/.opencode/commands
cp commands/wiki-*.md /path/to/vault/.opencode/commands/
```

## Verify

```bash
ls /path/to/vault/.opencode/commands/
# Expected:
# wiki-analyze.md
# wiki-ingest.md
# wiki-lint.md
# wiki-reindex.md
# wiki-research.md
```

Smoke test (requires `opencode` CLI):

```bash
opencode run --command wiki-lint --dir /path/to/vault
```

`wiki-lint` is read-only — safest first run.

## Rollback

If something breaks:

```bash
cd /path/to/vault
cp .opencode/opencode.json.bak-v0.2.0 .opencode/opencode.json
rm -f .opencode/commands/wiki-*.md
```

Then `git checkout v0.2.0` (or pre-migration commit) in the skill repo. **No vault data is modified** by this migration.

## File Layout Comparison

### v0.2.0

```
vault/
├── wiki/                          # skill artifacts
├── .opencode/
│   ├── opencode.json              # contains: { command: { wiki-*: { template: "..." } } }
│   └── skills/llm-wiki/SKILL.md
```

### v0.3.0

```
vault/
├── wiki/                          # skill artifacts (unchanged)
├── .opencode/
│   ├── opencode.json              # no `command:` block
│   ├── commands/                  # NEW: native opencode command dir
│   │   ├── wiki-reindex.md
│   │   ├── wiki-research.md
│   │   ├── wiki-analyze.md
│   │   ├── wiki-lint.md
│   │   └── wiki-ingest.md
│   └── skills/llm-wiki/SKILL.md   # slimmed: 319 lines, no Command Contracts
```

## See Also

- `MIGRATION.md` — v0.1.0 → v0.2.0 (rename `agent/` → `wiki/`, rename `wiki-process-note` → `wiki-ingest`)
- `CHANGELOG.md` — full release notes
- `README.md` — install / upgrade instructions
