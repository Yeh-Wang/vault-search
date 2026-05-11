# Vault Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1 Vault Search Python CLI described in `docs/2026-05-11-vault-search-project-blueprint.md`.

**Architecture:** The repository root becomes the Python project root. Core behavior is split into focused modules: parser, discovery, database, indexer, and CLI. V1 uses full rebuild indexing into SQLite + FTS5, with a simple Chinese-friendly `LIKE` fallback for CJK queries.

**Tech Stack:** Python `>=3.10`, `setuptools`, `pytest`, standard library `argparse`, `sqlite3`, `pathlib`, `dataclasses`, and `json`.

---

## File Structure

Create these files:

- `pyproject.toml`: package metadata, pytest config, console scripts.
- `.gitignore`: Python development ignores.
- `README.md`: public usage and development entry point.
- `src/vault_search/__init__.py`: package marker and version.
- `src/vault_search/models.py`: `Document`, `Heading`, and `Link` dataclasses.
- `src/vault_search/parser.py`: Markdown/frontmatter/tag/heading/wikilink parser.
- `src/vault_search/discovery.py`: Markdown file discovery, ignored directory tracking, area detection.
- `src/vault_search/database.py`: SQLite schema, full rebuild, search, health summary.
- `src/vault_search/indexer.py`: orchestration for discovery, parsing, wikilink resolution, and database rebuild.
- `src/vault_search/cli.py`: `vault-index`, `vault-search`, and `vault-health` entry points.
- `tests/__init__.py`: test package marker.
- `tests/conftest.py`: shared fixture vault helpers.
- `tests/test_parser.py`: parser behavior tests.
- `tests/test_discovery.py`: discovery and area tests.
- `tests/test_database.py`: database rebuild, search, fallback, and health tests.
- `tests/test_indexer.py`: end-to-end index build tests.
- `tests/test_cli.py`: CLI contract tests.

Do not create a nested `vault-search/` directory inside the current repository.

---

## Task 1: Create Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/vault_search/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create package and test directories**

Run:

```bash
mkdir -p src/vault_search tests
touch tests/__init__.py
```

Expected: directories exist at repository root.

- [ ] **Step 2: Write `pyproject.toml`**

Create:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "vault-search"
version = "0.1.0"
description = "Local SQLite + FTS5 full-text search for Obsidian vaults"
requires-python = ">=3.10"
readme = "README.md"
license = {text = "MIT"}

[project.scripts]
vault-index = "vault_search.cli:main_index"
vault-search = "vault_search.cli:main_search"
vault-health = "vault_search.cli:main_health"

[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: Write `.gitignore`**

Create:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
dist/
build/
*.egg-info/
.DS_Store
.vscode/
.idea/
tmp/
```

- [ ] **Step 4: Write package init**

Create `src/vault_search/__init__.py`:

```python
"""Local search tools for Obsidian vaults."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Add initial README placeholder**

Create `README.md`:

````markdown
# Vault Search

Local-first command line search for Obsidian vaults.

This project is under active V1 implementation. See `docs/2026-05-11-vault-search-project-blueprint.md` for the project blueprint.
```

- [ ] **Step 6: Verify package metadata**

Run:

```bash
python -m pip install -e .
python -c "import vault_search; print(vault_search.__version__)"
```

Expected output includes:

```text
0.1.0
```

---

## Task 2: Implement Core Models

**Files:**
- Create: `src/vault_search/models.py`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Write failing model smoke test**

Create `tests/test_parser.py`:

```python
from vault_search.models import Document, Heading, Link


def test_document_model_smoke():
    heading = Heading(level=1, text="Title", line=3)
    link = Link(target="Other Note", alias="Other", line=5)
    doc = Document(
        path="wiki/title.md",
        title="Title",
        area="wiki",
        tags=["knowledge"],
        headings=[heading],
        links=[link],
        body="# Title\n[[Other Note|Other]]\n",
        mtime=123.0,
        explicit_title=True,
    )

    assert doc.path == "wiki/title.md"
    assert doc.headings[0].text == "Title"
    assert doc.links[0].alias == "Other"
    assert doc.explicit_title is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_parser.py::test_document_model_smoke -v
```

Expected: FAIL with an import error for `vault_search.models`.

- [ ] **Step 3: Implement models**

Create `src/vault_search/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int


@dataclass(frozen=True)
class Link:
    target: str
    alias: str | None = None
    line: int = 0
    resolved_path: str | None = None


@dataclass(frozen=True)
class Document:
    path: str
    title: str
    area: str
    tags: list[str] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    body: str = ""
    mtime: float = 0.0
    explicit_title: bool = False
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_parser.py::test_document_model_smoke -v
```

Expected: PASS.

---

## Task 3: Implement Markdown Parser

**Files:**
- Modify: `src/vault_search/parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Add parser tests**

Append to `tests/test_parser.py`:

```python
from vault_search.parser import parse_markdown


def test_parse_markdown_frontmatter_headings_tags_and_links():
    text = """---
title: SSL Guide
tags: [network, 知识总结]
---
# SSL 证书

正文包含 #https 和 [[TLS|Transport Layer Security]]。

## Details
See [[Missing Note#Section]].
"""

    doc = parse_markdown(
        text,
        path="wiki/ssl.md",
        area="wiki",
        mtime=10.0,
    )

    assert doc.path == "wiki/ssl.md"
    assert doc.title == "SSL 证书"
    assert doc.explicit_title is True
    assert doc.tags == ["network", "知识总结", "https"]
    assert [heading.text for heading in doc.headings] == ["SSL 证书", "Details"]
    assert doc.links[0].target == "TLS"
    assert doc.links[0].alias == "Transport Layer Security"
    assert doc.links[1].target == "Missing Note#Section"
    assert "title: SSL Guide" not in doc.body


def test_parse_markdown_uses_filename_fallback_title():
    doc = parse_markdown("No heading here", path="notes/my-note.md", area="notes", mtime=1.0)

    assert doc.title == "my-note"
    assert doc.explicit_title is False
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run:

```bash
python -m pytest tests/test_parser.py -v
```

Expected: FAIL with an import error for `vault_search.parser`.

- [ ] **Step 3: Implement parser**

Create `src/vault_search/parser.py`:

```python
from __future__ import annotations

import re
from pathlib import Path

from .models import Document, Heading, Link

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
INLINE_TAG_RE = re.compile(r"(?<!\w)#([\w\-\u4e00-\u9fff]+)")


def parse_markdown(text: str, path: str, area: str, mtime: float = 0.0) -> Document:
    frontmatter, body = _split_frontmatter(text)
    frontmatter_tags = _parse_frontmatter_tags(frontmatter)
    headings = _parse_headings(body)
    links = _parse_links(body)
    inline_tags = _parse_inline_tags(body)
    tags = _dedupe(frontmatter_tags + inline_tags)
    title, explicit_title = _choose_title(frontmatter, headings, path)

    return Document(
        path=path,
        title=title,
        area=area,
        tags=tags,
        headings=headings,
        links=links,
        body=body,
        mtime=mtime,
        explicit_title=explicit_title,
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            if text.endswith("\n"):
                body += "\n"
            return frontmatter, body

    return "", text


def _parse_frontmatter_tags(frontmatter: str) -> list[str]:
    tags: list[str] = []
    lines = frontmatter.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("tags:"):
            value = stripped.partition(":")[2].strip()
            if value.startswith("[") and value.endswith("]"):
                tags.extend(part.strip().strip("\"'") for part in value[1:-1].split(","))
            elif value:
                tags.extend(value.strip().strip("\"'").split())
            else:
                for nested in lines[index + 1 :]:
                    nested = nested.strip()
                    if not nested.startswith("- "):
                        break
                    tags.append(nested[2:].strip().strip("\"'"))
            break
    return [tag for tag in tags if tag]


def _parse_headings(body: str) -> list[Heading]:
    headings: list[Heading] = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(level=len(match.group(1)), text=match.group(2), line=line_number))
    return headings


def _parse_links(body: str) -> list[Link]:
    links: list[Link] = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        for match in WIKILINK_RE.finditer(line):
            links.append(Link(target=match.group(1).strip(), alias=(match.group(2) or "").strip() or None, line=line_number))
    return links


def _parse_inline_tags(body: str) -> list[str]:
    return [match.group(1) for match in INLINE_TAG_RE.finditer(body)]


def _choose_title(frontmatter: str, headings: list[Heading], path: str) -> tuple[str, bool]:
    if headings:
        return headings[0].text, True

    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("title:"):
            title = stripped.partition(":")[2].strip().strip("\"'")
            if title:
                return title, True

    return Path(path).stem, False


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
python -m pytest tests/test_parser.py -v
```

Expected: all parser tests PASS.

---

## Task 4: Implement File Discovery

**Files:**
- Create: `src/vault_search/discovery.py`
- Create: `tests/conftest.py`
- Create: `tests/test_discovery.py`

- [ ] **Step 1: Add shared fixture vault helper**

Create `tests/conftest.py`:

```python
from pathlib import Path

import pytest


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / "wiki").mkdir(parents=True)
    (root / "IT-learning" / "java-basic").mkdir(parents=True)
    (root / "tmp").mkdir(parents=True)
    (root / ".obsidian").mkdir(parents=True)

    (root / "README.md").write_text("# Fixture Vault\n", encoding="utf-8")
    (root / "wiki" / "INDEX.md").write_text("# Wiki Index\n", encoding="utf-8")
    (root / "IT-learning" / "java-basic" / "java.md").write_text("# Java\n", encoding="utf-8")
    (root / "tmp" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (root / ".obsidian" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (root / "plain.txt").write_text("not markdown\n", encoding="utf-8")
    return root
```

- [ ] **Step 2: Write failing discovery tests**

Create `tests/test_discovery.py`:

```python
from vault_search.discovery import discover_markdown_files, path_area


def test_discover_markdown_files_ignores_runtime_directories(sample_vault):
    result = discover_markdown_files(sample_vault)
    paths = [item.relative_path for item in result.files]

    assert paths == [
        "IT-learning/java-basic/java.md",
        "README.md",
        "wiki/INDEX.md",
    ]
    assert result.ignored_files == 2


def test_path_area_uses_top_level_directory_or_root():
    assert path_area("wiki/INDEX.md") == "wiki"
    assert path_area("IT-learning/java-basic/java.md") == "IT-learning"
    assert path_area("README.md") == "root"
```

- [ ] **Step 3: Run discovery tests to verify they fail**

Run:

```bash
python -m pytest tests/test_discovery.py -v
```

Expected: FAIL with an import error for `vault_search.discovery`.

- [ ] **Step 4: Implement discovery**

Create `src/vault_search/discovery.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_IGNORED_DIRS = {".obsidian", ".git", "tmp", ".trash", "node_modules", ".venv"}


@dataclass(frozen=True)
class DiscoveredFile:
    path: Path
    relative_path: str
    area: str
    mtime: float


@dataclass(frozen=True)
class DiscoveryResult:
    files: list[DiscoveredFile]
    ignored_files: int


def discover_markdown_files(root: Path, ignored_dirs: set[str] | None = None) -> DiscoveryResult:
    ignored = ignored_dirs or DEFAULT_IGNORED_DIRS
    files: list[DiscoveredFile] = []
    ignored_files = 0

    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        parts = set(relative.parts[:-1])
        if parts & ignored:
            ignored_files += 1
            continue

        relative_path = relative.as_posix()
        files.append(
            DiscoveredFile(
                path=path,
                relative_path=relative_path,
                area=path_area(relative_path),
                mtime=path.stat().st_mtime,
            )
        )

    return DiscoveryResult(files=files, ignored_files=ignored_files)


def path_area(relative_path: str) -> str:
    parts = Path(relative_path).parts
    if len(parts) <= 1:
        return "root"
    return parts[0]
```

- [ ] **Step 5: Run discovery tests**

Run:

```bash
python -m pytest tests/test_discovery.py -v
```

Expected: all discovery tests PASS.

---

## Task 5: Implement Database Rebuild, Search, and Health

**Files:**
- Create: `src/vault_search/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write database tests**

Create `tests/test_database.py`:

```python
from pathlib import Path

from vault_search.database import health_summary, rebuild_database, search_documents
from vault_search.models import Document, Heading, Link


def _docs():
    return [
        Document(
            path="wiki/ssl.md",
            title="SSL 证书",
            area="wiki",
            tags=["network", "知识总结"],
            headings=[Heading(level=1, text="SSL 证书", line=1)],
            links=[Link(target="TLS", alias=None, line=3, resolved_path="wiki/tls.md")],
            body="# SSL 证书\nSSL 证书用于 HTTPS。\n",
            mtime=1.0,
            explicit_title=True,
        ),
        Document(
            path="wiki/tls.md",
            title="TLS",
            area="wiki",
            tags=[],
            headings=[Heading(level=1, text="TLS", line=1)],
            links=[Link(target="Missing", alias=None, line=2, resolved_path=None)],
            body="# TLS\nTransport Layer Security\n",
            mtime=2.0,
            explicit_title=True,
        ),
    ]


def test_rebuild_and_search_fts(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    results = search_documents(db_path, query="SSL", limit=10)

    assert results[0]["path"] == "wiki/ssl.md"
    assert results[0]["title"] == "SSL 证书"
    assert results[0]["tags"] == ["network", "知识总结"]


def test_search_chinese_fallback(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    results = search_documents(db_path, query="证书用于", limit=10)

    assert [item["path"] for item in results] == ["wiki/ssl.md"]


def test_health_summary(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    summary = health_summary(db_path)

    assert summary["documents"] == 2
    assert summary["areas"] == {"wiki": 2}
    assert summary["tags"] == 2
    assert summary["missing_tags"] == 1
    assert summary["missing_titles"] == 0
    assert summary["wikilinks"] == 2
    assert summary["broken_wikilinks"] == 1
    assert summary["ignored_files"] == 1
```

- [ ] **Step 2: Run database tests to verify they fail**

Run:

```bash
python -m pytest tests/test_database.py -v
```

Expected: FAIL with an import error for `vault_search.database`.

- [ ] **Step 3: Implement database module**

Create `src/vault_search/database.py`:

```python
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Document


def rebuild_database(db_path: Path, documents: Iterable[Document], ignored_files: int = 0) -> dict[str, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    docs = list(documents)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _create_schema(conn)
        _clear_tables(conn)
        conn.execute("INSERT INTO index_meta(key, value) VALUES (?, ?)", ("ignored_files", str(ignored_files)))
        for doc in docs:
            _insert_document(conn, doc)
        conn.commit()
    return {"documents": len(docs), "ignored_files": ignored_files}


def search_documents(
    db_path: Path,
    query: str,
    limit: int = 10,
    area: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    tags = tags or []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        fts_results = _search_fts(conn, query, limit, area, tags)
        fallback_results = _search_like(conn, query, limit, area, tags) if _needs_fallback(query, fts_results) else []

    merged: list[dict] = []
    seen: set[str] = set()
    for item in fts_results + fallback_results:
        if item["path"] not in seen:
            seen.add(item["path"])
            merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def health_summary(db_path: Path) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        tags = conn.execute("SELECT COUNT(DISTINCT tag) FROM document_tags").fetchone()[0]
        missing_tags = conn.execute(
            "SELECT COUNT(*) FROM documents d WHERE NOT EXISTS (SELECT 1 FROM document_tags t WHERE t.path = d.path)"
        ).fetchone()[0]
        missing_titles = conn.execute("SELECT COUNT(*) FROM documents WHERE explicit_title = 0").fetchone()[0]
        wikilinks = conn.execute("SELECT COUNT(*) FROM wikilinks").fetchone()[0]
        broken_wikilinks = conn.execute("SELECT COUNT(*) FROM wikilinks WHERE resolved_path IS NULL").fetchone()[0]
        ignored_files = int(_meta_value(conn, "ignored_files", "0"))
        areas = {
            row["area"]: row["count"]
            for row in conn.execute("SELECT area, COUNT(*) AS count FROM documents GROUP BY area ORDER BY area")
        }
    return {
        "documents": documents,
        "areas": areas,
        "tags": tags,
        "missing_tags": missing_tags,
        "missing_titles": missing_titles,
        "wikilinks": wikilinks,
        "broken_wikilinks": broken_wikilinks,
        "ignored_files": ignored_files,
    }


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            path TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            area TEXT NOT NULL,
            body TEXT NOT NULL,
            mtime REAL NOT NULL,
            explicit_title INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS document_tags (
            path TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (path, tag),
            FOREIGN KEY (path) REFERENCES documents(path) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS headings (
            path TEXT NOT NULL,
            level INTEGER NOT NULL,
            text TEXT NOT NULL,
            line INTEGER NOT NULL,
            FOREIGN KEY (path) REFERENCES documents(path) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS wikilinks (
            path TEXT NOT NULL,
            target TEXT NOT NULL,
            alias TEXT,
            line INTEGER NOT NULL,
            resolved_path TEXT,
            FOREIGN KEY (path) REFERENCES documents(path) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS index_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(path UNINDEXED, title, body);
        """
    )


def _clear_tables(conn: sqlite3.Connection) -> None:
    for table in ["document_tags", "headings", "wikilinks", "documents", "index_meta", "documents_fts"]:
        conn.execute(f"DELETE FROM {table}")


def _insert_document(conn: sqlite3.Connection, doc: Document) -> None:
    conn.execute(
        "INSERT INTO documents(path, title, area, body, mtime, explicit_title) VALUES (?, ?, ?, ?, ?, ?)",
        (doc.path, doc.title, doc.area, doc.body, doc.mtime, int(doc.explicit_title)),
    )
    conn.execute(
        "INSERT INTO documents_fts(path, title, body) VALUES (?, ?, ?)",
        (doc.path, doc.title, doc.body),
    )
    conn.executemany("INSERT INTO document_tags(path, tag) VALUES (?, ?)", [(doc.path, tag) for tag in doc.tags])
    conn.executemany(
        "INSERT INTO headings(path, level, text, line) VALUES (?, ?, ?, ?)",
        [(doc.path, heading.level, heading.text, heading.line) for heading in doc.headings],
    )
    conn.executemany(
        "INSERT INTO wikilinks(path, target, alias, line, resolved_path) VALUES (?, ?, ?, ?, ?)",
        [(doc.path, link.target, link.alias, link.line, link.resolved_path) for link in doc.links],
    )


def _search_fts(conn: sqlite3.Connection, query: str, limit: int, area: str | None, tags: list[str]) -> list[dict]:
    sql = """
        SELECT d.path, d.title, d.area, d.body
        FROM documents_fts f
        JOIN documents d ON d.path = f.path
        WHERE documents_fts MATCH ?
    """
    params: list[object] = [query]
    sql, params = _append_filters(sql, params, area, tags)
    sql += " LIMIT ?"
    params.append(limit)
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []
    return [_row_to_result(conn, row) for row in rows]


def _search_like(conn: sqlite3.Connection, query: str, limit: int, area: str | None, tags: list[str]) -> list[dict]:
    sql = """
        SELECT path, title, area, body
        FROM documents d
        WHERE (title LIKE ? OR body LIKE ?)
    """
    like = f"%{query}%"
    params: list[object] = [like, like]
    sql, params = _append_filters(sql, params, area, tags)
    sql += """
        ORDER BY
            CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
            path
        LIMIT ?
    """
    params.extend([like, limit])
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_result(conn, row) for row in rows]


def _append_filters(sql: str, params: list[object], area: str | None, tags: list[str]) -> tuple[str, list[object]]:
    if area:
        sql += " AND d.area = ?"
        params.append(area)
    for tag in tags:
        sql += " AND EXISTS (SELECT 1 FROM document_tags t WHERE t.path = d.path AND t.tag = ?)"
        params.append(tag)
    return sql, params


def _row_to_result(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    tag_rows = conn.execute("SELECT tag FROM document_tags WHERE path = ? ORDER BY tag", (row["path"],)).fetchall()
    return {
        "path": row["path"],
        "title": row["title"],
        "area": row["area"],
        "tags": [tag_row["tag"] for tag_row in tag_rows],
    }


def _needs_fallback(query: str, fts_results: list[dict]) -> bool:
    return not fts_results or any("\u4e00" <= char <= "\u9fff" for char in query)


def _meta_value(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM index_meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default
```

- [ ] **Step 4: Run database tests**

Run:

```bash
python -m pytest tests/test_database.py -v
```

Expected: all database tests PASS.

---

## Task 6: Implement Indexer and Wikilink Resolution

**Files:**
- Create: `src/vault_search/indexer.py`
- Create: `tests/test_indexer.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add richer fixture content**

Modify `tests/conftest.py` file writes to include linked notes:

```python
(root / "wiki" / "INDEX.md").write_text("# Wiki Index\nSee [[TLS]].\n", encoding="utf-8")
(root / "wiki" / "TLS.md").write_text("# TLS\nTransport Layer Security\n", encoding="utf-8")
(root / "IT-learning" / "java-basic" / "java.md").write_text(
    "---\ntags: [学习, java]\n---\n# Java\n[[Missing]]\n",
    encoding="utf-8",
)
```

- [ ] **Step 2: Write failing indexer tests**

Create `tests/test_indexer.py`:

```python
from pathlib import Path

from vault_search.database import health_summary, search_documents
from vault_search.indexer import build_index


def test_build_index_discovers_parses_resolves_and_rebuilds(sample_vault):
    db_path = sample_vault / "tmp" / "vault-search.sqlite"

    summary = build_index(sample_vault, db_path)
    results = search_documents(db_path, "TLS", limit=10)
    health = health_summary(db_path)

    assert summary["documents"] == 4
    assert any(item["path"] == "wiki/TLS.md" for item in results)
    assert health["ignored_files"] == 2
    assert health["broken_wikilinks"] == 1
```

- [ ] **Step 3: Run indexer tests to verify they fail**

Run:

```bash
python -m pytest tests/test_indexer.py -v
```

Expected: FAIL with an import error for `vault_search.indexer`.

- [ ] **Step 4: Implement indexer**

Create `src/vault_search/indexer.py`:

```python
from __future__ import annotations

from pathlib import Path

from .database import rebuild_database
from .discovery import discover_markdown_files
from .models import Document, Link
from .parser import parse_markdown


def build_index(root: Path, db_path: Path | None = None) -> dict[str, int]:
    db_path = db_path or default_db_path(root)
    discovery = discover_markdown_files(root)
    documents: list[Document] = []

    for item in discovery.files:
        text = item.path.read_text(encoding="utf-8")
        documents.append(parse_markdown(text, path=item.relative_path, area=item.area, mtime=item.mtime))

    documents = _resolve_links(documents)
    summary = rebuild_database(db_path, documents, ignored_files=discovery.ignored_files)
    return summary


def default_db_path(root: Path) -> Path:
    return root / "tmp" / "vault-search.sqlite"


def _resolve_links(documents: list[Document]) -> list[Document]:
    title_index: dict[str, str] = {}
    stem_index: dict[str, str] = {}
    path_index: dict[str, str] = {}

    for doc in documents:
        title_index[doc.title] = doc.path
        path = Path(doc.path)
        stem_index[path.stem] = doc.path
        path_index[doc.path] = doc.path

    return [_with_resolved_links(doc, title_index, stem_index, path_index) for doc in documents]


def _with_resolved_links(
    doc: Document,
    title_index: dict[str, str],
    stem_index: dict[str, str],
    path_index: dict[str, str],
) -> Document:
    links = []
    for link in doc.links:
        base_target = link.target.split("#", 1)[0].strip()
        resolved = path_index.get(base_target) or title_index.get(base_target) or stem_index.get(base_target)
        links.append(Link(target=link.target, alias=link.alias, line=link.line, resolved_path=resolved))

    return Document(
        path=doc.path,
        title=doc.title,
        area=doc.area,
        tags=doc.tags,
        headings=doc.headings,
        links=links,
        body=doc.body,
        mtime=doc.mtime,
        explicit_title=doc.explicit_title,
    )
```

- [ ] **Step 5: Run indexer tests**

Run:

```bash
python -m pytest tests/test_indexer.py -v
```

Expected: all indexer tests PASS.

---

## Task 7: Implement CLI Entry Points

**Files:**
- Create: `src/vault_search/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/test_cli.py`:

```python
import json
import sys

from vault_search.cli import main_health, main_index, main_search


def test_cli_index_search_and_health_with_root(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault)])
    assert main_index() == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["summary"]["documents"] == 4

    monkeypatch.setattr(sys, "argv", ["vault-search", "TLS", "--root", str(sample_vault), "--json"])
    assert main_search() == 0
    search_payload = json.loads(capsys.readouterr().out)
    assert any(item["path"] == "wiki/TLS.md" for item in search_payload["results"])

    monkeypatch.setattr(sys, "argv", ["vault-health", "--root", str(sample_vault), "--json"])
    assert main_health() == 0
    health_payload = json.loads(capsys.readouterr().out)
    assert health_payload["summary"]["broken_wikilinks"] == 1


def test_cli_search_supports_db_override(sample_vault, capsys, monkeypatch):
    db_path = sample_vault / "tmp" / "custom.sqlite"
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault), "--db", str(db_path)])
    assert main_index() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vault-search", "证书", "--db", str(db_path), "--json"])
    assert main_search() == 0
    payload = json.loads(capsys.readouterr().out)

    assert "results" in payload
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
python -m pytest tests/test_cli.py -v
```

Expected: FAIL with an import error for `vault_search.cli`.

- [ ] **Step 3: Implement CLI**

Create `src/vault_search/cli.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .database import health_summary, search_documents
from .indexer import build_index, default_db_path


def main_index() -> int:
    parser = argparse.ArgumentParser(prog="vault-index")
    parser.add_argument("--root", required=True)
    parser.add_argument("--db")
    args = parser.parse_args(sys.argv[1:])

    root = Path(args.root)
    db_path = Path(args.db) if args.db else default_db_path(root)
    summary = build_index(root, db_path)
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0


def main_search() -> int:
    parser = argparse.ArgumentParser(prog="vault-search")
    parser.add_argument("query")
    parser.add_argument("--root")
    parser.add_argument("--db")
    parser.add_argument("--area")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    db_path = _resolve_db(args.root, args.db, parser)
    results = search_documents(db_path, query=args.query, limit=args.limit, area=args.area, tags=args.tag)
    payload = {"query": args.query, "results": results}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in results:
            tags = ", ".join(item["tags"])
            print(f"{item['path']} | {item['title']} | {tags}")
    return 0


def main_health() -> int:
    parser = argparse.ArgumentParser(prog="vault-health")
    parser.add_argument("--root")
    parser.add_argument("--db")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    db_path = _resolve_db(args.root, args.db, parser)
    payload = {"summary": health_summary(db_path)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload["summary"].items():
            print(f"{key}: {value}")
    return 0


def _resolve_db(root: str | None, db: str | None, parser: argparse.ArgumentParser) -> Path:
    if db:
        return Path(db)
    if root:
        return default_db_path(Path(root))
    parser.error("one of --root or --db is required")
    raise AssertionError("unreachable")
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python -m pytest tests/test_cli.py -v
```

Expected: all CLI tests PASS.

---

## Task 8: Complete README and Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README with V1 usage docs**

Replace `README.md`:

````markdown
# Vault Search

Local-first command line search for Obsidian vaults.

Vault Search indexes Markdown files from an Obsidian vault into SQLite + FTS5 and provides CLI commands for search and lightweight vault health checks.

## Install

```bash
python -m pip install -e .
```

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

## Limitations

V1 does not include semantic search, incremental indexing, a web UI, an Obsidian plugin, or advanced knowledge graph analysis.
````

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Verify installed CLI help**

Run:

```bash
vault-index --help
vault-search --help
vault-health --help
```

Expected: each command prints help text and exits successfully.

- [ ] **Step 4: Verify package import**

Run:

```bash
python -c "import vault_search; print(vault_search.__version__)"
```

Expected:

```text
0.1.0
```

---

## Self-Review Checklist

- [ ] The plan implements every V1 goal in the blueprint.
- [ ] The plan does not implement deferred features such as embeddings, Web UI, plugins, file watching, or incremental indexing.
- [ ] The project root is the current repository root.
- [ ] The CLI supports `--root` as the normal path and `--db` as an override.
- [ ] Search includes FTS5 and Chinese-friendly fallback.
- [ ] Health includes lightweight metrics and broken wikilinks.
- [ ] Every code-bearing task has a failing test before implementation.
- [ ] No task requires a real Obsidian vault.
