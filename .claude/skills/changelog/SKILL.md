---
name: changelog
description: Use when source code changes are complete and need to be documented as a changelog entry in docs/changelog/
---

# Changelog Generator

## Overview

Generate or update a changelog entry after code changes are made to `src/vault_search/`.

## When to Use

- Source code modification is complete
- Hook reminded you to update docs
- User invokes `/changelog` explicitly

## Workflow

### 1. Gather Changes

```bash
git diff --stat HEAD        # overview
git diff HEAD               # full diff (or git diff HEAD~1..HEAD if committed)
```

### 2. Analyze

Identify meaningful changes from the diff:
- **Bug fixes**: root cause + fix
- **Features**: what + why + how
- **Refactoring**: what restructured + why
- **Performance**: what optimized + impact

Skip trivial changes (whitespace, formatting).

### 3. Create Document

File: `docs/changelog/YYYY-MM-DD-<short-topic>.md`

```markdown
# <Title>

Date: YYYY-MM-DD

## Background

1-3 sentences: why this change was needed.

## Changes

### <Category>

**File:** `path/to/file.py`

**Problem:** What was wrong.

**Fix:** What was changed and why.

**Impact:** Effect on behavior/performance.

## Test Results

<N tests passed>
```

If a changelog for today already exists, **update** it instead of creating a new one.

### 4. Update Project Status

Edit `docs/PROJECT_STATUS.md`:
- `Date:` field
- `Current State` description
- `Completed` list
- `Verification` section (test results)

### 5. Update CLAUDE.md

If new docs were added, update the relevant table in `CLAUDE.md` (`Design Documents` or `Changelog`).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Inventing changes not in diff | Only document what `git diff` shows |
| Creating duplicate entries | Check `docs/changelog/` first, update existing |
| Skipping PROJECT_STATUS | Always update date and state |
| Writing in wrong language | Match existing entries' language |
