# Vault Search

Local-first command line search for Obsidian vaults.

Vault Search indexes Markdown files from an Obsidian vault into SQLite + FTS5 and provides CLI commands for search and lightweight vault health checks.

## Setup and Run

Prerequisite: local Python `>=3.10`.

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode and install the test runner:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

Verify the package import:

```bash
python -c "import vault_search; print(vault_search.__version__)"
```

Run the test suite:

```bash
python -m pytest -v
```

Run the CLI:

```bash
vault-index --root /path/to/vault
vault-search "SSL 证书" --root /path/to/vault
vault-search "SSL 证书" --root /path/to/vault --json
vault-health --root /path/to/vault
vault-health --root /path/to/vault --json
```

If `vault-index`, `vault-search`, or `vault-health` are not found after installation, confirm that the virtual environment is active:

```bash
source .venv/bin/activate
which python
which vault-search
```

If commands are still not found, locate the Python scripts directory with:

```bash
python -m site --user-base
python -m pip show -f vault-search
```

Then either add that environment's `bin` directory to `PATH`, or run the generated scripts by absolute path.

## Quick Start

```bash
vault-index --root /path/to/vault
vault-search "SSL 证书" --root /path/to/vault --json
vault-health --root /path/to/vault --json
```

By default, the index is written to:

```text
<vault>/tmp/vault-search.sqlite
```

Use `--db` to override the index path:

```bash
vault-index --root /path/to/vault --db /tmp/vault.sqlite
vault-search "SSL" --db /tmp/vault.sqlite --json
```

## V1 Features

- Markdown discovery under a vault root
- Ignored runtime directories such as `.obsidian/`, `.git/`, and `tmp/`
- Frontmatter and inline tag extraction
- Heading extraction
- Wikilink extraction and basic resolution
- SQLite + FTS5 keyword search
- Chinese-friendly fallback matching with SQLite `LIKE`
- JSON output for automation
- Lightweight health metrics

## Development

Main code paths:

- `src/vault_search/parser.py`: Markdown parsing
- `src/vault_search/discovery.py`: vault file discovery
- `src/vault_search/database.py`: SQLite schema, search, and health queries
- `src/vault_search/indexer.py`: index build orchestration
- `src/vault_search/cli.py`: CLI entry points
- `tests/`: behavior coverage

Before committing changes, run:

```bash
python -m pytest -v
```

## Limitations

V1 does not include semantic search, incremental indexing, a web UI, an Obsidian plugin, or advanced knowledge graph analysis.
