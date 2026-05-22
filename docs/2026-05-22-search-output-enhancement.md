# 搜索输出优化方案

## 概述

本次修改旨在提升搜索结果的可读性，主要针对以下问题：
- 表格格式输出混乱
- 长代码行导致输出溢出
- 多行匹配内容缩进不对齐

同时引入**策略模式**，提高代码的可扩展性和可维护性。

---

## 改进内容

### 1. 策略模式重构

**架构设计**：

```
src/vault_search/
├── database.py                    # 主入口，使用策略模式
└── snippet_strategies/            # 策略类目录
    ├── __init__.py                # 策略导出
    ├── base.py                    # 基础策略接口
    ├── table.py                   # 表格处理策略
    ├── list.py                    # 列表处理策略
    ├── code_block.py              # 代码块处理策略
    └── plain_text.py              # 普通文本处理策略（兜底）
```

**策略接口**（`base.py`）：

```python
class SnippetStrategy(ABC):
    @abstractmethod
    def detect(self, line: str, in_code_block: bool) -> bool:
        pass
    
    @abstractmethod
    def process(self, line: str) -> str:
        pass
```

**策略实现**：

| 策略类 | 检测条件 | 处理方式 |
|--------|----------|----------|
| `TableStrategy` | 以 `|` 开头 | 直接保留 |
| `ListStrategy` | 以列表标记开头 | 直接保留 |
| `CodeBlockStrategy` | `in_code_block=True` | 添加4空格缩进 |
| `PlainTextStrategy` | 始终匹配（兜底） | 直接保留 |

### 2. 智能摘要生成器（`_make_snippet`）

**位置**：`src/vault_search/database.py`

**核心逻辑**：
- 逐行遍历文档内容
- 使用策略模式匹配内容类型
- 超长行以查询词为中心截取（最大120字符）
- 最多返回3个匹配行

```python
def _make_snippet(title: str, body: str, query: str) -> str:
    strategies = get_strategies()
    
    for line in body.splitlines():
        # 超长行处理
        processed_line = _truncate_line(stripped, query_lower, max_line_length)
        
        # 使用策略模式处理
        for strategy in strategies:
            if strategy.detect(stripped, in_code_block):
                matches.append(strategy.process(processed_line))
                break
```

### 3. 统一输出格式化器（`_format_search_results`）

**位置**：`src/vault_search/cli.py`

**功能**：
- 多行 snippet 缩进对齐
- 超长路径截断（60字符）
- 标签列表截断（60字符）

---

## 效果对比

### 修改前

```
--- Result 1 ---
  Title:  快捷键笔记
  Path:   shortcuts.md
  Tags:   shortcut
  Match:  | 快捷键 | 功能 |
|--------|------|
| Ctrl+C | 复制 |
```

### 修改后

```
--- Result 1 ---
  Title:  快捷键笔记
  Path:   shortcuts.md
  Tags:   shortcut
  Match:  | 快捷键 | 功能 |
          |--------|------|
          | Ctrl+C | 复制 |
```

---

## 处理策略汇总

| 场景 | 处理策略 | 阈值 |
|------|----------|------|
| 单行过长 | 以查询词为中心截取 | 120字符 |
| 文件路径过长 | 保留末尾部分 | 60字符 |
| 标签过多 | 截断并添加省略号 | 60字符 |
| 多行匹配 | 最多返回3行 | 3行 |

---

## 后续扩展可能性

### 新增策略类型

只需创建新的策略类并注册到 `get_strategies()` 即可：

```python
# 示例：引用块策略
class QuoteStrategy(SnippetStrategy):
    def detect(self, line: str, in_code_block: bool) -> bool:
        return line.startswith("> ")
    
    def process(self, line: str) -> str:
        return line  # 保留引用格式
```

### 可能的扩展方向

| 策略类型 | 检测条件 | 用途 |
|----------|----------|------|
| `QuoteStrategy` | 以 `> ` 开头 | Markdown 引用块 |
| `HeadingStrategy` | 以 `#` 开头 | 标题格式 |
| `MathStrategy` | 包含 `$` | 数学公式 |
| `LinkStrategy` | 包含 `[` 或 `[[` | 链接处理 |

---

## 测试验证

所有 **38 个测试用例均已通过**。

---

## 影响范围

- 仅修改输出格式，不影响搜索逻辑
- 向后兼容，JSON 输出格式不变
- 策略模式提高了代码的可扩展性
