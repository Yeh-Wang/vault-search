# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode + test runner
python3 -m pip install -e .
python3 -m pip install pytest

# Run full test suite
python3 -m pytest -v

# Run a single test file or test
python3 -m pytest tests/test_parser.py -v
python3 -m pytest tests/test_parser.py::test_parse_markdown_frontmatter_headings_tags_and_links -v

# Run the CLI tools
vault-index --root /path/to/vault
vault-search "query" --root /path/to/vault --json
vault-health --root /path/to/vault --json
```

## Architecture

This is a local-first CLI tool for full-text search over Obsidian vaults. It indexes Markdown files into SQLite + FTS5 and provides three CLI entry points: `vault-index`, `vault-search`, `vault-health`.

**Pipeline:** `discovery` → `parser` → `indexer` (which calls `database`)

- **`discovery.py`** — walks a vault root for `*.md` files, skips ignored dirs (`.obsidian/`, `.git/`, `tmp/`, `.venv/`, `node_modules/`, `.trash/`, `.pytest_cache/`). Returns `DiscoveredFile` objects with `relative_path`, `area` (top-level dir or `"root"`), and `mtime`.
- **`parser.py`** — parses a single Markdown file into a `Document` dataclass. Extracts: YAML frontmatter (title, tags), headings (`#`), wikilinks (`[[target|alias]]`), inline tags (`#tag`). Title resolution: first heading > frontmatter `title:` > filename stem. Supports Chinese characters in inline tags.
- **`models.py`** — frozen dataclasses: `Document`, `Heading`, `Link`. These are the canonical data types flowing through the pipeline.
- **`indexer.py`** — orchestrates discovery + parsing + link resolution, then calls `rebuild_database()`. Link resolution matches wikilink targets against document paths, titles, and stems (in that order), stripping `#section` fragments.
- **`database.py`** — SQLite schema management, full-text search, and health queries. Uses FTS5 for keyword search with a Chinese-friendly `LIKE` fallback (triggered when FTS5 returns nothing for CJK queries). Schema: `documents`, `document_tags`, `headings`, `wikilinks`, `documents_fts` (virtual), `index_meta`.
- **`cli.py`** — argparse-based CLI. `--root` sets vault path (implies default DB path `<vault>/tmp/vault-search.sqlite`). `--db` overrides the DB path directly. `_resolve_db` handles the root/db resolution logic shared across all three commands.

**Default DB path:** `<vault_root>/tmp/vault-search.sqlite`

## Key conventions

- Codebase targets Python >= 3.10, uses `from __future__ import annotations` everywhere.
- Package uses `src` layout (`src/vault_search/`), configured via `pyproject.toml` with setuptools.
- Tests use `tmp_path` fixture for isolation and `sample_vault` (conftest) for a realistic multi-file vault structure.
- Ignored directories are a hardcoded set in `discovery.py` — no config file.
- The index is a full rebuild every time (no incremental indexing in v1).
