"""CLI for phases 2,3,5,6 and 8. Phase 1 uses course-pipeline."""
import argparse
import json
from pathlib import Path
from .stages import parse_registry, search, export_project


def main(argv=None):
    parser = argparse.ArgumentParser(description="Parse and export course materials")
    parser.add_argument("--registry", type=Path, default=Path("data/registry.sqlite3"))
    parser.add_argument("--parsed", type=Path, default=Path("data/parsed.sqlite3"))
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("parse")
    p.add_argument("source_root", type=Path)
    p.add_argument("--backend", choices=["docling", "pymupdf-diagnostic"],
                   default="docling")
    s = commands.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=10)
    e = commands.add_parser("export")
    e.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    if args.command == "parse":
        output = parse_registry(args.registry, args.source_root, args.parsed, args.backend)
    elif args.command == "search":
        output = search(args.parsed, args.query, args.limit)
    else:
        output = export_project(args.registry, args.parsed, args.destination)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return output


if __name__ == "__main__":
    main()
