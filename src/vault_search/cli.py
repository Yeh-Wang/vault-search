from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .database import health_summary, search_documents
from .indexer import build_index, default_db_path


def main_index() -> int:
    parser = argparse.ArgumentParser(prog="vault-index")
    parser.add_argument("--root", required=True)
    parser.add_argument("--db")
    args = parser.parse_args(sys.argv[1:])

    root = Path(args.root)
    db_path = Path(args.db) if args.db else default_db_path(root)
    summary = build_index(root, db_path)
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0


def main_search() -> int:
    parser = argparse.ArgumentParser(prog="vault-search")
    parser.add_argument("query")
    parser.add_argument("--root")
    parser.add_argument("--db")
    parser.add_argument("--area")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    db_path = _resolve_db(args.root, args.db, parser)
    _require_existing_db(db_path, parser)
    results = search_documents(db_path, query=args.query, limit=args.limit, area=args.area, tags=args.tag)
    payload = {"query": args.query, "results": results}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results.")
        else:
            for item in results:
                tags = ", ".join(item["tags"])
                print(f"{item['path']} | {item['title']} | {tags}")
                print(f"  {item['snippet']}")
    return 0


def main_health() -> int:
    parser = argparse.ArgumentParser(prog="vault-health")
    parser.add_argument("--root")
    parser.add_argument("--db")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    db_path = _resolve_db(args.root, args.db, parser)
    _require_existing_db(db_path, parser)
    payload = {"summary": health_summary(db_path)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload["summary"].items():
            print(f"{key}: {value}")
    return 0


def _resolve_db(root: str | None, db: str | None, parser: argparse.ArgumentParser) -> Path:
    if db:
        return Path(db)
    if root:
        return default_db_path(Path(root))
    parser.error("one of --root or --db is required")
    raise AssertionError("unreachable")


def _require_existing_db(db_path: Path, parser: argparse.ArgumentParser) -> None:
    if not db_path.exists():
        parser.error(f"database not found: {db_path}. Run vault-index first.")
