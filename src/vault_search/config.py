from __future__ import annotations

import json
from pathlib import Path


def global_config_path() -> Path:
    """全局配置路径：~/.config/vault-search/config.json

    Windows 和 macOS 统一使用 Path.home()，无平台分支。
    """
    return Path.home() / ".config" / "vault-search" / "config.json"


def project_config_path(vault_root: Path) -> Path:
    """项目级配置路径：<vault>/.obsidian/vault-search.json

    每个 Obsidian vault 都有 .obsidian/ 目录，将配置放在这里与 Obsidian 插件惯例一致。
    """
    return vault_root / ".obsidian" / "vault-search.json"


def detect_vault_root(start: Path | None = None) -> Path | None:
    """从给定目录向上查找 .obsidian/ 目录，自动识别 vault 根路径。

    优先级：当前目录 → 父目录 → ... 直到找到含 .obsidian/ 的目录。
    """
    current = (start or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".obsidian").is_dir():
            return parent
    return None


def load_global_config() -> dict:
    """加载全局配置，文件不存在则返回空字典。"""
    path = global_config_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_project_config(vault_root: Path) -> dict:
    """加载项目级配置，文件不存在则返回空字典。"""
    path = project_config_path(vault_root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_global_config(config: dict) -> None:
    """写入全局配置，自动创建目录。"""
    path = global_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_project_config(vault_root: Path, config: dict) -> None:
    """写入项目级配置，自动创建目录。"""
    path = project_config_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_root(args_root: str | None = None) -> Path | None:
    """解析 vault 根路径，优先级：CLI --root > 自动检测 .obsidian/ > 全局配置 default_root。

    项目级配置不参与 root 解析（需要先知道 root 才能读取项目配置，存在循环依赖）。
    """
    # 1. CLI 显式指定
    if args_root:
        return Path(args_root)

    # 2. 从当前目录向上自动检测 .obsidian/
    detected = detect_vault_root()
    if detected:
        return detected

    # 3. 全局配置中的 default_root
    global_cfg = load_global_config()
    if "default_root" in global_cfg:
        return Path(global_cfg["default_root"])

    return None


def resolve_setting(key: str, vault_root: Path | None = None, default=...):
    """合并配置项：项目级 > 全局级 > 硬编码默认值。

    Args:
        key: 配置键名（如 "default_limit"）
        vault_root: 已解析的 vault 根路径，用于读取项目级配置
        default: 找不到任何配置时的返回值
    """
    # 全局配置为基础
    merged = load_global_config()

    # 项目级配置覆盖全局
    if vault_root:
        merged.update(load_project_config(vault_root))

    return merged.get(key, default)
