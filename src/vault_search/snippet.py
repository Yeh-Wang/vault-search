from __future__ import annotations

from .snippet_strategies import get_strategies


class SnippetGenerator:
    """智能摘要生成器

    负责：
    - 根据文档长度动态确定匹配数量
    - 使用评分机制选择最优匹配行
    - 应用策略模式处理不同内容类型
    """

    def __init__(self):
        self.strategies = get_strategies()

    def generate(self, title: str, body: str, query: str) -> str:
        """生成智能摘要

        Args:
            title: 文档标题
            body: 文档正文
            query: 查询词

        Returns:
            格式化后的摘要文本
        """
        # 重置所有策略的状态，避免前一个文档的状态残留
        self._reset_strategies()

        if not query:
            return title

        query_lower = query.lower()
        max_line_length = 120

        # 根据文档长度动态确定最大匹配数
        max_matches = self._calculate_max_matches(body)

        # 收集所有匹配行并评分
        candidates = self._collect_matches(body, query_lower, max_line_length)

        # 按分数排序，取前 N 个
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[:max_matches]

        # 应用策略处理并构建结果
        matches = []

        for candidate in top_candidates:
            line = candidate["line"]
            stripped = line.strip()

            # 使用 _collect_matches 中按文档顺序记录的正确状态
            in_code_block = candidate["in_code_block"]

            # 带标题上下文：如果有所属标题且匹配行本身不是标题，则附带标题
            heading = candidate.get("heading", "")
            if heading and not stripped.startswith("#"):
                # 标题作为上下文前缀，缩进表示层级
                matches.append(f"  {heading}")
                # 使用策略模式处理
                processed = self._apply_strategy(stripped, in_code_block)
                matches.append(f"  {processed}")
            else:
                # 使用策略模式处理
                processed = self._apply_strategy(stripped, in_code_block)
                matches.append(processed)

        if matches:
            return "\n".join(matches)
        return title

    def _calculate_max_matches(self, body: str) -> int:
        """根据文档行数动态确定最大匹配数"""
        line_count = len(body.splitlines())

        if line_count < 10:
            return 2
        elif line_count < 50:
            return 3
        elif line_count < 100:
            return 4
        else:
            return 5

    def _calculate_score(
        self,
        line: str,
        query_lower: str,
        in_code_block: bool = False,
        is_heading: bool = False,
    ) -> int:
        """计算匹配行的分数

        评分规则：
        - Markdown 标题匹配（## xxx）：+50
        - 正文匹配：基础分
        - 代码注释匹配（// 或 # 开头）：-20 降权
        - 查询词位置：越靠前分数越高（+0~20）
        - 查询词频率：+15/次
        - 行长度适中（80字符以内）：+10
        """
        score = 0

        # Markdown 标题匹配（最强信号）
        if is_heading:
            score += 50

        # 代码注释降权
        if in_code_block:
            stripped = line.lstrip()
            if stripped.startswith("//") or stripped.startswith("#"):
                score -= 20

        # 查询词位置：越靠前分数越高
        pos = line.lower().find(query_lower)
        if pos != -1:
            max_pos_score = 20
            score += max(0, max_pos_score - pos // 4)

        # 查询词频率
        freq = line.lower().count(query_lower)
        score += freq * 15

        # 行长度适中加分
        if len(line) <= 80:
            score += 10

        return score

    def _collect_matches(self, body: str, query_lower: str, max_line_length: int) -> list[dict]:
        """收集所有包含查询词的行，并计算分数"""
        candidates = []
        in_code_block = False
        current_heading = ""

        for line in body.splitlines():
            stripped = line.strip()

            # 检测代码块边界
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            # 追踪当前标题（非代码块内的 # 开头行）
            if not in_code_block and stripped.startswith("#"):
                current_heading = stripped
                # 标题本身也可能包含查询词，作为候选
                if query_lower in stripped.lower():
                    is_heading = True
                    score = self._calculate_score(stripped, query_lower, in_code_block, is_heading)
                    candidates.append({
                        "line": stripped,
                        "score": score,
                        "in_code_block": in_code_block,
                        "heading": "",
                    })
                continue

            # 跳过空行
            if not stripped:
                continue

            # 检查是否包含查询词
            if query_lower not in stripped.lower():
                continue

            # 超长行截断处理
            processed_line = self._truncate_line(stripped, query_lower, max_line_length)

            # 计算分数
            is_heading = False
            score = self._calculate_score(stripped, query_lower, in_code_block, is_heading)

            candidates.append({
                "line": processed_line,
                "score": score,
                "in_code_block": in_code_block,
                "heading": current_heading,
            })

        return candidates

    def _truncate_line(self, line: str, query: str, max_length: int) -> str:
        """超长行截断辅助函数，以查询词为中心截取"""
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

    def _apply_strategy(self, line: str, in_code_block: bool) -> str:
        """应用策略模式处理不同内容类型"""
        for strategy in self.strategies:
            if strategy.detect(line, in_code_block):
                return strategy.process(line)
        return line

    def _reset_strategies(self):
        """重置所有策略的状态"""
        for strategy in self.strategies:
            strategy.reset()