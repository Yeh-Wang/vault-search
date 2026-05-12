from pathlib import Path

from vault_search.config import (
    detect_vault_root,
    global_config_path,
    load_global_config,
    load_project_config,
    project_config_path,
    resolve_root,
    resolve_setting,
    save_global_config,
    save_project_config,
)


def test_global_config_path_uses_home():
    """全局配置路径应在 ~/.config/vault-search/ 下"""
    path = global_config_path()
    assert path == Path.home() / ".config" / "vault-search" / "config.json"


def test_project_config_path_under_obsidian():
    """项目配置路径应在 <vault>/.obsidian/ 下"""
    vault = Path("/tmp/my-vault")
    path = project_config_path(vault)
    assert path == vault / ".obsidian" / "vault-search.json"


def test_detect_vault_root_finds_obsidian_dir(tmp_path: Path):
    """从子目录向上查找 .obsidian/，成功识别 vault root"""
    vault = tmp_path / "my-vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (vault / ".obsidian").mkdir()

    # 从子目录开始检测
    result = detect_vault_root(start=notes)
    assert result == vault.resolve()


def test_detect_vault_root_finds_from_cwd(tmp_path: Path, monkeypatch):
    """从当前工作目录检测 vault root"""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    monkeypatch.chdir(vault)

    result = detect_vault_root()
    assert result == vault.resolve()


def test_detect_vault_root_returns_none_when_not_found(tmp_path: Path):
    """没有 .obsidian/ 目录时返回 None"""
    empty = tmp_path / "no-vault"
    empty.mkdir()
    result = detect_vault_root(start=empty)
    assert result is None


def test_load_global_config_returns_empty_when_no_file(tmp_path: Path, monkeypatch):
    """全局配置文件不存在时返回空字典"""
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: tmp_path / "nonexistent.json")
    assert load_global_config() == {}


def test_save_and_load_global_config(tmp_path: Path, monkeypatch):
    """全局配置写入后可正确读取"""
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)

    save_global_config({"default_root": "/tmp/vault", "default_limit": 20})
    loaded = load_global_config()

    assert loaded["default_root"] == "/tmp/vault"
    assert loaded["default_limit"] == 20


def test_save_and_load_project_config(tmp_path: Path):
    """项目配置写入后可正确读取"""
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)

    save_project_config(vault, {"default_limit": 30})
    loaded = load_project_config(vault)

    assert loaded["default_limit"] == 30


def test_resolve_root_prefers_cli_over_auto_detect(tmp_path: Path, monkeypatch):
    """CLI --root 参数优先级最高"""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    monkeypatch.chdir(vault)

    # 即使在 vault 目录内（可自动检测），--root 仍然优先
    other = tmp_path / "other-vault"
    result = resolve_root(args_root=str(other))
    assert result == other


def test_resolve_root_auto_detects_obsidian(tmp_path: Path, monkeypatch):
    """在 vault 目录内运行时自动检测"""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    monkeypatch.chdir(vault)

    result = resolve_root()
    assert result == vault.resolve()


def test_resolve_root_falls_back_to_global_config(tmp_path: Path, monkeypatch):
    """无自动检测时，回退到全局配置的 default_root"""
    empty = tmp_path / "no-vault-here"
    empty.mkdir()
    monkeypatch.chdir(empty)

    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)
    save_global_config({"default_root": str(tmp_path / "my-vault")})

    result = resolve_root()
    assert result == tmp_path / "my-vault"


def test_resolve_root_returns_none_when_nothing_set(tmp_path: Path, monkeypatch):
    """既没有 CLI 参数，也没有自动检测，也没有全局配置时返回 None"""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: tmp_path / "nonexistent.json")

    result = resolve_root()
    assert result is None


def test_resolve_setting_merges_project_over_global(tmp_path: Path, monkeypatch):
    """项目级配置覆盖全局配置"""
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("vault_search.config.global_config_path", lambda: config_path)

    # 全局设置 limit=10
    save_global_config({"default_limit": 10})
    # 项目设置 limit=20
    save_project_config(vault, {"default_limit": 20})

    # 项目级覆盖全局
    assert resolve_setting("default_limit", vault_root=vault) == 20
    # 没有 project config 时用全局
    assert resolve_setting("default_limit", vault_root=None) == 10
    # 不存在的 key 用默认值
    assert resolve_setting("nonexistent", vault_root=vault, default=42) == 42
