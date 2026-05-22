from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Document


class Database:
    """数据库操作类
    
    封装所有数据库操作，提供面向对象接口。
    同时保持与原有函数式 API 的向后兼容。
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def connect(self) -> sqlite3.Connection:
        """建立数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def create_schema(self) -> None:
        """创建数据库表结构"""
        with self.connect() as conn:
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
    
    def rebuild(self, documents: Iterable[Document], ignored_files: int = 0) -> dict[str, int]:
        """重建数据库索引"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        docs = list(documents)
        
        with self.connect() as conn:
            self.create_schema()
            self._clear_tables(conn)
            conn.execute("INSERT INTO index_meta(key, value) VALUES (?, ?)", ("ignored_files", str(ignored_files)))
            for doc in docs:
                self._insert_document(conn, doc)
            conn.commit()
        
        return {"documents": len(docs), "ignored_files": ignored_files}
    
    def search_fts(
        self,
        query: str,
        limit: int = 10,
        area: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """使用 FTS5 进行全文搜索"""
        tags = tags or []
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT d.path, d.title, d.area, d.body
                FROM documents_fts f
                JOIN documents d ON d.path = f.path
                WHERE documents_fts MATCH ?
            """
            params: list[object] = [query]
            sql, params = self._append_filters(sql, params, area, tags)
            sql += " LIMIT ?"
            params.append(limit)
            
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                return []
            
            return [{"path": row["path"], "title": row["title"], "area": row["area"], "body": row["body"]} for row in rows]
    
    def search_like(
        self,
        query: str,
        limit: int = 10,
        area: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """使用 LIKE 进行模糊搜索（fallback）"""
        tags = tags or []
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            sql = """
                SELECT path, title, area, body
                FROM documents d
                WHERE (title LIKE ? OR body LIKE ?)
            """
            like = f"%{query}%"
            params: list[object] = [like, like]
            sql, params = self._append_filters(sql, params, area, tags)
            sql += """
                ORDER BY
                    CASE WHEN title LIKE ? THEN 0 ELSE 1 END,
                    path
                LIMIT ?
            """
            params.extend([like, limit])
            
            rows = conn.execute(sql, params).fetchall()
            return [{"path": row["path"], "title": row["title"], "area": row["area"], "body": row["body"]} for row in rows]
    
    def get_document(self, path: str) -> dict | None:
        """获取单个文档信息"""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM documents WHERE path = ?", (path,)).fetchone()
            if row:
                return dict(row)
            return None
    
    def get_tags(self, path: str) -> list[str]:
        """获取文档的标签列表"""
        with self.connect() as conn:
            rows = conn.execute("SELECT tag FROM document_tags WHERE path = ? ORDER BY tag", (path,)).fetchall()
            return [row[0] for row in rows]
    
    def health(self) -> dict:
        """获取数据库健康状态摘要"""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            tags = conn.execute("SELECT COUNT(DISTINCT tag) FROM document_tags").fetchone()[0]
            missing_tags = conn.execute(
                "SELECT COUNT(*) FROM documents d WHERE NOT EXISTS (SELECT 1 FROM document_tags t WHERE t.path = d.path)"
            ).fetchone()[0]
            missing_titles = conn.execute("SELECT COUNT(*) FROM documents WHERE explicit_title = 0").fetchone()[0]
            wikilinks = conn.execute("SELECT COUNT(*) FROM wikilinks").fetchone()[0]
            broken_wikilinks = conn.execute("SELECT COUNT(*) FROM wikilinks WHERE resolved_path IS NULL").fetchone()[0]
            ignored_files = int(self._meta_value(conn, "ignored_files", "0"))
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
    
    def _clear_tables(self, conn: sqlite3.Connection) -> None:
        """清空所有表"""
        for table in ["document_tags", "headings", "wikilinks", "documents", "index_meta", "documents_fts"]:
            conn.execute(f"DELETE FROM {table}")
    
    def _insert_document(self, conn: sqlite3.Connection, doc: Document) -> None:
        """插入单个文档"""
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
    
    def _append_filters(
        self, sql: str, params: list[object], area: str | None, tags: list[str]
    ) -> tuple[str, list[object]]:
        """添加过滤条件"""
        if area:
            sql += " AND d.area = ?"
            params.append(area)
        for tag in tags:
            sql += " AND EXISTS (SELECT 1 FROM document_tags t WHERE t.path = d.path AND t.tag = ?)"
            params.append(tag)
        return sql, params
    
    def _meta_value(self, conn: sqlite3.Connection, key: str, default: str) -> str:
        """获取元数据值"""
        row = conn.execute("SELECT value FROM index_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


# ==================== 向后兼容的函数式 API ====================

def rebuild_database(db_path: Path, documents: Iterable[Document], ignored_files: int = 0) -> dict[str, int]:
    """向后兼容：重建数据库"""
    return Database(db_path).rebuild(documents, ignored_files)


def search_documents(
    db_path: Path,
    query: str,
    limit: int = 10,
    area: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    """向后兼容：搜索文档（使用旧的字典格式返回）"""
    db = Database(db_path)
    fts_results = db.search_fts(query, limit, area, tags)
    needs_fallback = not fts_results or any("\u4e00" <= char <= "\u9fff" for char in query)
    like_results = db.search_like(query, limit, area, tags) if needs_fallback else []
    
    merged: list[dict] = []
    seen: set[str] = set()
    for item in fts_results + like_results:
        if item["path"] not in seen:
            seen.add(item["path"])
            tags_list = db.get_tags(item["path"])
            snippet = _make_snippet(item["title"], item["body"], query)
            merged.append({
                "path": item["path"],
                "title": item["title"],
                "area": item["area"],
                "tags": tags_list,
                "snippet": snippet,
            })
        if len(merged) >= limit:
            break
    return merged


def health_summary(db_path: Path) -> dict:
    """向后兼容：获取健康摘要"""
    return Database(db_path).health()


def _truncate_line(line: str, query: str, max_length: int) -> str:
    """超长行截断辅助函数"""
    if len(line) <= max_length:
        return line
    
    query_pos = line.lower().find(query)
    if query_pos != -1:
        half_len = max_length // 2
        start = max(0, query_pos - half_len)
        end = min(len(line), query_pos + len(query) + half_len)
        
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(line) else ""
        return f"{prefix}{line[start:end]}{suffix}"
    
    return line[:max_length - 3] + "..."


def _make_snippet(title: str, body: str, query: str) -> str:
    """智能摘要生成器（旧版，保持向后兼容）"""
    from .snippet_strategies import get_strategies
    
    query_lower = query.lower()
    max_matches = 3
    max_line_length = 120
    matches: list[str] = []
    in_code_block = False
    
    strategies = get_strategies()
    
    for line in body.splitlines():
        stripped = line.strip()
        
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if query_lower in stripped.lower():
                matches.append(stripped[:max_line_length])
        
        if not stripped:
            continue
        
        if query_lower not in stripped.lower():
            continue
        
        processed_line = _truncate_line(stripped, query_lower, max_line_length)
        
        for strategy in strategies:
            if strategy.detect(stripped, in_code_block):
                matches.append(strategy.process(processed_line))
                break
        
        if len(matches) >= max_matches:
            break
    
    if matches:
        return "\n".join(matches)
    return title