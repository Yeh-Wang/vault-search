"""表格处理策略"""

from .base import SnippetStrategy

class TableStrategy(SnippetStrategy):
    """表格处理策略

    处理 Markdown 表格，保持原始格式。
    """

    def detect(self, line: str, in_code_block: bool) -> bool:
        """检测表格行

        表格行特征：
        - 标准表格：以 | 开头
        - 分隔线行：包含 | 和 :-
        """
        has_pipe = "|" in line
        is_separator = has_pipe and ":" in line and any(c in line for c in "-_")
        return has_pipe and (line.startswith("|") or is_separator)

    def process(self, line: str) -> str:
        """处理表格行，保持原始格式"""
        return line

    def reset(self):
        """重置状态（保持接口一致性）"""
        pass
