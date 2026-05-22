# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install project and all dependencies (creates venv + lockfile automatically)
uv sync

# Run full test suite
uv run pytest -v

# Run a single test file or test
uv run pytest tests/test_parser.py -v
uv run pytest tests/test_parser.py::test_parse_markdown_frontmatter_headings_tags_and_links -v

# Run the CLI tool
uv run vlt index --root /path/to/vault
uv run vlt search "query" --root /path/to/vault --json
uv run vlt health --root /path/to/vault --json

# Config management
uv run vlt config set default_root /path/to/vault
uv run vlt config get default_root
uv run vlt config list
uv run vlt config path
```

## Architecture

This is a local-first CLI tool for full-text search over Obsidian vaults. It indexes Markdown files into SQLite + FTS5 and provides a single `vlt` CLI entry point with subcommands: `index`, `search`, `health`, `config`.

**模块职责:**

| 模块                  | 职责                                                           |
| --------------------- | -------------------------------------------------------------- |
| `cli.py`              | CLI命令解析与入口，使用SearchEngine和OutputFormatter           |
| `search.py`           | 搜索核心逻辑（SearchEngine），协调数据库查询和结果合并         |
| `database.py`         | 纯数据库操作（Database类），包含FTS5和LIKE搜索                 |
| `snippet.py`          | 智能摘要生成（SnippetGenerator），基于评分机制选择最优匹配     |
| `formatter.py`        | CLI输出格式化（OutputFormatter），支持文本/JSON/紧凑格式       |
| `models.py`           | 数据模型定义（Document, SearchResult）                         |
| `discovery.py`        | 文件发现                                                       |
| `parser.py`           | Markdown解析                                                   |
| `indexer.py`          | 索引构建                                                       |
| `config.py`           | 配置管理                                                       |
| `snippet_strategies/` | 内容类型处理策略（策略模式）：table/list/code_block/plain_text |

**Default DB path:** `<vault_root>/tmp/vault-search.sqlite`

## Design Documents

| Document                                       | Description      |
| ---------------------------------------------- | ---------------- |
| `docs/strategy-design/overview.md`             | 策略模式架构概览 |
| `docs/strategy-design/code_block.md`           | 代码块策略       |
| `docs/strategy-design/table.md`                | 表格策略         |
| `docs/strategy-design/list.md`                 | 列表策略         |
| `docs/strategy-design/plain_text.md`           | 普通文本策略     |
| `docs/2026-05-22-search-output-enhancement.md` | 搜索输出优化方案 |
| `docs/2026-05-22-search-refactoring.md`        | 查询逻辑重构设计 |

## Key conventions

- Codebase targets Python >= 3.10, uses `from __future__ import annotations` everywhere.
- Package uses `src` layout (`src/vault_search/`), configured via `pyproject.toml` with setuptools.
- Tests use `tmp_path` fixture for isolation and `sample_vault` (conftest) for a realistic multi-file vault structure.
- Config system: global (`~/.config/vault-search/config.json`) + project (`<vault>/.obsidian/vault-search.json`). No env vars.
- The index is a full rebuild every time (no incremental indexing in v1).

## Agent Rules

- **Do not directly modify code**: Before making any code changes, always propose the solution to the user first and wait for confirmation before implementing.
