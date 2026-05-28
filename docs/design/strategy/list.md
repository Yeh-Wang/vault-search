# ListStrategy 设计文档

## 概述

列表处理策略，用于处理 Markdown 列表内容。

## 核心逻辑

### 检测逻辑

```mermaid
flowchart TD
    A[输入: line] --> B{匹配列表标记?}
    B -->|否| C[返回 False]
    B -->|是| D[更新层级信息]
    D --> E[返回 True]
```

**支持的列表类型**：

| 类型 | 标记 | 示例 |
|------|------|------|
| 无序列表 | *, -, + | `- 项目` |
| 有序列表 | 数字. | `1. 第一项` |
| 圆点列表 | • | `• 项目` |
| 复选框 | - [ ] / - [x] | `- [x] 已完成` |

### 层级管理

```mermaid
flowchart LR
    A[输入: marker] --> B[计算前导空格数]
    B --> C[层级 = 空格数 // 2 + 1]
    C --> D[更新 current_level]
```

**层级示例**：

| 标记 | 前导空格 | 层级 |
|------|----------|------|
| `- ` | 0 | 1 |
| `  - ` | 2 | 2 |
| `    - ` | 4 | 3 |

## 状态管理

```mermaid
stateDiagram-v2
    [*] --> Level1
    Level1 --> Level2: 检测到二级列表
    Level2 --> Level3: 检测到三级列表
    Level3 --> Level2: 返回二级
    Level2 --> Level1: 返回一级
    Level1 --> Level1: 同级列表项
    Level1 --> [*]: reset() 调用
```

## 处理流程

```mermaid
sequenceDiagram
    participant Main as _make_snippet
    participant Strategy as ListStrategy
    
    Main->>Strategy: detect("- 一级项目")
    Strategy-->>Main: True
    Note right of Strategy: current_level = 1
    Main->>Strategy: process("- 一级项目")
    Strategy-->>Main: "- 一级项目"
    
    Main->>Strategy: detect("  - 二级项目")
    Strategy-->>Main: True
    Note right of Strategy: current_level = 2
    Main->>Strategy: process("  - 二级项目")
    Strategy-->>Main: "  - 二级项目"
    
    Main->>Strategy: detect("- [x] 已完成")
    Strategy-->>Main: True
    Note right of Strategy: current_level = 1
    Main->>Strategy: process("- [x] 已完成")
    Strategy-->>Main: "- [x] 已完成"
```

## 关键方法

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `detect()` | 检测列表项 | line, in_code_block | bool |
| `process()` | 处理列表行 | line | str |
| `_update_level()` | 更新层级 | marker | None |
| `is_child_item()` | 判断是否子项 | 无 | bool |
| `reset()` | 重置状态 | 无 | None |
