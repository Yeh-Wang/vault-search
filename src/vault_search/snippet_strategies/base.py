"""摘要处理策略接口"""

from abc import ABC, abstractmethod

class SnippetStrategy(ABC):
    """摘要处理策略接口"""
    
    @abstractmethod
    def detect(self, line: str, in_code_block: bool) -> bool:
        """检测是否匹配该策略
        
        Args:
            line: 待检测的行内容（已strip）
            in_code_block: 是否处于代码块内
        
        Returns:
            True 表示匹配该策略，False 表示不匹配
        """
        pass
    
    @abstractmethod
    def process(self, line: str) -> str:
        """处理该行内容
        
        Args:
            line: 待处理的行内容
        
        Returns:
            处理后的行内容
        """
        pass
