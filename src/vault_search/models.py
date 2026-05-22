from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int


@dataclass(frozen=True)
class Link:
    target: str
    alias: str | None = None
    line: int = 0
    resolved_path: str | None = None


@dataclass(frozen=True)
class Document:
    path: str
    title: str
    area: str
    tags: list[str] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    body: str = ""
    mtime: float = 0.0
    explicit_title: bool = False


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
