# Vault Search

Local-first command line search for Obsidian vaults.

Vault Search indexes Markdown files from an Obsidian vault into SQLite + FTS5 and provides CLI commands for search and lightweight vault health checks.

## 安装

Prerequisite: Python >= 3.10。

创建并激活虚拟环境：

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

安装项目和依赖：

```bash
# macOS / Linux
python3 -m pip install --upgrade pip
python3 -m pip install -e .

# Windows
python -m pip install --upgrade pip
python -m pip install -e .
```

验证安装：

```bash
# macOS / Linux
python3 -c "import vault_search; print(vault_search.__version__)"

# Windows
python -c "import vault_search; print(vault_search.__version__)"
```

每次新开终端使用前，先激活虚拟环境：

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

## 使用

### 1. 建立索引

```bash
vault-index --root /path/to/your-vault
```

`--root` 指向你的 Obsidian vault 根目录（包含 `.obsidian/` 隐藏文件夹的那个目录）。索引文件默认生成在 `<vault>/tmp/vault-search.sqlite`。

vault 内容有新增或修改后，重新执行一次 `vault-index` 即可全量重建索引。

### 2. 搜索

```bash
# 基础搜索
vault-search "关键词" --root /path/to/your-vault

# JSON 格式输出
vault-search "关键词" --root /path/to/your-vault --json

# 按区域和标签过滤
vault-search "关键词" --root /path/to/your-vault --area notes --tag python
```

支持中文关键词，底层使用 SQLite FTS5 + LIKE 回退。

### 3. 健康检查

```bash
vault-health --root /path/to/your-vault
vault-health --root /path/to/your-vault --json
```

### 使用 --db 替代 --root

如果不想每次指定 `--root`，可以直接用 `--db` 指向已生成的索引文件：

```bash
vault-search "关键词" --db /path/to/vault/tmp/vault-search.sqlite
```

## 功能特性

- Markdown 文件发现，自动忽略 `.obsidian/`、`.git/`、`tmp/` 等运行时目录
- YAML frontmatter 和行内标签提取
- 标题层级提取
- Wikilink 提取及基础解析
- SQLite + FTS5 关键词搜索
- 中文友好的 `LIKE` 回退匹配
- JSON 输出，便于脚本集成
- 轻量健康指标

## 开发

主要代码路径：

- `src/vault_search/parser.py` — Markdown 解析
- `src/vault_search/discovery.py` — vault 文件发现
- `src/vault_search/database.py` — SQLite 模式、搜索与健康查询
- `src/vault_search/indexer.py` — 索引构建编排
- `src/vault_search/cli.py` — CLI 入口
- `tests/` — 测试覆盖

安装测试依赖并运行：

```bash
# macOS / Linux
python3 -m pip install pytest
python3 -m pytest -v

# Windows
python -m pip install pytest
python -m pytest -v
```

## 限制

V1 不包含语义搜索、增量索引、Web 界面、Obsidian 插件或高级知识图谱分析。
