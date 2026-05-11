# Vault Search: 代码提取为独立项目 — 设计文档

Date: 2026-05-11

## Purpose

将 [Vault Search 设计文档](2026-05-10-vault-search-design.md) 和 [实现计划](2026-05-10-vault-search.md) 中的技术实现部分（Python 代码、测试、CLI）从当前 Obsidian vault 中提取为独立的 Python 项目。Vault 保留设计文档和运行时配置，代码按标准 Python 工程结构独立管理。

## Why Extract

### 关注点分离

| 留在 vault（知识管理）                  | 提取到项目（软件工程）            |
| ------------------------------- | ---------------------- |
| 设计文档 / 实现计划                     | Python 源码              |
| 运行时配置 `meta/search-config.json` | 单元测试 + fixture         |
| Vault 标签/目录规范                   | `pyproject.toml` / 版本号 |

当前 vault 的 `docs/superpowers/plans/2026-05-10-vault-search.md` 内嵌了 ~1200 行 Python 代码——这混淆了"笔记仓库"和"代码仓库"的职责边界。

### 复用性

Vault Search CLI 设计为"给定任意 Obsidian vault 路径，建索引并搜索"——天然是通用工具，不应绑定在当前 vault 内。独立后可通过 `pip install` 或 `pipx` 安装到任意环境。

### 工程规范化

- 去掉 `code_scripts` / `code-scripts` 混淆命名
- 用 `pyproject.toml` 的 `[project.scripts]` 替代 3 个 wrapper `.py` 文件
- 标准的 `src/` + `tests/` 布局，任何 Python 开发者都能立即上手

## Non-Goals

- **不修改** `docs/superpowers/specs/2026-05-10-vault-search-design.md`
- **不修改** `docs/superpowers/plans/2026-05-10-vault-search.md`
- **不修改** vault 内的任何现有文件
- **不改变** 原始设计的功能范围（仍然是 V1 SQLite + FTS5）
- **不绑定** 新项目的位置——由执行者决定放在哪里

## Target Project Structure

```
vault-search/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── vault_search/
│       ├── __init__.py          # package marker + __version__
│       ├── models.py            # Document, Link, Heading dataclasses
│       ├── parser.py            # Markdown/frontmatter parser
│       ├── discovery.py         # File discovery + area detection
│       ├── database.py          # SQLite schema, FTS5 search, health queries
│       ├── indexer.py           # Build-index orchestration + link resolution
│       └── cli.py               # argparse CLI: vault-index/search/health
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_discovery.py
│   ├── test_database.py
│   ├── test_cli.py
│   └── fixtures/
│       └── sample_vault/        # 与原始计划一致的 fixture vault
│           ├── README.md
│           ├── IT-learning/
│           │   └── java-basic/
│           │       └── java.md
│           ├── wiki/
│           │   └── INDEX.md
│           ├── tmp/
│           │   └── ignored.md
│           └── .obsidian/
│               └── ignored.md
```

## Mapping: 原始计划 → 独立项目

| 原始计划路径 | 独立项目路径 | 变更 |
|---|---|---|
| `code_scripts/__init__.py` | 删除（`src/vault_search/` 即为包） | — |
| `code_scripts/vault_search/__init__.py` | `src/vault_search/__init__.py` | import 前缀变 |
| `code_scripts/vault_search/models.py` | `src/vault_search/models.py` | 无代码变更 |
| `code_scripts/vault_search/parser.py` | `src/vault_search/parser.py` | `from .models` 路径不变 |
| `code_scripts/vault_search/discovery.py` | `src/vault_search/discovery.py` | 无代码变更 |
| `code_scripts/vault_search/database.py` | `src/vault_search/database.py` | 无代码变更 |
| `code_scripts/vault_search/indexer.py` | `src/vault_search/indexer.py` | 无代码变更 |
| `code_scripts/vault_search/cli.py` | `src/vault_search/cli.py` | 无代码变更 |
| `code-scripts/vault-search.py` | 删除，用 `pyproject.toml` 入口替代 | — |
| `code-scripts/vault-index.py` | 删除，用 `pyproject.toml` 入口替代 | — |
| `code-scripts/vault-health.py` | 删除，用 `pyproject.toml` 入口替代 | — |
| `code-scripts/vault_search/tests/*` | `tests/*` | import 从 `code_scripts.vault_search` → `vault_search` |
| `code-scripts/vault_search/tests/fixtures/` | `tests/fixtures/` | fixture 内容不变 |
| `code-scripts/vault_search/README.md` | `README.md`（项目根） | 去掉 vault 内路径引用 |

### 唯一需要改代码的地方

1. **测试文件**：`from code_scripts.vault_search.xxx` → `from vault_search.xxx`
2. **fixture 路径**：`Path("code-scripts/vault_search/tests/fixtures/sample_vault")` → `Path(__file__).parent / "fixtures" / "sample_vault"`
3. **CLI 入口**：3 个 wrapper `.py` 文件替换为 `pyproject.toml` 的 `[project.scripts]`

其余模块代码（models, parser, discovery, database, indexer, cli）**零改动**。

## pyproject.toml 设计

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "vault-search"
version = "0.1.0"
description = "Local SQLite + FTS5 full-text search for Obsidian vaults"
requires-python = ">=3.10"
license = {text = "MIT"}
readme = "README.md"

[project.scripts]
vault-index = "vault_search.cli:main_index"
vault-search = "vault_search.cli:main_search"
vault-health = "vault_search.cli:main_health"
[tool.setuptools.package-dir]
vault_search = "src/vault_search"
```

注：为支持 `pyproject.toml` 的独立入口函数，`cli.py` 需微调——将原来的 `main()` 函数拆分为 `main_index()`、`main_search()`、`main_health()` 三个独立入口（或用一个入口 + `argv[1]` dispatcher）。推荐拆分方式：

```python
# cli.py 调整示意（非完整代码）
import sys

def main_index():
    from .indexer import build_index
    # ... 解析 --root --db
    sys.exit(0)

def main_search():
    from .database import search_documents
    # ... 解析 query --db
    sys.exit(0)

def main_health():
    from .database import health_summary
    # ... 解析 --db
    sys.exit(0)
```

这比原始计划的 3 个 wrapper `.py` 文件更干净，且可以分别 `pip install` 后直接调用。

## API Boundary: 运行时与 Vault 的关系

独立项目通过 `--root` 参数与 vault 交互：

```bash
# 安装后
vault-index --root ~/my-obsidian-vault
vault-search "java 泛型" --root ~/my-obsidian-vault
vault-health --root ~/my-obsidian-vault
```

- 工具本身不包含任何 vault 数据
- 数据库默认写入 vault 内的 `tmp/vault-search.sqlite`（该路径由 `.gitignore` 排除）
- 运行时配置从 vault 的 `meta/search-config.json` 加载（V1 可先硬编码默认值）

## What Stays in the Vault

| 文件 | 角色 |
|------|------|
| `docs/superpowers/specs/2026-05-10-vault-search-design.md` | 设计规格——项目文档的"为什么" |
| `docs/superpowers/plans/2026-05-10-vault-search.md` | 实现计划——项目文档的"怎么做" |
| `docs/superpowers/specs/2026-05-11-vault-search-extraction.md` | 本文档——提取方案设计 |
| `docs/superpowers/plans/2026-05-11-vault-search-extraction.md` | 提取执行计划 |
| `meta/search-config.json` | 运行时配置——由独立工具读取 |
| `tmp/vault-search.sqlite` | 衍生索引数据——由独立工具写入 |

原 `code-scripts/`、`code_scripts/` 路径在本方案中不会创建，代码直接在新项目中落地。

## Roadmap Alignment

独立项目的版本路线与原始设计同步：

- **v0.1.0** = V1 范围：SQLite + FTS5，全量重建，CLI 搜索 + health，JSON 输出
- **v0.2.0** = V2 范围：语义检索（embeddings）
- **v0.3.0** = V3 范围：知识图谱分析
- **v0.4.0** = V4 范围：本地 Web UI

## Testing Strategy

独立项目测试与原计划一致，只是测试文件路径变更：

- 使用 `tests/fixtures/sample_vault/` 作为 fixture vault
- `python -m pytest` 或 `python -m unittest discover tests/`
- CI/CD 可独立运行，不依赖真实 vault

## Open Decision

- **项目托管位置**：本地单独目录、GitHub 独立仓库、还是 monorepo 子目录？由执行者决定。本方案不绑定具体位置。
