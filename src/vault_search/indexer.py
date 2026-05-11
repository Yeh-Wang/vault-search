from __future__ import annotations

from pathlib import Path

from .database import rebuild_database
from .discovery import discover_markdown_files
from .models import Document, Link
from .parser import parse_markdown


def build_index(root: Path, db_path: Path | None = None) -> dict[str, int]:
    db_path = db_path or default_db_path(root)
    discovery = discover_markdown_files(root)
    documents: list[Document] = []

    for item in discovery.files:
        text = item.path.read_text(encoding="utf-8")
        documents.append(parse_markdown(text, path=item.relative_path, area=item.area, mtime=item.mtime))

    documents = _resolve_links(documents)
    return rebuild_database(db_path, documents, ignored_files=discovery.ignored_files)


def default_db_path(root: Path) -> Path:
    return root / "tmp" / "vault-search.sqlite"


def _resolve_links(documents: list[Document]) -> list[Document]:
    title_index: dict[str, str] = {}
    stem_index: dict[str, str] = {}
    path_index: dict[str, str] = {}

    for doc in documents:
        title_index[doc.title] = doc.path
        path = Path(doc.path)
        stem_index[path.stem] = doc.path
        path_index[doc.path] = doc.path

    return [_with_resolved_links(doc, title_index, stem_index, path_index) for doc in documents]


def _with_resolved_links(
    doc: Document,
    title_index: dict[str, str],
    stem_index: dict[str, str],
    path_index: dict[str, str],
) -> Document:
    links = []
    for link in doc.links:
        base_target = link.target.split("#", 1)[0].strip()
        resolved = path_index.get(base_target) or title_index.get(base_target) or stem_index.get(base_target)
        links.append(Link(target=link.target, alias=link.alias, line=link.line, resolved_path=resolved))

    return Document(
        path=doc.path,
        title=doc.title,
        area=doc.area,
        tags=doc.tags,
        headings=doc.headings,
        links=links,
        body=doc.body,
        mtime=doc.mtime,
        explicit_title=doc.explicit_title,
    )
