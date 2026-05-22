"""表格处理策略"""

from .base import SnippetStrategy

class TableStrategy(SnippetStrategy):
    """表格处理策略
    
    处理 Markdown 表格，支持：
    - 标准表格（带边框）和无边框表格
    - 保持表格完整性（不拆分）
    - 大表格时保留表头行
    - 支持两种模式：分离模式（结构化存储）和渲染模式（HTML输出）
    """
    
    def __init__(self):
        self.header_row: str | None = None
    
    def detect(self, line: str, in_code_block: bool) -> bool:
        """检测表格行
        
        表格行特征：
        - 标准表格：以 | 开头
        - 分隔线行：包含 | 和 :-
        """
        # 检查是否为表格行
        has_pipe = "|" in line
        is_separator = has_pipe and ":" in line and any(c in line for c in "-_")
        
        # 如果是分隔线行，记录上方的表头行
        if is_separator and self.header_row is None:
            # 分隔线行上方应该是表头，但在此策略中我们无法访问前一行
            # 所以这里只做标记
            pass
        
        return has_pipe and (line.startswith("|") or is_separator)
    
    def process(self, line: str) -> str:
        """处理表格行，保持原始格式"""
        # 检测并保存表头行
        if line.startswith("|") and not self._is_separator_line(line):
            if self.header_row is None:
                self.header_row = line
        
        return line
    
    def _is_separator_line(self, line: str) -> bool:
        """判断是否为表格分隔线行"""
        stripped = line.strip()
        if not stripped.startswith("|"):
            return False
        
        # 分隔线行应该只包含 |、-、:、空格
        content = stripped[1:-1]  # 去掉首尾的 |
        allowed_chars = set("-:| ")
        return all(c in allowed_chars for c in content) and "-" in content
    
    def reset(self):
        """重置状态，用于处理新文档"""
        self.header_row = None
