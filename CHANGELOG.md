# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] — Unreleased
### Fixed
- `links:` frontmatter: agent sometimes wrote unquoted `[[filename]]` (parses as YAML flow sequence — silently broken) or `[["filename"]]` (parses as nested list). The correct canonical form is `"[[filename]]"`. Updated `SKILL.md` (Obsidian Compatibility + Hard guardrails), `commands/wiki-analyze.md` (Step 7), `commands/wiki-ingest.md` (Step 4), and `commands/wiki-lint.md` (Step 7) with explicit format rules and concrete YAML examples. Tightened `wiki-lint` to flag all three bad variants. Fixed `tests/test_analyze_apply.py` reference implementation that produced the wrong form, and added a Test 4 that asserts the canonical quoted form is written. Replaced the no-op malformed-link check in `tests/test_lint.py` with a real scan. Added new eval scenario `analyze-link-format.yaml` and `links_quoted_format` check type to the eval harness.

## [0.3.0] — Unreleased
### Changed
- Commands extracted from `SKILL.md` into `commands/wiki-*.md` (one file per command).
- `opencode-commands.json` and `merge-commands.sh` deleted; opencode loads commands natively from `<vault>/.opencode/commands/`.
- `SKILL.md` slimmed from 434 to 319 lines; "Command Contracts" section replaced by an index table pointing to `commands/`.
- `setup.sh` now installs `commands/` into `<vault>/.opencode/commands/` (symlinks by default, `--copy` for Windows).
- `setup.sh` also strips the obsolete `command:` block from existing `<vault>/.opencode/opencode.json` files.
- `MIGRATION_COMMANDS.md` added with the v0.2.0 → v0.3.0 playbook and `migrate-commands.sh` automation.

### Notes
- Runtime behavior unchanged: same five commands, same arguments, same outputs.
- See `MIGRATION_COMMANDS.md` for upgrade instructions for v0.2.0 users.

## [0.2.0] — Unreleased
### Added
- Первая публичная версия: 7 скриптов, 6 команд, 14 тестов.
