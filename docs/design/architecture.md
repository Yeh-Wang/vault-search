# Vault Search 架构文档

Date: 2026-05-12

本文档描述 Vault Search 当前的实际架构，替代原始设计文档作为后续开发的基线参考。

## 1. 项目概述

Vault Search 是一个面向 Obsidian vault 的本地命令行搜索工具。它将 Markdown 笔记索引到 SQLite + FTS5，通过统一的 `vlt` CLI 提供搜索、健康检查和配置管理功能。

## 2. 技术栈

| 层面 | 选型 |
|------|------|
| 语言 | Python >= 3.10 |
| 包管理 | uv（替代 pip/pyenv） |
| 构建 | setuptools + pyproject.toml |
| 数据库 | SQLite + FTS5（标准库） |
| CLI | argparse subparsers |
| 测试 | pytest |
| 外部依赖 | 无 |

## 3. 项目结构

```
vault-search/
├── pyproject.toml              # 包元数据、入口点、依赖
├── .python-version             # Python 版本（3.13）
├── uv.lock                     # uv 锁文件
├── README.md                   # 用户指南 + 开发者指南
├── CLAUDE.md                   # AI 协作指令
├── src/vault_search/
│   ├── __init__.py             # 包标记 + __version__
│   ├── models.py               # 数据模型（Document, Heading, Link）
│   ├── parser.py               # Markdown 解析
│   ├── discovery.py            # 文件发现
│   ├── database.py             # SQLite schema、FTS5 搜索、健康查询
│   ├── indexer.py              # 索引编排 + wikilink 解析
│   ├── config.py               # 配置管理（全局 + 项目级）
│   └── cli.py                  # CLI 入口（vlt 统一命令）
├── tests/
│   ├── conftest.py             # sample_vault fixture
│   ├── test_parser.py          # 解析器测试（3）
│   ├── test_discovery.py       # 文件发现测试（2）
│   ├── test_database.py        # 数据库测试（4）
│   ├── test_indexer.py         # 索引器测试（2）
│   ├── test_cli.py             # CLI 集成测试（14）
│   └── test_config.py          # 配置模块测试（13）
└── docs/                       # 设计文档（历史 + 当前）
```

共 38 个测试用例。

## 4. CLI 设计

### 入口点

单一入口点 `vlt`，通过 argparse subparsers 分发：

```toml
[project.scripts]
vlt = "vault_search.cli:main"
```

### 子命令

```
vlt index   [--root <path>] [--db <path>]
vlt search  <query> [--root] [--db] [--area] [--tag] [--limit] [--json]
vlt health  [--root] [--db] [--json]
vlt config  set <key> <value> [--local] [--root <path>]
vlt config  get <key> [--root <path>]
vlt config  list [--root <path>]
vlt config  path
```

所有参数均带有中文 `help` 描述，`--help` 全层级可用。

### 错误处理

CLI 层使用 `_CliError` 异常封装错误，由 `main()` 统一捕获后输出到 stderr 并返回非零退出码：

```python
class _CliError(Exception):
    """CLI 层错误，由 main() 捕获后输出到 stderr 并退出。"""
    pass
```

辅助函数（如 `_auto_build_index_if_needed`）抛出 `_CliError` 而非直接调用 `sys.exit()`，保证可测试性。

### 自动建索引

`search` 和 `health` 子命令在数据库不存在时自动调用 `build_index()`，前提是能确定 vault root。如果只有 `--db` 没有 root，则报错。

### Windows UTF-8

CLI 启动时自动将 stdout/stderr 编码设为 UTF-8，确保中文输出不乱码。

## 5. 配置系统

### 配置文件位置

| 范围 | 路径 |
|------|------|
| 全局 | `~/.config/vault-search/config.json`（`Path.home() / ".config" / "vault-search" / "config.json"`） |
| 项目 | `<vault>/.obsidian/vault-search.json` |

统一使用 `Path.home()`，Windows 和 macOS 无平台分支。

### Root 解析优先级

```
CLI --root  >  自动检测 .obsidian/  >  全局配置 default_root
```

`resolve_root(args_root)` 实现此链路。项目级配置不参与 root 解析（需要先知道 root 才能读取，存在循环依赖）。

### Setting 合并

```
项目级配置  >  全局配置  >  硬编码默认值
```

`resolve_setting(key, vault_root, default)` 实现合并逻辑。当前可配置项：

| 键 | 说明 | 默认值 |
|----|------|--------|
| `default_root` | vault 根路径（仅全局配置有效） | 无 |
| `default_limit` | 搜索返回结果数 | 10 |

### Limit 解析链

```
CLI --limit  >  项目配置 default_limit  >  全局配置 default_limit  >  硬编码 10
```

## 6. 数据流水线

```
discovery → parser → indexer → database
  (发现)     (解析)   (编排)    (存储)
```

### discovery.py

遍历 vault root 查找 `*.md` 文件，跳过忽略目录。返回 `DiscoveredFile` 列表。

默认忽略目录：`.obsidian/`, `.git/`, `tmp/`, `.trash/`, `node_modules/`, `.venv/`, `.pytest_cache/`

每个文件包含：`relative_path`（POSIX 格式）、`area`（顶层目录名或 `"root"`）、`mtime`。

### parser.py

解析单个 Markdown 文件为 `Document`。提取内容：

- YAML frontmatter（`tags:` 字段，支持行内数组 `[a, b]`、列表 `- a`、简单字符串）
- 标题层级（`#` 到 `######`）
- Wikilink（`[[target]]`, `[[target|alias]]`, `[[target#section]]`）
- 行内标签（`#tag`，支持中文字符 `\u4e00-\u9fff`）

标题解析优先级：第一个 heading > frontmatter `title:` > 文件名 stem

### indexer.py

编排 discovery + parsing + link resolution，调用 `rebuild_database()`。

Wikilink 解析按优先级匹配：path > title > stem。`#section` 片段会被剥离后匹配。

### database.py

SQLite schema：

- `documents` — 路径、标题、区域、正文、mtime、是否显式标题
- `document_tags` — 文档-标签对
- `headings` — 标题层级
- `wikilinks` — wikilink 及解析结果
- `documents_fts` — FTS5 虚拟表（title + body）
- `index_meta` — 元数据（如 ignored_files 计数）

搜索策略：
1. FTS5 MATCH 查询
2. 如果 FTS5 无结果或查询含 CJK 字符，触发 `LIKE` 回退
3. 合并去重，按 limit 截断

默认索引路径：`<vault_root>/tmp/vault-search.sqlite`

索引为全量重建，无增量模式。

## 7. 数据模型

```python
@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int

@dataclass(frozen=True)
class Link:
    target: str
    alias: str | None
    line: int
    resolved_path: str | None

@dataclass(frozen=True)
class Document:
    path: str
    title: str
    area: str
    tags: list[str]
    headings: list[Heading]
    links: list[Link]
    body: str
    mtime: float
    explicit_title: bool
```

## 8. 测试策略

使用 pytest + `tmp_path` 隔离 + `sample_vault` fixture（conftest.py）。

Fixture vault 结构：4 个 markdown 文件 + 2 个被忽略文件（`.obsidian/`, `tmp/`）+ 1 个非 md 文件。

测试覆盖：

| 模块 | 测试数 | 覆盖内容 |
|------|--------|---------|
| parser | 3 | frontmatter/tags/headings/wikilink/标题回退 |
| discovery | 2 | 文件发现 + 忽略目录 + area 检测 |
| database | 4 | FTS5 搜索 + 中文回退 + 过滤 + 健康指标 |
| indexer | 2 | 端到端索引 + 空 vault |
| cli | 14 | 所有子命令 + 配置 + 自动建索引 + 错误路径 |
| config | 13 | 配置路径/加载/保存/解析优先级/合并 |

CLI 测试通过 `monkeypatch.setattr(sys, "argv", ...)` 模拟命令行调用，`capsys` 捕获输出。

## 9. 全局工具安装

通过 uv 安装为全局工具：

```bash
uv tool install -e .
```

可执行文件安装到 `~/.local/bin/vlt`，editable 模式（符号链接到源码），代码修改即时生效。

## 10. 与原始设计的差异

| 维度 | 原始设计（v0.1.0 计划） | 当前实现 |
|------|------------------------|---------|
| CLI | 三个独立命令（vault-index/search/health） | 统一 `vlt` + 子命令 |
| 配置 | 无，所有参数硬编码 | 全局 + 项目级配置系统 |
| vault 识别 | 必须传 `--root` | 自动检测 `.obsidian/` + 配置回退 |
| 包管理 | pip/pyenv | uv |
| 自动建索引 | 数据库不存在时报错 | 自动调用 build_index |
| 错误处理 | `sys.exit()` 直接退出 | `_CliError` 异常模式 |
| config 子命令 | 无 | `vlt config set/get/list/path` |
| Windows 支持 | 未考虑 | UTF-8 输出修复 |
| 测试 | 8 个 | 38 个 |

## 11. 已知限制

- 索引为全量重建，无增量模式
- 搜索排序简单，无相关性评分
- Frontmatter 解析仅支持 YAML 子集
- Snippet 生成基础
- 无语义搜索/向量检索
- 无 Web UI / Obsidian 插件
- 无知识图谱分析

## 12. 路线图

| 版本 | 目标 |
|------|------|
| v0.1.0 | 当前状态：FTS5 + 配置 + 统一 CLI |
| v0.2.0 | 增量索引、搜索排序优化、frontmatter 增强 |
| v0.3.0 | 语义搜索/向量检索调研 |
| v0.4.0 | 知识图谱分析 |
| v0.5.0 | Web UI / Obsidian 插件 |
