from pathlib import Path

from vault_search.database import health_summary, rebuild_database, search_documents
from vault_search.models import Document, Heading, Link


def _docs():
    return [
        Document(
            path="wiki/ssl.md",
            title="SSL 证书",
            area="wiki",
            tags=["network", "知识总结"],
            headings=[Heading(level=1, text="SSL 证书", line=1)],
            links=[Link(target="TLS", alias=None, line=3, resolved_path="wiki/tls.md")],
            body="# SSL 证书\nSSL 证书用于 HTTPS。\n",
            mtime=1.0,
            explicit_title=True,
        ),
        Document(
            path="wiki/tls.md",
            title="TLS",
            area="wiki",
            tags=[],
            headings=[Heading(level=1, text="TLS", line=1)],
            links=[Link(target="Missing", alias=None, line=2, resolved_path=None)],
            body="# TLS\nTransport Layer Security\n",
            mtime=2.0,
            explicit_title=True,
        ),
    ]


def test_rebuild_and_search_fts(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    results = search_documents(db_path, query="SSL", limit=10)

    assert results[0]["path"] == "wiki/ssl.md"
    assert results[0]["title"] == "SSL 证书"
    assert results[0]["tags"] == ["network", "知识总结"]
    assert results[0]["snippet"] == "# SSL 证书"


def test_search_chinese_fallback(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    results = search_documents(db_path, query="证书用于", limit=10)

    assert [item["path"] for item in results] == ["wiki/ssl.md"]
    assert results[0]["snippet"] == "SSL 证书用于 HTTPS。"


def test_search_filters_by_area_and_tag(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    by_area = search_documents(db_path, query="TLS", area="wiki", limit=10)
    wrong_area = search_documents(db_path, query="TLS", area="notes", limit=10)
    by_tag = search_documents(db_path, query="SSL", tags=["network"], limit=10)
    wrong_tag = search_documents(db_path, query="SSL", tags=["missing"], limit=10)

    assert [item["path"] for item in by_area] == ["wiki/tls.md"]
    assert wrong_area == []
    assert [item["path"] for item in by_tag] == ["wiki/ssl.md"]
    assert wrong_tag == []


def test_health_summary(tmp_path: Path):
    db_path = tmp_path / "vault-search.sqlite"
    rebuild_database(db_path, _docs(), ignored_files=1)

    summary = health_summary(db_path)

    assert summary["documents"] == 2
    assert summary["areas"] == {"wiki": 2}
    assert summary["tags"] == 2
    assert summary["missing_tags"] == 1
    assert summary["missing_titles"] == 0
    assert summary["wikilinks"] == 2
    assert summary["broken_wikilinks"] == 1
    assert summary["ignored_files"] == 1
