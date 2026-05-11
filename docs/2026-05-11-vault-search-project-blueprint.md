# Vault Search Project Blueprint

Date: 2026-05-11

## 1. Project Summary

Vault Search is a local-first command line search tool for Obsidian vaults.

The project starts from an empty Python codebase. Its first version will turn the current repository into a standard Python project that can index Markdown notes from any Obsidian vault, store searchable metadata in SQLite, and expose search and vault health checks through CLI commands.

The current repository root is the future project root. The existing `docs/` directory remains the planning and design area. Source code, tests, packaging metadata, and fixtures will be added at the root level.

## 2. Problem Statement

Obsidian vaults are excellent knowledge stores, but plain file search is often not enough for structured retrieval. A useful search tool should understand common vault conventions:

- Markdown titles and headings
- YAML-style frontmatter tags
- Inline tags
- Wikilinks such as `[[Some Note]]`
- Directory-based areas such as `wiki/`, `IT-learning/`, or other top-level folders
- Ignored runtime folders such as `.obsidian/` and `tmp/`

Vault Search should provide a small, reliable local index that can be rebuilt quickly and queried from scripts, terminals, and future integrations.

## 3. Goals

V1 will provide:

- A standard Python package named `vault-search`, importing as `vault_search`.
- A CLI for indexing, searching, and health checks.
- Local SQLite storage with FTS5 for full-text search.
- A Chinese-friendly fallback search path for terms that FTS5 does not match well.
- Markdown parsing for title, headings, frontmatter tags, inline tags, wikilinks, and body text.
- File discovery for Markdown notes, excluding common generated or internal vault folders.
- Lightweight vault health metrics, including missing tags, missing titles, wikilink count, broken wikilink count, and area distribution.
- JSON output for automation and readable text output for terminal usage.
- Tests based on a fixture vault, without requiring a real user vault.

## 4. Non-Goals

V1 will not include:

- Semantic search or embeddings.
- A web UI.
- An Obsidian plugin.
- Background filesystem watching.
- Incremental indexing.
- Cloud sync or remote storage.
- Automatic modification of user notes.
- Heavy knowledge graph analysis such as orphan note ranking, backlink scoring, or duplicate-title resolution.

These may become later roadmap items, but the first version should stay small and testable.

## 5. Project Root Layout

The repository root should become the Python project root:

```text
vault-search/
├── docs/
│   ├── 2026-05-11-vault-search-plan.md
│   ├── 2026-05-11-vault-search-exe.md
│   └── 2026-05-11-vault-search-project-blueprint.md
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── vault_search/
│       ├── __init__.py
│       ├── models.py
│       ├── parser.py
│       ├── discovery.py
│       ├── database.py
│       ├── indexer.py
│       └── cli.py
└── tests/
    ├── __init__.py
    ├── test_parser.py
    ├── test_discovery.py
    ├── test_database.py
    ├── test_indexer.py
    ├── test_cli.py
    └── fixtures/
        └── sample_vault/
```

This is not a nested project. Do not create a second `vault-search/` directory inside the current repository.

## 6. Tech Stack Decisions

### V1 Locked Decisions

- Language: Python `>=3.10`
- Packaging: `pyproject.toml` with `setuptools`
- Import package: `vault_search`
- CLI entry points: `[project.scripts]`
- Database: SQLite via Python standard library `sqlite3`
- Full-text index: SQLite FTS5
- Paths and filesystem: `pathlib`
- CLI parsing: `argparse`
- JSON output: standard library `json`
- Tests: `pytest`

### V1 Dependency Policy

Prefer the Python standard library unless a dependency clearly improves correctness.

For frontmatter, V1 can start with a lightweight parser that supports the project-required subset:

- Frontmatter starts and ends with `---`
- `tags` may be a YAML-style list, bracket list, or simple string
- Unknown frontmatter keys are preserved only if needed later

If real-world vaults require broader YAML support, add `PyYAML` deliberately and cover it with tests.

### Deferred Stack Decisions

Do not choose these technologies during V1:

- Embedding model provider
- Vector database
- Web framework
- Obsidian plugin framework
- Graph analysis library
- Background job runner

Those choices belong to later versions after V1 proves the local index and CLI shape.

## 7. CLI Contract

The normal user experience is `--root` first. `--db` is available as an advanced override for tests, custom locations, or multiple indexes.

### Index

```bash
vault-index --root /path/to/vault
vault-index --root /path/to/vault --db /custom/path/index.sqlite
```

Behavior:

- Scan Markdown files under `--root`.
- Exclude ignored folders.
- Parse notes.
- Rebuild the SQLite index.
- Default database path: `<root>/tmp/vault-search.sqlite`.
- Print an indexing summary as JSON.

### Search

```bash
vault-search "SSL 证书" --root /path/to/vault
vault-search "SSL 证书" --root /path/to/vault --json
vault-search "SSL 证书" --root /path/to/vault --area wiki --tag network --limit 20
vault-search "SSL 证书" --db /custom/path/index.sqlite --json
```

Behavior:

- Query the existing SQLite index.
- Use FTS5 first.
- Use a Chinese-friendly fallback match when FTS5 returns weak or empty results.
- Support optional filters by area and tag.
- Return readable terminal output by default.
- Return structured JSON when `--json` is passed.

### Health

```bash
vault-health --root /path/to/vault
vault-health --root /path/to/vault --json
vault-health --db /custom/path/index.sqlite --json
```

Behavior:

- Read health metrics from the index.
- Report lightweight vault quality indicators.
- Return readable terminal output by default.
- Return structured JSON when `--json` is passed.

## 8. Data Model

The core model should stay small.

### Document

Represents one Markdown file.

Fields:

- `path`: vault-relative path, such as `wiki/INDEX.md`
- `title`: first H1, frontmatter title, or filename fallback
- `area`: top-level directory or configured area
- `tags`: normalized list of tags
- `headings`: parsed Markdown headings
- `links`: parsed wikilinks
- `body`: searchable plain Markdown text
- `mtime`: source file modification time

### Heading

Fields:

- `level`: Markdown heading level
- `text`: heading text
- `line`: source line number

### Link

Fields:

- `target`: raw wikilink target
- `alias`: optional alias after `|`
- `line`: source line number
- `resolved_path`: matched vault-relative file path, if resolvable

## 9. Index Storage

SQLite should store both structured metadata and searchable text.

Recommended tables:

- `documents`: one row per Markdown file
- `document_tags`: one row per document/tag pair
- `headings`: one row per heading
- `wikilinks`: one row per wikilink
- `documents_fts`: FTS5 virtual table for title and body search

V1 indexing can use full rebuilds only:

1. Delete existing index file or clear existing tables.
2. Discover all Markdown files.
3. Parse each file.
4. Resolve wikilinks against discovered note titles and paths.
5. Insert documents and related rows in one transaction.
6. Rebuild the FTS table.

Incremental indexing is intentionally deferred.

## 10. Search Behavior

Search should combine precision and practical usefulness.

Primary path:

- Query `documents_fts` using FTS5.
- Rank results using SQLite FTS rank or a simple project-defined score.
- Apply area, tag, and limit filters.

Fallback path:

- If FTS5 returns no results, or if the query contains CJK characters and FTS5 matching is weak, use a simple `LIKE` fallback against title and body.
- Merge fallback results with FTS results without duplicates.
- Keep ranking simple: title matches before body matches, exact substring before partial fallback.

The fallback is not intended to be a full Chinese tokenizer. It exists to make Chinese vault search useful in V1 without adding heavy dependencies.

## 11. Health Metrics

V1 health checks should be lightweight and index-derived.

Metrics:

- `documents`: total indexed Markdown documents
- `areas`: document counts by area
- `tags`: total unique tags
- `missing_tags`: documents with no tags
- `missing_titles`: documents without an explicit title or H1
- `wikilinks`: total wikilinks
- `broken_wikilinks`: wikilinks that could not be resolved
- `ignored_files`: Markdown files skipped because they are under ignored directories

The health command should not modify notes. It only reports.

## 12. File Discovery Rules

V1 should discover files by walking the vault root and selecting `.md` files.

Default ignored directories:

- `.obsidian/`
- `.git/`
- `tmp/`
- `.trash/`
- `node_modules/`
- `.venv/`

Area detection:

- If a file is under a top-level directory, the area is that directory name.
- If a file is at the vault root, the area is `root`.

Future versions may read area rules and ignored paths from `meta/search-config.json`.

## 13. Parser Rules

The parser should support the common subset needed by V1:

- Optional frontmatter block at the top of the file.
- Tags from frontmatter `tags`.
- Inline tags in body text, such as `#python` or `#知识总结`.
- Markdown headings from `#` through `######`.
- Wikilinks in forms:
  - `[[Target]]`
  - `[[Target|Alias]]`
  - `[[Target#Heading]]`
- Body text as the original Markdown content minus frontmatter.

Parser behavior should be deterministic and covered by focused tests.

## 14. Configuration

V1 should work without a config file.

Default behavior should be hardcoded and documented:

- Default database: `<root>/tmp/vault-search.sqlite`
- Default ignored directories as listed above
- Default area detection by top-level folder

Future config file:

```text
<vault>/meta/search-config.json
```

Potential future settings:

- ignored directories
- area mappings
- default database path
- search ranking options
- health check thresholds

## 15. Testing Strategy

Use `pytest` and a fixture vault.

Required test areas:

- Parser extracts title, headings, tags, body, and wikilinks.
- Discovery finds Markdown files and ignores internal/runtime folders.
- Database rebuild creates expected tables and searchable rows.
- Search returns FTS matches and Chinese fallback matches.
- Indexer ties discovery, parsing, link resolution, and database rebuild together.
- CLI commands work with `--root`, `--db`, and `--json`.
- Health metrics match known fixture data.

Tests should not require a real Obsidian vault.

## 16. README Scope

After implementation starts, `README.md` should become the public entry point and contain:

- What Vault Search does
- Installation instructions
- Quick start commands
- CLI reference
- V1 limitations
- Development setup

This blueprint remains the internal project definition.

## 17. Roadmap

### v0.1.0

- SQLite + FTS5 index
- Chinese fallback search
- Full rebuild indexing
- CLI search
- CLI health
- JSON output
- Fixture-based tests

### v0.2.0

- Config file support
- Better ranking
- More robust frontmatter parsing
- Optional incremental indexing

### v0.3.0

- Semantic search investigation
- Embedding storage strategy
- Hybrid keyword + semantic retrieval

### v0.4.0

- Knowledge graph metrics
- Backlink and orphan note analysis
- Duplicate or near-duplicate note detection

### v0.5.0

- Local web UI or Obsidian integration, depending on validated usage patterns

## 18. Open Questions

These decisions are intentionally deferred until implementation or real vault testing:

- Whether lightweight frontmatter parsing is enough, or `PyYAML` is needed.
- Whether Chinese fallback with `LIKE` is sufficient for the user's real notes.
- Whether default ignored directories need user configuration in V1.
- Whether area detection should stay top-level-folder based or become config-driven earlier.

## 19. Implementation Readiness

The project is ready for an implementation plan once this blueprint is accepted.

The recommended implementation order is:

1. Create packaging skeleton.
2. Implement parser with tests.
3. Implement discovery with tests.
4. Implement SQLite schema and rebuild logic with tests.
5. Implement search and Chinese fallback with tests.
6. Implement index orchestration and wikilink resolution with tests.
7. Implement CLI entry points with tests.
8. Write README and verify commands against the fixture vault.
