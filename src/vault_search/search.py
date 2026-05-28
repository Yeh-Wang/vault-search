from __future__ import annotations

from pathlib import Path

from .database import Database
from .models import SearchResult
from .snippet import SnippetGenerator


class SearchEngine:
    """搜索引擎核心类

    负责：
    - 协调数据库查询
    - 合并 FTS 和 LIKE 搜索结果
    - 生成智能摘要
    - 构建 SearchResult 对象
    """

    def __init__(self, db_path: Path):
        self.db = Database(db_path)
        self.snippet_generator = SnippetGenerator()

    def search(
        self,
        query: str,
        limit: int = 10,
        area: str | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchResult]:
        """执行搜索并返回结果列表"""
        tags = tags or []

        with self.db.connect() as conn:
            # 执行 FTS 搜索
            fts_results = self.db.search_fts(query, limit, area, tags, conn=conn)

            # 判断是否需要 fallback（CJK 查询或无结果）
            if self._needs_fallback(query, fts_results):
                like_results = self.db.search_like(query, limit, area, tags, conn=conn)
            else:
                like_results = []

            # 合并结果并去重
            merged = self._merge_results(fts_results, like_results, limit)

            # 构建 SearchResult 对象
            return [self._build_result(item, query, conn) for item in merged]

    def _needs_fallback(self, query: str, fts_results: list[dict]) -> bool:
        """判断是否需要 fallback 到 LIKE 查询"""
        return not fts_results or any("\u4e00" <= char <= "\u9fff" for char in query)

    def _merge_results(
        self,
        fts_results: list[dict],
        like_results: list[dict],
        limit: int,
    ) -> list[dict]:
        """合并两个结果列表，去重并保持顺序（FTS 在前，LIKE 补充）"""
        merged: list[dict] = []
        seen: set[str] = set()

        for item in fts_results + like_results:
            if item["path"] not in seen:
                seen.add(item["path"])
                merged.append(item)
            if len(merged) >= limit:
                break

        return merged

    def _build_result(self, item: dict, query: str, conn) -> SearchResult:
        """从数据库结果构建 SearchResult 对象"""
        # 获取标签（使用共享连接）
        tags = self.db.get_tags_with_conn(conn, item["path"])

        # 生成摘要
        snippet = self.snippet_generator.generate(
            item["title"], item["body"], query
        )

        return SearchResult(
            path=item["path"],
            title=item["title"],
            area=item["area"],
            tags=tags,
            snippet=snippet,
            score=item.get("score", 0.0),
        )