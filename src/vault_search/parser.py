from __future__ import annotations

import re
from pathlib import Path

from .models import Document, Heading, Link

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
INLINE_TAG_RE = re.compile(r"(?<!\w)#([\w\-\u4e00-\u9fff]+)")


def parse_markdown(text: str, path: str, area: str, mtime: float = 0.0) -> Document:
    frontmatter, body = _split_frontmatter(text)
    frontmatter_tags = _parse_frontmatter_tags(frontmatter)
    headings = _parse_headings(body)
    links = _parse_links(body)
    inline_tags = _parse_inline_tags(body)
    tags = _dedupe(frontmatter_tags + inline_tags)
    title, explicit_title = _choose_title(frontmatter, headings, path)

    return Document(
        path=path,
        title=title,
        area=area,
        tags=tags,
        headings=headings,
        links=links,
        body=body,
        mtime=mtime,
        explicit_title=explicit_title,
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            if text.endswith("\n"):
                body += "\n"
            return frontmatter, body

    return "", text


def _parse_frontmatter_tags(frontmatter: str) -> list[str]:
    tags: list[str] = []
    lines = frontmatter.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("tags:"):
            value = stripped.partition(":")[2].strip()
            if value.startswith("[") and value.endswith("]"):
                tags.extend(part.strip().strip("\"'") for part in value[1:-1].split(","))
            elif value:
                tags.extend(value.strip().strip("\"'").split())
            else:
                for nested in lines[index + 1 :]:
                    nested = nested.strip()
                    if not nested.startswith("- "):
                        break
                    tags.append(nested[2:].strip().strip("\"'"))
            break
    return [tag for tag in tags if tag]


def _parse_headings(body: str) -> list[Heading]:
    headings: list[Heading] = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(level=len(match.group(1)), text=match.group(2), line=line_number))
    return headings


def _parse_links(body: str) -> list[Link]:
    links: list[Link] = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        for match in WIKILINK_RE.finditer(line):
            links.append(
                Link(
                    target=match.group(1).strip(),
                    alias=(match.group(2) or "").strip() or None,
                    line=line_number,
                )
            )
    return links


def _parse_inline_tags(body: str) -> list[str]:
    return [match.group(1) for match in INLINE_TAG_RE.finditer(body)]


def _choose_title(frontmatter: str, headings: list[Heading], path: str) -> tuple[str, bool]:
    if headings:
        return headings[0].text, True

    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("title:"):
            title = stripped.partition(":")[2].strip().strip("\"'")
            if title:
                return title, True

    return Path(path).stem, False


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
