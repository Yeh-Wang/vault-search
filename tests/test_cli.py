import json
import sys

from vault_search.cli import main


def test_cli_index_search_and_health_with_root(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(sample_vault)])
    assert main() == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["summary"]["documents"] == 4

    monkeypatch.setattr(sys, "argv", ["vlt", "search", "TLS", "--root", str(sample_vault), "--json"])
    assert main() == 0
    search_payload = json.loads(capsys.readouterr().out)
    assert any(item["path"] == "wiki/TLS.md" for item in search_payload["results"])
    assert all("snippet" in item for item in search_payload["results"])

    monkeypatch.setattr(sys, "argv", ["vlt", "health", "--root", str(sample_vault), "--json"])
    assert main() == 0
    health_payload = json.loads(capsys.readouterr().out)
    assert health_payload["summary"]["broken_wikilinks"] == 1


def test_cli_search_supports_db_override(sample_vault, capsys, monkeypatch):
    db_path = sample_vault / "tmp" / "custom.sqlite"
    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(sample_vault), "--db", str(db_path)])
    assert main() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vlt", "search", "证书", "--db", str(db_path), "--json"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)

    assert "results" in payload
    assert all("snippet" in item for item in payload["results"])


def test_cli_search_supports_area_and_tag_filters(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(sample_vault)])
    assert main() == 0
    capsys.readouterr()

    monkeypatch.setattr(
        sys,
        "argv",
        ["vlt", "search", "Java", "--root", str(sample_vault), "--area", "IT-learning", "--tag", "java", "--json"],
    )
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)

    assert [item["path"] for item in payload["results"]] == ["IT-learning/java-basic/java.md"]


def test_cli_index_handles_empty_vault(tmp_path, capsys, monkeypatch):
    root = tmp_path / "empty-vault"
    root.mkdir()

    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(root)])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["summary"] == {"documents": 0, "ignored_files": 0}


def test_cli_text_search_prints_snippet(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(sample_vault)])
    assert main() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vlt", "search", "TLS", "--root", str(sample_vault)])
    assert main() == 0
    output = capsys.readouterr().out

    assert "Path:   wiki/TLS.md" in output
    assert "Title:  TLS" in output


def test_cli_text_search_prints_no_results(sample_vault, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["vlt", "index", "--root", str(sample_vault)])
    assert main() == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["vlt", "search", "no-such-term", "--root", str(sample_vault)])
    assert main() == 0

    assert capsys.readouterr().out == "No results.\n"


def test_cli_search_auto_builds_index(sample_vault, capsys, monkeypatch):
    """vlt search 在数据库不存在但有 root 时，自动建索引而不是报错。"""
    monkeypatch.setattr(sys, "argv", ["vlt", "search", "TLS", "--root", str(sample_vault)])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Path:   wiki/TLS.md" in output


def test_cli_health_auto_builds_index(sample_vault, capsys, monkeypatch):
    """vlt health 在数据库不存在但有 root 时，自动建索引而不是报错。"""
    monkeypatch.setattr(sys, "argv", ["vlt", "health", "--root", str(sample_vault)])
    assert main() == 0
    output = capsys.readouterr().out
    assert "documents:" in output


def test_cli_config_set_global(tmp_path, capsys, monkeypatch):
    """vlt config set 写入全局配置。"""
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)

    monkeypatch.setattr(sys, "argv", ["vlt", "config", "set", "default_limit", "20"])
    assert main() == 0
    assert "global" in capsys.readouterr().out

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["default_limit"] == 20


def test_cli_config_set_local_with_root(sample_vault, capsys, monkeypatch):
    """vlt config set --local --root 写入项目级配置。"""
    monkeypatch.setattr(sys, "argv", ["vlt", "config", "set", "--root", str(sample_vault), "default_limit", "30", "--local"])
    assert main() == 0
    assert "project" in capsys.readouterr().out.lower()

    from vault_search.config import project_config_path
    saved = json.loads(project_config_path(sample_vault).read_text(encoding="utf-8"))
    assert saved["default_limit"] == 30


def test_cli_config_get(tmp_path, capsys, monkeypatch):
    """vlt config get 查看配置值。"""
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)

    # 先设值
    config_path.write_text('{"default_limit": 15}', encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["vlt", "config", "get", "default_limit"])
    assert main() == 0
    assert "15" in capsys.readouterr().out


def test_cli_config_list(tmp_path, capsys, monkeypatch):
    """vlt config list 列出配置。"""
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)
    config_path.write_text('{"default_limit": 10}', encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["vlt", "config", "list"])
    assert main() == 0
    output = capsys.readouterr().out
    assert "default_limit" in output
    assert "global" in output


def test_cli_config_path(capsys, monkeypatch):
    """vlt config path 显示配置文件路径。"""
    monkeypatch.setattr(sys, "argv", ["vlt", "config", "path"])
    assert main() == 0
    output = capsys.readouterr().out.strip()
    assert "vault-search" in output


def test_cli_search_reports_missing_db_without_root(tmp_path, capsys, monkeypatch):
    """vlt search 使用 --db 但无 root 且数据库不存在时，返回错误。"""
    db_path = tmp_path / "nonexistent.sqlite"
    empty = tmp_path / "no-vault"
    empty.mkdir()
    monkeypatch.chdir(empty)
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: tmp_path / "no-config.json")

    monkeypatch.setattr(sys, "argv", ["vlt", "search", "test", "--db", str(db_path)])
    assert main() == 2
    assert "Error" in capsys.readouterr().err
