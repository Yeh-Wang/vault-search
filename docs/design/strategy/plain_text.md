# PlainTextStrategy 设计文档

## 概述

普通文本处理策略，作为兜底策略处理所有未被其他策略匹配的内容。

## 核心逻辑

### 检测逻辑

```mermaid
flowchart LR
    A[输入: line, in_code_block] --> B[始终返回 True]
```

**设计特点**：
- 始终返回 True
- 必须放在策略列表的最后
- 确保所有内容都能被处理

### 处理逻辑

```mermaid
flowchart LR
    A[输入: line] --> B[直接返回原始内容]
```

**效果示例**：

| 输入 | 输出 |
|------|------|
| `这是一段普通文本` | `这是一段普通文本` |
| `## 标题` | `## 标题` |

## 兜底机制

```mermaid
flowchart TD
    A[遍历策略列表] --> B{TableStrategy?}
    B -->|匹配| C[使用表格策略]
    B -->|不匹配| D{ListStrategy?}
    D -->|匹配| E[使用列表策略]
    D -->|不匹配| F{CodeBlockStrategy?}
    F -->|匹配| G[使用代码块策略]
    F -->|不匹配| H[使用普通文本策略]
```

## 设计原因

| 设计原则 | 说明 |
|----------|------|
| 完整性 | 确保所有内容都能被处理 |
| 简单性 | 不做任何修改，保持原样 |
| 安全性 | 作为最后一道防线 |

## 在策略链中的位置

```mermaid
sequenceDiagram
    participant Main as _make_snippet
    participant T as TableStrategy
    participant L as ListStrategy
    participant C as CodeBlockStrategy
    participant P as PlainTextStrategy
    
    Main->>T: detect(line)
    T-->>Main: False
    Main->>L: detect(line)
    L-->>Main: False
    Main->>C: detect(line)
    C-->>Main: False
    Main->>P: detect(line)
    P-->>Main: True
    Main->>P: process(line)
    P-->>Main: line
```
