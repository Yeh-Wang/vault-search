import json
import sys

from vault_search.cli import main_health, main_index, main_search


def test_cli_index_search_and_health_with_root(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault)])
    assert main_index() == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["summary"]["documents"] == 4

    monkeypatch.setattr(sys, "argv", ["vault-search", "TLS", "--root", str(sample_vault), "--json"])
    assert main_search() == 0
    search_payload = json.loads(capsys.readouterr().out)
    assert any(item["path"] == "wiki/TLS.md" for item in search_payload["results"])
    assert all("snippet" in item for item in search_payload["results"])

    monkeypatch.setattr(sys, "argv", ["vault-health", "--root", str(sample_vault), "--json"])
    assert main_health() == 0
    health_payload = json.loads(capsys.readouterr().out)
    assert health_payload["summary"]["broken_wikilinks"] == 1


def test_cli_search_supports_db_override(sample_vault, capsys, monkeypatch):
    db_path = sample_vault / "tmp" / "custom.sqlite"
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault), "--db", str(db_path)])
    assert main_index() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vault-search", "证书", "--db", str(db_path), "--json"])
    assert main_search() == 0
    payload = json.loads(capsys.readouterr().out)

    assert "results" in payload
    assert all("snippet" in item for item in payload["results"])


def test_cli_search_supports_area_and_tag_filters(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault)])
    assert main_index() == 0
    capsys.readouterr()

    monkeypatch.setattr(
        sys,
        "argv",
        ["vault-search", "Java", "--root", str(sample_vault), "--area", "IT-learning", "--tag", "java", "--json"],
    )
    assert main_search() == 0
    payload = json.loads(capsys.readouterr().out)

    assert [item["path"] for item in payload["results"]] == ["IT-learning/java-basic/java.md"]


def test_cli_index_handles_empty_vault(tmp_path, capsys, monkeypatch):
    root = tmp_path / "empty-vault"
    root.mkdir()

    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(root)])
    assert main_index() == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"] == {"documents": 0, "ignored_files": 0}


def test_cli_text_search_prints_snippet(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault)])
    assert main_index() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vault-search", "TLS", "--root", str(sample_vault)])
    assert main_search() == 0
    output = capsys.readouterr().out

    assert "wiki/TLS.md | TLS |" in output
    assert "  # TLS" in output


def test_cli_text_search_prints_no_results(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vault-index", "--root", str(sample_vault)])
    assert main_index() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vault-search", "no-such-term", "--root", str(sample_vault)])
    assert main_search() == 0

    assert capsys.readouterr().out == "No results.\n"


def test_cli_search_reports_missing_database(tmp_path, capsys, monkeypatch):
    missing_db = tmp_path / "missing.sqlite"

    monkeypatch.setattr(sys, "argv", ["vault-search", "TLS", "--db", str(missing_db)])
    try:
        main_search()
    except SystemExit as exc:
        assert exc.code == 2

    assert "database not found" in capsys.readouterr().err


def test_cli_health_reports_missing_database(tmp_path, capsys, monkeypatch):
    missing_db = tmp_path / "missing.sqlite"

    monkeypatch.setattr(sys, "argv", ["vault-health", "--db", str(missing_db)])
    try:
        main_health()
    except SystemExit as exc:
        assert exc.code == 2

    assert "database not found" in capsys.readouterr().err
