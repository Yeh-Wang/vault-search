# Search Quality Fix

Date: 2026-05-28

## Background

搜索功能在实际使用中结果质量差，用户难以找到期望的内容。经代码审查发现多个逻辑缺陷共同影响了搜索准确性。

## Issues & Fixes

### 1. `in_code_block` 状态在排序后错乱

**File:** `src/vault_search/snippet.py`

**Problem:** `SnippetGenerator.generate()` 在按分数排序候选行后，重新通过 ``` toggle 追踪 `in_code_block` 状态。但排序后行已不在文档原始顺序，导致状态完全错误。`_collect_matches` 已经按文档顺序正确记录了每行的 `in_code_block`，但被忽略。

**Fix:** 直接使用 `candidate["in_code_block"]`（由 `_collect_matches` 按文档顺序正确记录的值），移除 `generate()` 中的重复追踪逻辑。

**Impact:** 代码块策略（`CodeBlockStrategy`）的 `detect()` 现在能拿到正确的代码块状态，代码内容不再被误判为普通文本。

### 2. FTS5 rank 未使用，所有 score 为 0

**File:** `src/vault_search/database.py`, `src/vault_search/search.py`

**Problem:** `search_fts` 查询不包含 FTS5 的 `rank` 列，`search_like` 也不返回 score。导致所有 `SearchResult.score` 始终为 0，无法按相关性排序。

**Fix:**
- `search_fts`: 查询增加 `f.rank`，按 `ORDER BY f.rank` 排序，返回 `-rank` 作为正分数
- `search_like`: 标题匹配给 1.0 分，正文匹配给 0.5 分

### 3. LIKE 查询中 `%` 和 `_` 未转义

**File:** `src/vault_search/database.py`

**Problem:** `search_like` 直接用 `f"%{query}%"` 构造 LIKE 模式，用户输入的 `%` 和 `_` 会被当作 LIKE 通配符，导致搜索结果不准确。

**Fix:** 转义 `\`、`%`、`_`，并使用 `ESCAPE '\\'` 子句告知 SQLite 转义字符。

### 4. FTS5 特殊字符未处理

**File:** `src/vault_search/database.py`

**Problem:** 用户输入直接传入 FTS5 `MATCH`，包含 `AND`、`OR`、`NOT`、`*`、`"`、`(`、`)` 等特殊字符时会导致查询失败或意外行为。虽然有 `try/except` 兜底，但静默返回空结果，用户无感知。

**Fix:** 新增 `_sanitize_fts_query()` 静态方法：
- 移除 FTS5 特殊字符 `"()*^:+`
- 将 FTS5 关键字（`AND`、`OR`、`NOT`、`NEAR`）用双引号包裹
- 词项间用 `OR` 连接，实现宽松匹配

### 5. 数据库连接浪费

**File:** `src/vault_search/database.py`, `src/vault_search/search.py`

**Problem:** `SearchEngine.search()` 一次搜索打开 N+2 个连接（`search_fts` 1个 + `search_like` 1个 + 每个结果的 `get_tags` 各1个）。

**Fix:**
- `search_fts`、`search_like` 新增可选 `conn` 参数，支持传入外部连接
- 新增 `get_tags_with_conn()` 方法
- `SearchEngine.search()` 使用 `with self.db.connect() as conn` 共享连接

### 6. 摘要增加标题上下文

**File:** `src/vault_search/snippet.py`

**Problem:** 搜索摘要只显示匹配行本身，缺少所属标题上下文，用户难以判断匹配内容属于哪个章节。

**Fix:**
- `_collect_matches` 追踪当前标题（`current_heading`），每个候选行记录其所属标题
- 标题本身如果包含查询词，作为独立候选（+50 分，最强信号）
- `generate()` 输出时，非标题匹配行附带缩进的所属标题作为上下文前缀

**Impact:** 摘要可读性显著提升，用户能快速定位匹配内容所属章节。

### 7. 代码注释降权

**File:** `src/vault_search/snippet.py`

**Problem:** 代码块内的注释（`//` 或 `#` 开头）与正文同权重，经常排在真正有意义的代码行前面。

**Fix:** 代码块内注释行在评分时 -20 分降权。

### 8. 清理死代码

- `cli.py`: 移除未使用的 `search_documents` 导入
- `snippet_strategies/table.py`: 移除从未被读取的 `header_row` 状态和 `_is_separator_line` 方法

## Test Results

```
38 passed in 0.58s
```

All existing tests pass. No test changes required.
