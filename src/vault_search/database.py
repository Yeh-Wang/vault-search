from __future__ import annotations

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
    return [_row_to_result(conn, row, query) for row in rows]


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
    return [_row_to_result(conn, row, query) for row in rows]


def _append_filters(sql: str, params: list[object], area: str | None, tags: list[str]) -> tuple[str, list[object]]:
    if area:
        sql += " AND d.area = ?"
        params.append(area)
    for tag in tags:
        sql += " AND EXISTS (SELECT 1 FROM document_tags t WHERE t.path = d.path AND t.tag = ?)"
        params.append(tag)
    return sql, params


def _row_to_result(conn: sqlite3.Connection, row: sqlite3.Row, query: str) -> dict:
    tag_rows = conn.execute("SELECT tag FROM document_tags WHERE path = ? ORDER BY tag", (row["path"],)).fetchall()
    return {
        "path": row["path"],
        "title": row["title"],
        "area": row["area"],
        "tags": [tag_row["tag"] for tag_row in tag_rows],
        "snippet": _make_snippet(row["title"], row["body"], query),
    }


def _needs_fallback(query: str, fts_results: list[dict]) -> bool:
    return not fts_results or any("\u4e00" <= char <= "\u9fff" for char in query)


def _make_snippet(title: str, body: str, query: str) -> str:
    query_lower = query.lower()
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and query_lower in stripped.lower():
            return stripped
    return title


def _meta_value(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM index_meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default
