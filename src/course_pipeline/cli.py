"""Command-line ingestion entrypoint for Windows/PowerShell."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .ingestion import scan_sources
from .registry import SourceRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="Register course source documents.")
    parser.add_argument("source_dir", type=Path, help="Directory containing source lectures")
    parser.add_argument("--db", type=Path, default=Path("data/registry.sqlite3"))
    args = parser.parse_args()
    with SourceRegistry(args.db) as registry:
        report = scan_sources(args.source_dir, registry)
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
