"""代码块处理策略"""

from .base import SnippetStrategy

class CodeBlockStrategy(SnippetStrategy):
    """代码块处理策略
    
    处理代码块内的内容，支持：
    - 代码上下文绑定（保持代码完整性）
    - 嵌套围栏处理（支持四重/五重反引号）
    - 代码+输出配对识别
    """
    
    def detect(self, line: str, in_code_block: bool) -> bool:
        return in_code_block
    
    def process(self, line: str) -> str:
        """处理代码行，添加缩进保持格式"""
        return f"    {line}"
