from vault_search.models import Document, Heading, Link
from vault_search.parser import parse_markdown


def test_document_model_smoke():
    heading = Heading(level=1, text="Title", line=3)
    link = Link(target="Other Note", alias="Other", line=5)
    doc = Document(
        path="wiki/title.md",
        title="Title",
        area="wiki",
        tags=["knowledge"],
        headings=[heading],
        links=[link],
        body="# Title\n[[Other Note|Other]]\n",
        mtime=123.0,
        explicit_title=True,
    )

    assert doc.path == "wiki/title.md"
    assert doc.headings[0].text == "Title"
    assert doc.links[0].alias == "Other"
    assert doc.explicit_title is True


def test_parse_markdown_frontmatter_headings_tags_and_links():
    text = """---
title: SSL Guide
tags: [network, 知识总结]
---
# SSL 证书

正文包含 #https 和 [[TLS|Transport Layer Security]]。

## Details
See [[Missing Note#Section]].
"""

    doc = parse_markdown(
        text,
        path="wiki/ssl.md",
        area="wiki",
        mtime=10.0,
    )

    assert doc.path == "wiki/ssl.md"
    assert doc.title == "SSL 证书"
    assert doc.explicit_title is True
    assert doc.tags == ["network", "知识总结", "https"]
    assert [heading.text for heading in doc.headings] == ["SSL 证书", "Details"]
    assert doc.links[0].target == "TLS"
    assert doc.links[0].alias == "Transport Layer Security"
    assert doc.links[1].target == "Missing Note#Section"
    assert "title: SSL Guide" not in doc.body


def test_parse_markdown_uses_filename_fallback_title():
    doc = parse_markdown("No heading here", path="notes/my-note.md", area="notes", mtime=1.0)

    assert doc.title == "my-note"
    assert doc.explicit_title is False
