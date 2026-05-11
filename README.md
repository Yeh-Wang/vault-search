# Vault Search

Local-first command line search for Obsidian vaults.

Vault Search indexes Markdown files from an Obsidian vault into SQLite + FTS5 and provides CLI commands for search and lightweight vault health checks.

## Install

```bash
python -m pip install -e .
```

Verify the package import:

```bash
python -c "import vault_search; print(vault_search.__version__)"
```

If `vault-index`, `vault-search`, or `vault-health` are not found after installation, your Python scripts directory is probably not on `PATH`. Locate it with:

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

```bash
python -m pip install -e .
python -m pytest -v
```

This project requires Python `>=3.10`. If your system `python` points to an older runtime, use a newer interpreter explicitly:

```bash
python3.12 -m pip install -e .
python3.12 -m pytest -v
```

## Limitations

V1 does not include semantic search, incremental indexing, a web UI, an Obsidian plugin, or advanced knowledge graph analysis.
