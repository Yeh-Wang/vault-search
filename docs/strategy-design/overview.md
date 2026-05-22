# 策略模式设计文档

## 概述

本文档详细描述了 vault-search 项目中使用的策略模式设计，用于处理不同类型的 Markdown 内容。

## 架构设计

### 策略模式结构图

```mermaid
classDiagram
    class SnippetStrategy {
        <<interface>>
        +detect(line, in_code_block) bool
        +process(line) str
    }

    class TableStrategy {
        -header_row: str
        +detect(line, in_code_block) bool
        +process(line) str
        +_is_separator_line(line) bool
        +reset()
    }

    class ListStrategy {
        -current_level: int
        -prev_line_level: int
        +detect(line, in_code_block) bool
        +process(line) str
        +_update_level(marker)
        +is_child_item() bool
        +reset()
    }

    class CodeBlockStrategy {
        +detect(line, in_code_block) bool
        +process(line) str
    }

    class PlainTextStrategy {
        +detect(line, in_code_block) bool
        +process(line) str
    }

    class _make_snippet {
        +main()
    }

    SnippetStrategy <|.. TableStrategy
    SnippetStrategy <|.. ListStrategy
    SnippetStrategy <|.. CodeBlockStrategy
    SnippetStrategy <|.. PlainTextStrategy

    _make_snippet --> SnippetStrategy : uses
```

### 策略执行流程图

```mermaid
flowchart TD
    A[开始] --> B[逐行遍历文档]
    B --> C{检测代码块边界}
    C -->|是| D[in_code_block 取反]
    D --> E{检查空行}
    C -->|否| E
    E -->|是| B
    E -->|否| F{包含查询词}
    F -->|否| B
    F -->|是| G[超长行截断处理]
    G --> H[遍历策略列表]
    H --> I{策略匹配成功}
    I -->|是| J[应用策略处理]
    J --> K[添加到匹配结果]
    K --> L{达到最大匹配数}
    L -->|是| M[返回结果]
    L -->|否| B
    I -->|否| H
    H -->|遍历完成| B
```

## 策略优先级

| 优先级 | 策略              | 检测条件               |
| ------ | ----------------- | ---------------------- |
| 1      | TableStrategy     | 以 \| 开头或包含分隔线 |
| 2      | ListStrategy      | 以列表标记开头         |
| 3      | CodeBlockStrategy | in_code_block=True     |
| 4      | PlainTextStrategy | 始终匹配（兜底）       |

## 目录结构

```plaintext
src/vault_search/snippet_strategies/
├── __init__.py       # 策略注册和导出
├── base.py           # 策略接口定义
├── code_block.py     # 代码块策略
├── table.py          # 表格策略
├── list.py           # 列表策略
└── plain_text.py     # 普通文本策略
```
