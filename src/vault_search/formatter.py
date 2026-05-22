from __future__ import annotations

import json
from typing import Any

from .models import SearchResult


class OutputFormatter:
    """CLI 输出格式化器
    
    负责：
    - 多行 snippet 缩进对齐
    - 超长路径和标签截断
    - 支持多种输出格式（文本、JSON、紧凑）
    """
    
    def format_text(self, results: list[SearchResult | dict]) -> str:
        """格式化文本输出（人类可读格式）"""
        if not results:
            return "No results."
        
        lines = []
        for i, item in enumerate(results, 1):
            lines.append(f"--- Result {i} ---")
            
            # 转换为 dict 如果是 SearchResult 对象
            result = item.to_dict() if isinstance(item, SearchResult) else item
            
            lines.append(f"  Title:  {result['title']}")
            
            # 处理路径（超长截断）
            path = result["path"]
            if len(path) > 60:
                path = "..." + path[-57:]
            lines.append(f"  Path:   {path}")
            
            # 处理标签（超长截断）
            if result.get("tags"):
                tags_str = ", ".join(result["tags"])
                if len(tags_str) > 60:
                    tags_str = tags_str[:57] + "..."
                lines.append(f"  Tags:   {tags_str}")
            
            # 处理 snippet（多行缩进对齐）
            snippet = result.get("snippet", "")
            if snippet:
                snippet_lines = snippet.splitlines()
                lines.append(f"  Match:  {snippet_lines[0]}")
                for line in snippet_lines[1:]:
                    lines.append(f"          {line}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def format_json(self, results: list[SearchResult | dict], query: str | None = None) -> str:
        """格式化 JSON 输出"""
        # 转换为 dict 列表
        dict_results = [
            item.to_dict() if isinstance(item, SearchResult) else item
            for item in results
        ]
        
        payload: dict[str, Any] = {"results": dict_results}
        if query:
            payload["query"] = query
        
        return json.dumps(payload, ensure_ascii=False, indent=2)
    
    def format_compact(self, results: list[SearchResult | dict]) -> str:
        """格式化紧凑输出（一行一个结果）"""
        if not results:
            return "No results."
        
        lines = []
        for item in results:
            result = item.to_dict() if isinstance(item, SearchResult) else item
            tags = ",".join(result.get("tags", []))[:30]
            lines.append(f"{result['title']} | {result['path']} | {tags}")
        
        return "\n".join(lines)