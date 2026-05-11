from vault_search.database import health_summary, search_documents
from vault_search.indexer import build_index


def test_build_index_discovers_parses_resolves_and_rebuilds(sample_vault):
    db_path = sample_vault / "tmp" / "vault-search.sqlite"

    summary = build_index(sample_vault, db_path)
    results = search_documents(db_path, "TLS", limit=10)
    health = health_summary(db_path)

    assert summary["documents"] == 4
    assert any(item["path"] == "wiki/TLS.md" for item in results)
    assert health["ignored_files"] == 3
    assert health["broken_wikilinks"] == 1


def test_build_index_handles_empty_vault(tmp_path):
    root = tmp_path / "empty-vault"
    root.mkdir()
    db_path = root / "tmp" / "vault-search.sqlite"

    summary = build_index(root, db_path)
    health = health_summary(db_path)

    assert summary == {"documents": 0, "ignored_files": 0}
    assert health["documents"] == 0
    assert health["areas"] == {}
    assert health["tags"] == 0
    assert health["missing_tags"] == 0
    assert health["missing_titles"] == 0
    assert health["wikilinks"] == 0
    assert health["broken_wikilinks"] == 0
