# Project Status

Date: 2026-05-28

## Current State

V1 baseline + config system + unified CLI + query logic refactoring + search output enhancement + **search quality fixes**, tested and committed.

The package imports as `vault_search` and exposes a single `vlt` CLI entry point with subcommands:

- `vlt index`
- `vlt search`
- `vlt health`
- `vlt config`

Package management migrated from pip/pyenv to uv.

## Completed

- Python project skeleton with `pyproject.toml`, `src/`, and `tests/`.
- Editable package install using `setuptools`, managed by `uv`.
- Markdown parser for frontmatter tags, inline tags, headings, body text, and wikilinks.
- File discovery for Markdown notes with default ignored runtime directories.
- SQLite schema for documents, tags, headings, wikilinks, metadata, and FTS5 search.
- Full rebuild indexing.
- FTS5 keyword search.
- Chinese-friendly `LIKE` fallback search.
- Search result snippets.
- Area and tag search filters.
- Wikilink resolution by path, title, and file stem.
- Lightweight health summary.
- Unified CLI (`vlt`) with subcommands (index, search, health, config).
- Config system: global (`~/.config/vault-search/config.json`) + project (`<vault>/.obsidian/vault-search.json`).
- Auto-detect vault root by walking up from cwd looking for `.obsidian/`.
- Auto-build index when database doesn't exist.
- Windows UTF-8 output support.
- Configurable `--limit` via CLI > project config > global config > default 10.
- Global tool install via `uv tool install -e .`.
- README structured for users and developers.
- Git repository initialized with V1 baseline commit.
- **Search logic refactoring**: Introduced `SearchEngine`, `SnippetGenerator`, `OutputFormatter`, and `Database` classes for better separation of concerns.
- **Search output enhancement**: Strategy pattern for snippet generation with table, list, code block, and plain text handlers.
- **Smart snippet scoring**: Dynamic matching based on title matches, query position, frequency, and line length.
- **Dynamic match count**: Auto-adjusts based on document length (2-5 matches).
- **New output formats**: Added `--compact` option for one-line-per-result output.
- **Search quality fixes**: FTS5 rank scoring, LIKE wildcard escaping, FTS5 query sanitization, code block state tracking fix, shared DB connections.
- **Snippet heading context**: Matching lines show their parent heading for better readability; heading matches scored highest (+50).
- **Code comment downweight**: Comments inside code blocks scored -20 to deprioritize vs meaningful code.

## Verification

Last verified command:

```bash
uv run pytest -v
```

Last verified result:

```text
38 passed in 0.58s
```

Smoke checks performed:

- Indexed real vault (90 documents) successfully.
- Search returns Chinese and English results.
- Health check reports broken wikilinks.
- `vlt config set/get/list/path` all work.
- `vlt config set --local --root` writes project config correctly.
- Auto-detect `.obsidian/` from cwd works.
- `vlt --help` and all subcommand `--help` show descriptions.
- Search output formatting correctly handles tables, lists, and code blocks.
- New `--compact` output format works as expected.

## Known Limitations

- No incremental indexing.
- No semantic search or embeddings.
- No web UI.
- No Obsidian plugin.
- Basic wikilink resolution only.
- Frontmatter parsing intentionally supports only a small YAML-like subset.

## Next Candidates

- Improve health text output formatting.
- Add more parser coverage for real-world frontmatter variants.
- Add tests for malformed Markdown/frontmatter edge cases.
- Investigate incremental indexing.
- Semantic search investigation (v0.3.0 roadmap).
- Add additional snippet strategies (quote blocks, headings, math formulas).
- Improve search ranking algorithm.
