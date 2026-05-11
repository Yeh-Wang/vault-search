# Project Status

Date: 2026-05-11

## Current State

V1 baseline is implemented, tested, and committed.

Latest stable commit:

```text
04b62e5 feat: implement vault search v1
```

The repository root is now a working Python project. The package imports as `vault_search` and exposes three CLI commands:

- `vault-index`
- `vault-search`
- `vault-health`

## Completed

- Python project skeleton with `pyproject.toml`, `src/`, and `tests/`.
- Editable package install using `setuptools`.
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
- CLI commands for indexing, search, and health checks.
- Friendly CLI errors for missing databases.
- Empty vault handling.
- README with install, quick start, PATH troubleshooting, development, and limitations.
- Git repository initialized with V1 baseline commit.

## Verification

Last verified command:

```bash
python3 -m pytest -v
```

Last verified result:

```text
19 passed
```

Additional smoke checks performed:

- Indexed the project repository itself.
- Searched indexed docs for `SQLite`.
- Confirmed text search output includes snippets.
- Confirmed text search with no results prints `No results.`
- Confirmed `.pytest_cache/` is ignored during discovery.

## Known Limitations

- No config file support yet.
- No incremental indexing.
- No semantic search or embeddings.
- No web UI.
- No Obsidian plugin.
- Basic wikilink resolution only.
- Basic snippet generation only.
- Search ranking is still simple.
- Frontmatter parsing intentionally supports only a small YAML-like subset.

## Next Candidates

- Add `CHANGELOG.md` for `0.1.0`.
- Add release metadata to `pyproject.toml`.
- Improve search ranking.
- Improve health text output.
- Add config support via `<vault>/meta/search-config.json`.
- Add more parser coverage for real-world frontmatter variants.
- Add tests for malformed Markdown/frontmatter edge cases.
