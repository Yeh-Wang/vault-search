# Vault Search

Local-first command line search for Obsidian vaults.

Vault Search indexes Markdown files from an Obsidian vault into SQLite + FTS5 and provides CLI commands for search and lightweight vault health checks.

---

## 用户指南

### 安装

Prerequisite: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python >= 3.10。

```bash
# 从源码安装（开发阶段）
git clone <repo-url> && cd vault-search
uv sync
uv tool install -e .
```

安装后 `vlt` 命令全局可用。如果提示找不到命令，将 `~/.local/bin` 加入 PATH：

```bash
# Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# PowerShell
$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
```

### 快速开始

```bash
# 1. 配置 vault 路径（一次即可）
vlt config set default_root "D:\Personal Files\_private-notes"

# 2. 建立索引
vlt index

# 3. 搜索笔记
vlt search "python"
```

### 配置 vault 路径（三选一）

不需要每次输入 `--root`，三种方式自动识别 vault：

**方式 1：在 vault 目录内运行（零配置）**

工具自动向上查找 `.obsidian/` 目录识别 vault root，无需任何配置。

**方式 2：全局配置（推荐）**

```bash
vlt config set default_root "D:\Personal Files\_private-notes"
```

配置文件位于 `~/.config/vault-search/config.json`，设置一次全局生效。

**方式 3：项目级配置**

```bash
# 在 vault 目录内执行，或用 --root 指定
vlt config set default_limit 20 --local
vlt config set default_limit 20 --local --root "D:\Personal Files\_private-notes"
```

配置写入 `<vault>/.obsidian/vault-search.json`，随 vault 走。

### 命令参考

```bash
vlt index [--root <vault路径>] [--db <数据库路径>]              # 建立索引
vlt search <查询词> [--root] [--db] [--area] [--tag] [--limit] [--json] [--compact]  # 搜索
vlt health [--root] [--db] [--json]                            # 健康检查
vlt config set <key> <value> [--local] [--root <vault路径>] # 设置配置
vlt config get <key> [--root <vault路径>]                  # 查看配置
vlt config list [--root <vault路径>]                       # 列出配置
vlt config path                                            # 配置文件路径
```

配置优先级：CLI 参数 > 项目级配置 > 全局配置 > 自动检测。

### 使用场景

#### 场景 1：终端里快速查笔记

不想打开 Obsidian，在终端里直接搜。适合开发者工作流中快速查找资料。

```bash
vlt search "泛型"
vlt search "SSL 证书"
```

输出示例：

```
--- Result 1 ---
  Title:  SSL 证书
  Path:   wiki/ssl.md
  Tags:   network, 知识总结
  Match:  SSL 证书用于 HTTPS。
```

#### 场景 2：缩小搜索范围

按区域（顶层目录）或标签过滤，快速定位到特定类别的笔记。

```bash
# 只在 IT-learning 区域搜
vlt search "java" --area IT-learning

# 搜带特定标签的笔记
vlt search "学习" --tag python

# 组合过滤
vlt search "异步" --area IT-learning --tag python
```

当前 vault 的区域分布（供 `--area` 参考用）：

| 区域            | 说明         |
| --------------- | ------------ |
| IT-learning     | 技术学习笔记 |
| next-level-door | 下一扇门     |
| basic-data      | 基础数据     |
| Clippings       | 网页剪藏     |
| code-scripts    | 代码脚本     |
| docs            | 文档         |
| wiki            | 百科         |
| archives-years  | 年度归档     |
| meta            | 元信息       |

#### 场景 3：脚本自动化

`--json` 输出可被 `jq`、Python 等工具消费，用于自动化场景。

```bash
# 统计搜索结果数量
vlt search "python" --json | python -c "import sys,json; print(len(json.load(sys.stdin)['results']))"

# 导出某区域所有笔记路径
vlt search " " --area IT-learning --limit 100 --json | python -c "import sys,json; [print(r['path']) for r in json.load(sys.stdin)['results']]"
```

#### 场景 4：定期检查 vault 质量

健康检查帮助发现 vault 维护问题：断链、缺标签、缺标题。

```bash
vlt health --json
```

输出示例：

```json
{
  "summary": {
    "documents": 90,
    "areas": { "IT-learning": 22, "next-level-door": 15, ... },
    "tags": 30,
    "missing_tags": 61,
    "missing_titles": 13,
    "wikilinks": 24,
    "broken_wikilinks": 21,
    "ignored_files": 6
  }
}
```

重点关注：

- **`broken_wikilinks`** — 指向不存在笔记的 wikilink，需要修复
- **`missing_tags`** — 没有任何标签的笔记数量
- **`missing_titles`** — 没有标题（无 H1、无 frontmatter title）的笔记数量

#### 场景 5：用 --db 直接指定索引文件

如果有多个 vault 或想指定索引位置，可以用 `--db` 替代 `--root`：

```bash
vlt index --root "D:\Personal Files\_private-notes" --db /tmp/vault.sqlite
vlt search "关键词" --db /tmp/vault.sqlite
```

### 日常使用流程

```
首次 → vlt config set default_root "<vault路径>"  （一次配置）
     → vlt index
         ↓
日常 → vlt search "关键词"
         ↓
定期 → vlt health --json
       （检查断链、缺标签等问题）
         ↓
内容变动后 → vlt index（全量重建，速度较快）
```

### 功能特性

- Markdown 文件发现，自动忽略 `.obsidian/`、`.git/`、`tmp/` 等运行时目录
- YAML frontmatter 和行内标签提取
- 标题层级提取
- Wikilink 提取及基础解析
- SQLite + FTS5 关键词搜索
- 中文友好的 `LIKE` 回退匹配
- JSON 输出，便于脚本集成
- **智能摘要生成**：基于评分机制选择最优匹配行
- **策略模式**：针对表格、列表、代码块等内容类型采用不同处理策略
- **动态匹配数量**：根据文档长度自动调整（2-5个匹配）
- **多种输出格式**：支持文本、JSON、紧凑格式（`--compact`）
- 轻量健康指标
- 自动检测 vault 目录（向上查找 `.obsidian/`）
- 全局 + 项目级配置系统

### 限制

V1 不包含语义搜索、增量索引、Web 界面、Obsidian 插件或高级知识图谱分析。

---

## 开发者指南

### 开发环境搭建

```bash
# 安装依赖（自动创建 .venv + uv.lock）
uv sync

# 验证安装
uv run python -c "import vault_search; print(vault_search.__version__)"
```

### 运行测试

```bash
# 全量测试
uv run pytest -v

# 单个文件
uv run pytest tests/test_parser.py -v

# 单个用例
uv run pytest tests/test_parser.py::test_parse_markdown_frontmatter_headings_tags_and_links -v
```

### 项目结构

```
src/vault_search/
  cli.py              # CLI 入口（vlt 统一命令，argparse subparsers）
  config.py           # 配置管理（全局 + 项目级）
  indexer.py          # 索引构建编排
  database.py         # SQLite schema、FTS5 搜索、健康查询（Database 类）
  search.py           # 搜索核心逻辑（SearchEngine 类）
  snippet.py          # 智能摘要生成（SnippetGenerator 类）
  formatter.py        # CLI 输出格式化（OutputFormatter 类）
  parser.py           # Markdown 解析（frontmatter、标题、标签、wikilink）
  discovery.py        # vault 文件发现（忽略运行时目录）
  models.py           # 数据模型（Document, SearchResult, Heading, Link）
  snippet_strategies/ # 内容类型处理策略（策略模式）
    __init__.py
    base.py
    code_block.py
    table.py
    list.py
    plain_text.py
tests/
  conftest.py     # sample_vault fixture
  test_cli.py     # CLI 集成测试
  test_config.py  # 配置模块测试
  test_database.py
  test_discovery.py
  test_indexer.py
  test_parser.py
```

### 架构

**数据流水线：** `discovery` → `parser` → `indexer` (→ `database`)

- **`discovery.py`** — walks a vault root for `*.md` files, skips ignored dirs (`.obsidian/`, `.git/`, `tmp/`, `.venv/`, `node_modules/`, `.trash/`, `.pytest_cache/`). Returns `DiscoveredFile` objects with `relative_path`, `area` (top-level dir or `"root"`), and `mtime`.
- **`parser.py`** — parses a single Markdown file into a `Document` dataclass. Extracts: YAML frontmatter (title, tags), headings (`#`), wikilinks (`[[target|alias]]`), inline tags (`#tag`). Title resolution: first heading > frontmatter `title:` > filename stem. Supports Chinese characters in inline tags.
- **`indexer.py`** — orchestrates discovery + parsing + link resolution, then calls `rebuild_database()`. Link resolution matches wikilink targets against document paths, titles, and stems (in that order), stripping `#section` fragments.
- **`database.py`** — SQLite schema management, full-text search, and health queries. Uses FTS5 for keyword search with a Chinese-friendly `LIKE` fallback (triggered when FTS5 returns nothing for CJK queries). Schema: `documents`, `document_tags`, `headings`, `wikilinks`, `documents_fts` (virtual), `index_meta`. Now encapsulated in a `Database` class with backward-compatible function wrappers.
- **`search.py`** — Search engine core (`SearchEngine` class). Coordinates database queries, merges FTS and LIKE results, and builds `SearchResult` objects with smart snippets.
- **`snippet.py`** — Smart snippet generator (`SnippetGenerator` class). Uses scoring mechanism (title match +30, query position +0~20, frequency +15/occurrence, line length +10) and strategy pattern for content type handling. Dynamic match count based on document length (2-5 matches).
- **`formatter.py`** — CLI output formatter (`OutputFormatter` class). Supports text (human-readable), JSON, and compact (one-line-per-result) formats. Handles multi-line snippet indentation and truncation of long paths/tags.
- **`cli.py`** — argparse subcommands under `vlt` entry point. Root resolution: CLI `--root` > auto-detect `.obsidian/` from cwd > global config `default_root`. Auto-builds index when database missing. Errors in helpers use `_CliError` exception, caught in `main()` for clean exit codes. Uses new `SearchEngine` and `OutputFormatter` interfaces.
- **`config.py`** — global config at `~/.config/vault-search/config.json`, project config at `<vault>/.obsidian/vault-search.json`. `resolve_root()` implements the priority chain. `resolve_setting()` merges project > global settings.

**默认索引路径：** `<vault_root>/tmp/vault-search.sqlite`

### 约定

- Python >= 3.10，所有文件使用 `from __future__ import annotations`
- `src` layout + setuptools（`pyproject.toml`）
- 测试使用 `tmp_path` 隔离，`sample_vault` (conftest) 提供真实多文件 vault 结构
- 配置系统：全局 (`~/.config/vault-search/config.json`) + 项目 (`<vault>/.obsidian/vault-search.json`)，不使用环境变量
- V1 索引为全量重建，无增量索引
