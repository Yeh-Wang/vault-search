from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import (
    global_config_path,
    load_global_config,
    load_project_config,
    project_config_path,
    resolve_root,
    resolve_setting,
    save_global_config,
    save_project_config,
)
from .database import health_summary
from .formatter import OutputFormatter
from .indexer import build_index, default_db_path
from .search import SearchEngine

# Windows 终端 UTF-8 输出
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


class _CliError(Exception):
    """CLI 层错误，由 main() 捕获后输出到 stderr 并退出。"""
    pass


def main() -> int:
    """统一入口：vlt <subcommand> [options]"""
    parser = argparse.ArgumentParser(prog="vlt", description="Obsidian vault 本地搜索工具")
    sub = parser.add_subparsers(dest="command", required=True)

    # vlt index
    idx = sub.add_parser("index", help="建立/重建索引")
    idx.add_argument("--root", help="vault 根目录路径")
    idx.add_argument("--db", help="数据库文件路径（默认 <vault>/tmp/vault-search.sqlite）")

    # vlt search
    sch = sub.add_parser("search", help="搜索笔记")
    sch.add_argument("query", help="搜索关键词")
    sch.add_argument("--root", help="vault 根目录路径")
    sch.add_argument("--db", help="数据库文件路径")
    sch.add_argument("--area", help="按区域（顶层目录）过滤，如 IT-learning")
    sch.add_argument("--tag", action="append", default=[], help="按标签过滤，可多次使用")
    sch.add_argument("--limit", type=int, default=None, help="返回结果数量（默认读取配置或 10）")
    sch.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    sch.add_argument("--compact", action="store_true", help="以紧凑格式输出")

    # vlt health
    hlt = sub.add_parser("health", help="检查 vault 健康状况")
    hlt.add_argument("--root", help="vault 根目录路径")
    hlt.add_argument("--db", help="数据库文件路径")
    hlt.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    # vlt config
    cfg = sub.add_parser("config", help="管理配置")
    cfg_sub = cfg.add_subparsers(dest="action", required=True)

    set_p = cfg_sub.add_parser("set", help="设置配置项")
    set_p.add_argument("key", help="配置键名，如 default_root")
    set_p.add_argument("value", help="配置值")
    set_p.add_argument("--local", action="store_true", help="写入项目级配置（<vault>/.obsidian/vault-search.json）")
    set_p.add_argument("--root", help="vault 根目录路径（用于 --local 定位项目配置）")

    get_p = cfg_sub.add_parser("get", help="查看配置值")
    get_p.add_argument("key", help="配置键名")
    get_p.add_argument("--root", help="vault 根目录路径")

    list_p = cfg_sub.add_parser("list", help="列出所有配置及来源")
    list_p.add_argument("--root", help="vault 根目录路径")

    cfg_sub.add_parser("path", help="显示全局配置文件路径")

    args = parser.parse_args(sys.argv[1:])

    if args.command == "index":
        return _cmd_index(args, parser)
    elif args.command == "search":
        try:
            return _cmd_search(args, parser)
        except _CliError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
    elif args.command == "health":
        try:
            return _cmd_health(args, parser)
        except _CliError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
    elif args.command == "config":
        return _cmd_config(args)
    return 1


def _cmd_index(args, parser: argparse.ArgumentParser) -> int:
    """vlt index — 建立索引"""
    root = _require_root(args.root, parser)
    db_path = Path(args.db) if args.db else default_db_path(root)
    summary = build_index(root, db_path)
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0


def _cmd_search(args, parser: argparse.ArgumentParser) -> int:
    """vlt search — 搜索笔记"""
    root = _resolve_root_or_none(args.root)
    db_path = _resolve_db(root, args.db, parser)
    _auto_build_index_if_needed(db_path, root)

    # limit 优先级：CLI 参数 > 项目配置 > 全局配置 > 硬编码默认值 10
    limit = args.limit if args.limit is not None else resolve_setting("default_limit", root, default=10)

    # 使用新的 SearchEngine 接口
    engine = SearchEngine(db_path)
    results = engine.search(query=args.query, limit=limit, area=args.area, tags=args.tag)

    formatter = OutputFormatter()
    
    if args.json:
        print(formatter.format_json(results, args.query))
    elif args.compact:
        print(formatter.format_compact(results))
    else:
        print(formatter.format_text(results))
    
    return 0


def _cmd_health(args, parser: argparse.ArgumentParser) -> int:
    """vlt health — 检查 vault 健康状况"""
    root = _resolve_root_or_none(args.root)
    db_path = _resolve_db(root, args.db, parser)
    _auto_build_index_if_needed(db_path, root)
    payload = {"summary": health_summary(db_path)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload["summary"].items():
            print(f"{key}: {value}")
    return 0


def _cmd_config(args) -> int:
    """vlt config — 管理配置"""
    root = getattr(args, "root", None)
    if args.action == "set":
        return _config_set(args.key, args.value, args.local, root)
    elif args.action == "get":
        return _config_get(args.key, root)
    elif args.action == "list":
        return _config_list(root)
    elif args.action == "path":
        print(global_config_path())
        return 0
    return 1


def _config_set(key: str, value: str, local: bool, args_root: str | None = None) -> int:
    """写入配置项。--local 时写入项目级配置（自动检测 vault root），否则写入全局配置。"""
    parsed_value = _parse_value(value)

    if local:
        root = resolve_root(args_root)
        if not root:
            print("Error: cannot determine vault root. Run inside a vault or use --root.", file=sys.stderr)
            return 1
        config = load_project_config(root)
        config[key] = parsed_value
        save_project_config(root, config)
        print(f"Saved to project config: {project_config_path(root)}")
    else:
        config = load_global_config()
        config[key] = parsed_value
        save_global_config(config)
        print(f"Saved to global config: {global_config_path()}")

    return 0


def _config_get(key: str, args_root: str | None = None) -> int:
    """查看配置值，合并项目级 > 全局级。"""
    root = resolve_root(args_root)
    value = resolve_setting(key, root)
    if value is ...:
        print(f"(not set) {key}")
        return 1
    print(json.dumps(value, ensure_ascii=False))
    return 0


def _config_list(args_root: str | None = None) -> int:
    """列出所有配置，标注来源。"""
    global_cfg = load_global_config()
    root = resolve_root(args_root)
    project_cfg = load_project_config(root) if root else {}

    all_keys = sorted(set(list(global_cfg.keys()) + list(project_cfg.keys())))
    if not all_keys:
        print("No config. Run vlt config set <key> <value> to add.")
        return 0

    for key in all_keys:
        if key in project_cfg:
            print(f"  {key} = {json.dumps(project_cfg[key], ensure_ascii=False)}  (project)")
        elif key in global_cfg:
            print(f"  {key} = {json.dumps(global_cfg[key], ensure_ascii=False)}  (global)")
    return 0


def _parse_value(value: str):
    """尝试将字符串值解析为 JSON 类型（int/float/bool/list），失败则保持字符串。"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return value


def _require_root(args_root: str | None, parser: argparse.ArgumentParser) -> Path:
    """解析 vault root，解析失败则报错退出。"""
    root = resolve_root(args_root)
    if not root:
        parser.error("cannot determine vault root. Use --root, run inside a vault, or set default_root via vlt config.")
    return root


def _resolve_root_or_none(args_root: str | None) -> Path | None:
    """解析 vault root，允许返回 None（用于 --db 直接指定数据库的场景）。"""
    return resolve_root(args_root)


def _resolve_db(root: Path | None, db: str | None, parser: argparse.ArgumentParser) -> Path:
    """解析数据库路径：--db 直接指定 > 根据 root 推导默认路径。"""
    if db:
        return Path(db)
    if root:
        return default_db_path(root)
    parser.error("cannot determine database path. Use --root or --db.")
    raise AssertionError("unreachable")


def _auto_build_index_if_needed(db_path: Path, root: Path | None) -> None:
    """数据库不存在时自动建索引，避免手动先跑 vlt index。

    仅在能确定 vault root 时自动执行；如果用 --db 指定了路径但找不到 root，抛出错误。
    """
    if db_path.exists():
        return
    if not root:
        raise _CliError(f"database not found: {db_path}. Run vlt index first.")
    build_index(root, db_path)