from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_IGNORED_DIRS = {".obsidian", ".git", ".pytest_cache", "tmp", ".trash", "node_modules", ".venv"}


@dataclass(frozen=True)
class DiscoveredFile:
    path: Path
    relative_path: str
    area: str
    mtime: float


@dataclass(frozen=True)
class DiscoveryResult:
    files: list[DiscoveredFile]
    ignored_files: int


def discover_markdown_files(root: Path, ignored_dirs: set[str] | None = None) -> DiscoveryResult:
    ignored = ignored_dirs or DEFAULT_IGNORED_DIRS
    files: list[DiscoveredFile] = []
    ignored_files = 0

    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        parts = set(relative.parts[:-1])
        if parts & ignored:
            ignored_files += 1
            continue

        relative_path = relative.as_posix()
        files.append(
            DiscoveredFile(
                path=path,
                relative_path=relative_path,
                area=path_area(relative_path),
                mtime=path.stat().st_mtime,
            )
        )

    return DiscoveryResult(files=files, ignored_files=ignored_files)


def path_area(relative_path: str) -> str:
    parts = Path(relative_path).parts
    if len(parts) <= 1:
        return "root"
    return parts[0]
