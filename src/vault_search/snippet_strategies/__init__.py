from __future__ import annotations

"""摘要处理策略模块"""

from .base import SnippetStrategy
from .table import TableStrategy
from .list import ListStrategy
from .code_block import CodeBlockStrategy
from .plain_text import PlainTextStrategy

def get_strategies() -> list[SnippetStrategy]:
    """获取所有策略，按优先级排序"""
    return [
        TableStrategy(),
        ListStrategy(),
        CodeBlockStrategy(),
        PlainTextStrategy(),  # 兜底策略，放在最后
    ]
