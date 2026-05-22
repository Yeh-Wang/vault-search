"""普通文本处理策略"""

from .base import SnippetStrategy

class PlainTextStrategy(SnippetStrategy):
    """普通文本处理策略（兜底策略）
    
    当其他策略都不匹配时使用此策略。
    应该放在策略列表的最后。
    """
    
    def detect(self, line: str, in_code_block: bool) -> bool:
        return True  # 始终匹配
    
    def process(self, line: str) -> str:
        return line
