# Vault Search: 代码提取执行计划

> **Prerequisite**: 先阅读 [提取方案设计文档](../specs/2026-05-11-vault-search-extraction.md)。
> **Constraint**: 本计划中所有步骤均**不修改** vault 内现有文件。代码在新项目目录中创建。

Date: 2026-05-11

## Goal

将 [Vault Search 实现计划](2026-05-10-vault-search.md) 中内嵌的 6 个 Task 的 Python 代码，提取为标准 Python 项目结构。

---

## Step 1: 创建项目骨架

### 目录与文件

```bash
mkdir -p vault-search/src/vault_search
mkdir -p vault-search/tests/fixtures/sample_vault
```

创建以下空文件（内容在后续步骤填写）：

```
vault-search/
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
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_discovery.py
│   ├── test_database.py
│   └── test_cli.py
```

### .gitignore

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.vscode/
.idea/
```

---

## Step 2: 创建 pyproject.toml

从原始计划的 3 个 wrapper `.py` 迁移为 `pyproject.toml` 入口：

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

[project.scripts]
vault-index = "vault_search.cli:main_index"
vault-search = "vault_search.cli:main_search"
vault-health = "vault_search.cli:main_health"

[tool.setuptools.package-dir]
vault_search = "src/vault_search"
```

---

## Step 3: 迁移源码模块

以下模块从原始计划中**原样复制代码**，无需任何改动：

### `src/vault_search/__init__.py`

```python
"""Vault search package."""

__version__ = "0.1.0"
```

### `src/vault_search/models.py`

与 [原始计划 Task 1 Step 4](2026-05-10-vault-search.md) 中的 `models.py` **完全一致**（dataclass 定义无任何路径依赖）。

### `src/vault_search/parser.py`

与 [原始计划 Task 1 Step 5](2026-05-10-vault-search.md) 中的 `parser.py` **完全一致**（纯 Markdown 解析逻辑，无外部依赖）。

### `src/vault_search/discovery.py`

与 [原始计划 Task 2 Step 3](2026-05-10-vault-search.md) 中的 `discovery.py` **完全一致**。

### `src/vault_search/database.py`

与 [原始计划 Task 3 Step 3](2026-05-10-vault-search.md) + [Task 5 Step 3](2026-05-10-vault-search.md) 中的 `database.py` **完全一致**（合并 `health_summary` 函数到同一文件）。

### `src/vault_search/indexer.py`

与 [原始计划 Task 4 Step 3](2026-05-10-vault-search.md) 中的 `indexer.py` **完全一致**。

---

## Step 4: 迁移 CLI（需微调）

`src/vault_search/cli.py` 需要将原始计划的单一 `main()` 函数拆分为 3 个独立入口，以适配 `pyproject.toml` 的 `[project.scripts]`：

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .database import health_summary, search_documents
from .indexer import build_index

DEFAULT_DB = Path("tmp/vault-search.sqlite")


def _build_parser():
    parser = argparse.ArgumentParser(prog="vault-search-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("vault-index")
    index_parser.add_argument("--root", default=".")
    index_parser.add_argument("--db", default=str(DEFAULT_DB))

    search_parser = subparsers.add_parser("vault-search")
    search_parser.add_argument("query")
    search_parser.add_argument("--db", default=str(DEFAULT_DB))
    search_parser.add_argument("--area")
    search_parser.add_argument("--tag", action="append", default=[])
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--json", action="store_true")

    health_parser = subparsers.add_parser("vault-health")
    health_parser.add_argument("--db", default=str(DEFAULT_DB))
    health_parser.add_argument("--json", action="store_true")

    return parser


def main_index():
    """Entry point for vault-index command."""
    parser = argparse.ArgumentParser(prog="vault-index")
    parser.add_argument("--root", default=".")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args(sys.argv[1:])
    summary = build_index(Path(args.root), Path(args.db))
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0


def main_search():
    """Entry point for vault-search command."""
    parser = argparse.ArgumentParser(prog="vault-search")
    parser.add_argument("query")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--area")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    results = search_documents(Path(args.db), query=args.query, limit=args.limit, area=args.area, tags=args.tag)
    payload = {"query": args.query, "results": results}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['path']} | {item['title']} | {', '.join(item['tags'])}")
    return 0


def main_health():
    """Entry point for vault-health command."""
    parser = argparse.ArgumentParser(prog="vault-health")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    payload = {"summary": health_summary(Path(args.db))}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload["summary"].items():
            print(f"{key}: {value}")
    return 0
```

变化点说明：
- 原来 `main(argv, capture)` 的单入口模式 → 3 个独立函数 `main_index/search/health`
- 原来 dispatch 逻辑由 `_build_parser()` + 子命令完成 → 每个入口自己的 `ArgumentParser`
- `capture` 模式移除——测试改为直接调用函数并捕获 stdout
- 输出落点：`print()` 直接写到 stdout（测试通过 mock 或 subprocess 验证）

---

## Step 5: 迁移测试（需调 import 路径）

### `tests/__init__.py`

空文件。

### `tests/test_parser.py`

与 [原始计划 Task 1 Step 1](2026-05-10-vault-search.md) 中的测试**逻辑完全一致**，唯一改动：

```python
# 原始: from code_scripts.vault_search.parser import parse_markdown
# 改为:
from vault_search.parser import parse_markdown
```

### `tests/test_discovery.py`

与 [原始计划 Task 2 Step 1](2026-05-10-vault-search.md) 中的测试**逻辑完全一致**，两项改动：

```python
# 1. import 路径
# 原始: from code_scripts.vault_search.discovery import discover_markdown_files, path_area
# 改为:
from vault_search.discovery import discover_markdown_files, path_area

# 2. fixture 路径（从项目根定位，不再硬编码）
# 原始: FIXTURE = Path("code-scripts/vault_search/tests/fixtures/sample_vault")
# 改为:
import os
FIXTURE = Path(os.path.dirname(__file__)) / "fixtures" / "sample_vault"
```

### `tests/test_database.py`

与 [原始计划 Task 3 Step 1](2026-05-10-vault-search.md) + [Task 4 Step 1](2026-05-10-vault-search.md) 的合并测试，仅改 import：

```python
# 原始
# from code_scripts.vault_search.database import rebuild_database, search_documents
# from code_scripts.vault_search.parser import parse_markdown
# from code_scripts.vault_search.indexer import build_index
# 改为:
from vault_search.database import rebuild_database, search_documents
from vault_search.parser import parse_markdown
from vault_search.indexer import build_index
```

### `tests/test_cli.py`

需适配新的 CLI 入口签名。原计划通过 `main()` + `capture=True` 捕获输出；独立后改为调用独立函数并捕获 stdout：

```python
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from vault_search.cli import main_index, main_search, main_health


class CliTests(unittest.TestCase):
    def _capture(self, func, *args):
        """Redirect stdout and run func, return captured string."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            func()
        except SystemExit:
            pass
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output

    def _setup_vault(self, root: Path):
        (root / "wiki").mkdir(parents=True)
        (root / "wiki" / "ssl.md").write_text(
            "---\ntags: [知识总结, network]\n---\n# SSL 证书\nSSL 证书用于 HTTPS。\n",
            encoding="utf-8",
        )
        (root / "note.md").write_text("# Untagged\n[[Missing]]\n", encoding="utf-8")

    def test_index_search_and_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._setup_vault(root)
            db_path = root / "tmp" / "vault-search.sqlite"

            # Patch sys.argv and call main_index
            old_argv = sys.argv
            try:
                sys.argv = ["vault-index", "--root", str(root), "--db", str(db_path)]
                index_output = self._capture(main_index)
            finally:
                sys.argv = old_argv

            # Search
            try:
                sys.argv = ["vault-search", "SSL", "--db", str(db_path), "--json"]
                search_output = self._capture(main_search)
            finally:
                sys.argv = old_argv

            payload = json.loads(search_output)
            self.assertEqual(payload["results"][0]["path"], "wiki/ssl.md")

            # Health
            try:
                sys.argv = ["vault-health", "--db", str(db_path), "--json"]
                health_output = self._capture(main_health)
            finally:
                sys.argv = old_argv

            health = json.loads(health_output)
            self.assertEqual(health["summary"]["missing_tags"], 1)
            self.assertEqual(health["summary"]["wikilinks"], 1)


if __name__ == "__main__":
    unittest.main()
```

---

## Step 6: 创建 Fixture Vault

与 [原始计划 Task 2 Step 4](2026-05-10-vault-search.md) 中的 fixture **完全一致**。

```
tests/fixtures/sample_vault/
├── README.md                          # # Fixture Vault
├── IT-learning/
│   └── java-basic/
│       └── java.md                    # ---\ntags: [学习, java]\n---\n\n# Java
├── wiki/
│   └── INDEX.md                       # # Wiki Index
├── tmp/
│   └── ignored.md                     # # Ignored
└── .obsidian/
    └── ignored.md                     # # Ignored
```

---

## Step 7: 安装并验证

### 安装

```bash
cd vault-search
pip install -e .
```

验证 CLI 可用：

```bash
vault-index --help
vault-search --help
vault-health --help
```

### 运行单元测试

```bash
cd vault-search
python -m unittest discover tests/ -v
```

期望通过：parser (3), discovery (2), database (1), indexer (1), cli (1) = **8 个测试全部 PASS**。

### 对真实 vault 建索引

```bash
cd vault-search
vault-index --root /path/to/obsidian-vault --db /path/to/obsidian-vault/tmp/vault-search.sqlite
vault-search "SSL" --db /path/to/obsidian-vault/tmp/vault-search.sqlite --json
vault-health --db /path/to/obsidian-vault/tmp/vault-search.sqlite --json
```

---

## Step 8: 更新 Vault 内的文档引用（可选，未来做）

如果独立项目后续有了 GitHub 仓库地址，可在 vault 的原始设计文档中添加一条指向新仓库的链接。**这不是本计划的执行范围，也不在本计划中修改任何现有文件。**

---

## 变更总结

| 类别 | 文件 | 变更量 |
|------|------|--------|
| 新增（项目） | `pyproject.toml` `.gitignore` `README.md` | 3 个新文件 |
| 零改动 | `models.py` `parser.py` `discovery.py` `database.py` `indexer.py` | 0 行 |
| 微调 | `cli.py`（拆分入口函数） | ~30 行变化 |
| import 路径 | 5 个测试文件 | 每文件 1-4 行 import 改动 |
| fixture 路径 | `tests/test_discovery.py` | 1 行路径改动 |
| 删除 | 3 个 wrapper `.py` + `code_scripts/` 包别名 | 不再需要 |
