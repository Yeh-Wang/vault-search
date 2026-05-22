"""列表处理策略"""

from .base import SnippetStrategy


class ListStrategy(SnippetStrategy):
    """列表处理策略

    处理 Markdown 列表，支持：
    - 嵌套列表层级保留（不拆分父子关系）
    - 多种列表类型：无序列表、有序列表、复选框列表
    """

    # 支持的列表标记（按优先级排序）
    LIST_MARKERS = (
        # 一级列表
        "* ", "- ", "+ ",           # 无序列表
        "1. ", "2. ", "3. ",        # 有序列表
        "• ",                       # 圆点列表
        "- [ ] ", "- [x] ",         # 复选框列表（未勾选/已勾选）
        
        # 二级列表（2空格缩进）
        "  * ", "  - ", "  + ",     # 二级无序列表
        "  1. ", "  2. ",           # 二级有序列表
        "  • ",                     # 二级圆点列表
        "  - [ ] ", "  - [x] ",     # 二级复选框列表
        
        # 三级列表（4空格缩进）
        "    * ", "    - ", "    + ",
        "    1. ", "    2. ",
        "    • ",
        "    - [ ] ", "    - [x] ",
    )

    def detect(self, line: str, in_code_block: bool) -> bool:
        """检测列表项

        支持：
        - 无序列表：*, -, +, •
        - 有序列表：数字 + .
        - 复选框列表：- [ ] 或 - [x]
        - 多级嵌套列表
        """
        # 检查是否匹配列表标记
        for marker in self.LIST_MARKERS:
            if line.startswith(marker):
                return True

        return False

    def process(self, line: str) -> str:
        """处理列表行，保持层级结构"""
        # 保留原始缩进和标记，保持列表结构
        return line

    def reset(self):
        """重置状态（保持接口一致性）"""
        pass