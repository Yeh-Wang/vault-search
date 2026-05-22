# 查询逻辑重构设计文档

## 1. 现状分析

### 1.1 当前架构

```mermaid
graph TD
    A[cli.py] --> B[database.py]
    B --> C[(SQLite)]
    
    subgraph database.py
        D[数据库CRUD]
        E[搜索逻辑]
        F[摘要生成]
        G[结果格式化]
    end
```

### 1.2 问题识别

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| 职责混杂 | 难以定位和修改 | 高 |
| 可测试性差 | 单元测试困难 | 高 |
| 扩展性受限 | 新增功能影响全局 | 中 |
| 代码复用率低 | 无法单独使用组件 | 中 |

---

## 2. 重构目标

| 目标 | 描述 |
|------|------|
| **单一职责** | 每个模块只负责一件事 |
| **高内聚低耦合** | 模块内部紧密，模块间松散 |
| **可测试性** | 各模块可独立单元测试 |
| **可扩展性** | 易于添加新功能 |
| **代码复用** | 组件可独立复用 |

---

## 3. 重构方案

### 3.1 新架构设计

```mermaid
graph TD
    A[cli.py] --> B[search.py]
    A --> C[formatter.py]
    
    B --> D[database.py]
    B --> E[snippet.py]
    
    D --> F[(SQLite)]
    
    subgraph search.py
        G[SearchEngine]
    end
    
    subgraph database.py
        H[Database]
    end
    
    subgraph snippet.py
        I[SnippetGenerator]
    end
    
    subgraph formatter.py
        J[OutputFormatter]
    end
```

### 3.2 模块职责划分

| 模块 | 职责 | 核心类/函数 |
|------|------|-------------|
| `database.py` | 纯数据库操作 | `Database` 类 |
| `search.py` | 搜索核心逻辑 | `SearchEngine` 类 |
| `snippet.py` | 智能摘要生成 | `SnippetGenerator` 类 |
| `formatter.py` | CLI输出格式化 | `OutputFormatter` 类 |
| `models.py` | 数据模型定义 | `SearchResult` 数据类 |

### 3.3 类设计

#### 3.3.1 Database 类

```mermaid
classDiagram
    class Database {
        -db_path: Path
        +__init__(db_path: Path)
        +connect() Connection
        +create_schema() None
        +rebuild(documents: list) dict
        +search_fts(query, limit, area, tags) list
        +search_like(query, limit, area, tags) list
        +get_document(path) dict
        +get_tags(path) list
        +health() dict
    }
```

#### 3.3.2 SearchEngine 类

```mermaid
classDiagram
    class SearchEngine {
        -db: Database
        +__init__(db_path: Path)
        +search(query, limit, area, tags) list[SearchResult]
        -_needs_fallback(query, fts_results) bool
        -_merge_results(results) list[SearchResult]
        -_apply_filters(results, filters) list[SearchResult]
    }
```

#### 3.3.3 SnippetGenerator 类

```mermaid
classDiagram
    class SnippetGenerator {
        -strategies: list[SnippetStrategy]
        +__init__()
        +generate(title, body, query) str
        -_calculate_max_matches(body) int
        -_calculate_score(line, query) int
        -_collect_matches(body, query) list
    }
```

#### 3.3.4 OutputFormatter 类

```mermaid
classDiagram
    class OutputFormatter {
        +format_text(results) str
        +format_json(results) str
        +format_compact(results) str
        -_format_single(result) str
    }
```

#### 3.3.5 SearchResult 数据类

```mermaid
classDiagram
    class SearchResult {
        +path: str
        +title: str
        +area: str
        +tags: list[str]
        +snippet: str
        +score: float
        +to_dict() dict
    }
```

---

## 4. 调用链路

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant SE as SearchEngine
    participant DB as Database
    participant SG as SnippetGenerator
    participant OF as OutputFormatter
    
    CLI->>SE: SearchEngine(db_path)
    SE->>DB: Database(db_path)
    
    CLI->>SE: search(query, limit=10, area=None, tags=[])
    SE->>DB: search_fts(query, limit)
    DB-->>SE: fts_results
    
    alt 需要fallback（CJK查询或无结果）
        SE->>DB: search_like(query, limit)
        DB-->>SE: like_results
    end
    
    SE->>SE: _merge_results(fts, like)
    
    loop 每个文档
        SE->>DB: get_tags(path)
        DB-->>SE: tags
        
        SE->>SG: generate(title, body, query)
        SG-->>SE: snippet
        
        SE->>SE: 创建 SearchResult
    end
    
    SE-->>CLI: list[SearchResult]
    
    CLI->>OF: format_text(results)
    OF-->>CLI: formatted_output
    
    CLI->>CLI: print(output)
```

---

## 5. 迁移步骤

### 阶段一：创建新模块

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1 | 创建 `SearchResult` 数据类 | `models.py` |
| 2 | 创建 `Database` 类 | `database.py` |
| 3 | 创建 `SearchEngine` 类 | `search.py` |
| 4 | 创建 `SnippetGenerator` 类 | `snippet.py` |
| 5 | 创建 `OutputFormatter` 类 | `formatter.py` |

### 阶段二：更新调用方

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6 | 更新 CLI 使用新接口 | `cli.py` |
| 7 | 更新测试用例 | `tests/` |

### 阶段三：清理旧代码

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8 | 删除旧函数 | `database.py` |
| 9 | 运行测试验证 | - |

---

## 6. 优化点说明

### 6.1 智能摘要优化

```mermaid
flowchart TD
    A[输入: body, query] --> B[计算文档长度]
    B --> C[动态确定 max_matches]
    C --> D[逐行扫描]
    D --> E{包含查询词?}
    E -->|是| F[计算匹配分数]
    F --> G[添加到候选集]
    E -->|否| D
    G --> H{达到文档末尾?}
    H -->|否| D
    H -->|是| I[按分数排序]
    I --> J[取前N个]
    J --> K[应用策略处理]
    K --> L[输出摘要]
```

**评分规则**：

| 因素 | 权重 | 说明 |
|------|------|------|
| 标题行 | +30 | 标题中的匹配更重要 |
| 查询词位置 | +0~20 | 越靠前分数越高 |
| 查询词频率 | +15/次 | 出现次数越多越好 |
| 行长度适中 | +10 | 80字符以内加分 |

### 6.2 动态匹配数量

```mermaid
flowchart LR
    A[文档行数] --> B{< 10?}
    B -->|是| C[max_matches = 2]
    B -->|否| D{< 50?}
    D -->|是| E[max_matches = 3]
    D -->|否| F{< 100?}
    F -->|是| G[max_matches = 4]
    F -->|否| H[max_matches = 5]
```

---

## 7. 预期效果

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 模块职责数 | 4+ | 1 |
| 单元测试覆盖率 | 低 | 高 |
| 代码复用率 | 低 | 高 |
| 新增功能成本 | 高 | 低 |
| 维护难度 | 高 | 低 |

---

## 8. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 引入新bug | 中 | 完整测试覆盖 |
| 性能下降 | 低 | 保持原有算法 |
| API变更 | 中 | 向后兼容设计 |

---

## 9. 代码示例

### 9.1 SearchResult 数据类

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchResult:
    path: str
    title: str
    area: str
    tags: list[str]
    snippet: str
    score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "area": self.area,
            "tags": self.tags,
            "snippet": self.snippet,
        }
```

### 9.2 搜索调用示例

```python
# 重构前
results = search_documents(db_path, query, limit=10)

# 重构后
engine = SearchEngine(db_path)
results = engine.search(query, limit=10, area=None, tags=[])
```

---

## 附录：目录结构

```plaintext
src/vault_search/
├── __init__.py
├── cli.py              # CLI入口
├── config.py           # 配置管理
├── database.py         # 数据库操作（重构后）
├── discovery.py        # 文件发现
├── indexer.py          # 索引构建
├── models.py           # 数据模型（新增 SearchResult）
├── parser.py           # Markdown解析
├── search.py           # 搜索引擎（新增）
├── snippet.py          # 摘要生成器（新增）
├── formatter.py        # 输出格式化器（新增）
└── snippet_strategies/ # 策略模式目录
    ├── __init__.py
    ├── base.py
    ├── code_block.py
    ├── table.py
    ├── list.py
    └── plain_text.py
```
