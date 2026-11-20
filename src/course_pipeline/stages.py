"""Phase 2-8 prototype: parse, QA, lexical index and ChatGPT Project export.

Docling is the production backend. PyMuPDF diagnostic mode is deliberately
explicit: it does not validate formulas, diagrams, or Hebrew RTL accuracy.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

BACKEND_VERSION = "v1"
SCHEMA = """
CREATE TABLE IF NOT EXISTS parsed (
 source_id TEXT PRIMARY KEY,
 source_hash TEXT NOT NULL,
 backend TEXT NOT NULL,
 backend_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pages (
 source_id TEXT NOT NULL, page_no INTEGER NOT NULL, text TEXT NOT NULL,
 backend TEXT NOT NULL, PRIMARY KEY(source_id,page_no)
);
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
 source_id UNINDEXED, page_no UNINDEXED, text, tokenize='unicode61'
);
"""


def connect(db: Path) -> sqlite3.Connection:
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def extract_pdf(path: Path, backend: str = "docling") -> list[tuple[int, str]]:
    path = Path(path)
    if backend == "pymupdf-diagnostic":
        if path.suffix.lower() != ".pdf":
            raise ValueError("Diagnostic backend supports PDF only")
        import fitz
        with fitz.open(path) as document:
            return [(i, page.get_text(sort=True))
                    for i, page in enumerate(document, start=1)]
    if backend != "docling":
        raise ValueError(f"Unsupported backend: {backend}")
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError("Install Docling: pip install docling") from exc
    result = DocumentConverter().convert(str(path))
    document = result.document
    grouped: dict[int, list[str]] = {}
    counted: set[tuple[int, int]] = set()
    for item, _level in document.iterate_items():
        value = getattr(item, "text", None)
        if not value:
            continue
        for provenance in getattr(item, "prov", None) or []:
            number = int(provenance.page_no)
            key = (number, id(item))
            if key not in counted:
                grouped.setdefault(number, []).append(str(value))
                counted.add(key)
    total = len(document.pages)
    if total < 1:
        raise ValueError(f"Docling did not provide page count: {path}")
    return [(i, "\n".join(grouped.get(i, []))) for i in range(1, total + 1)]


def quality_report(source: Path, pages: list[tuple[int, str]]) -> dict:
    """Flags are review requests, not evidence of an incorrect answer."""
    warnings = []
    for number, body in pages:
        if not body.strip():
            warnings.append({"page": number, "kind": "empty_text"})
        elif len(body.strip()) < 100:
            warnings.append({"page": number, "kind": "low_text_density"})
        if "\ufffd" in body:
            warnings.append({"page": number, "kind": "replacement_character"})
    if source.suffix.lower() == ".pdf":
        try:
            import fitz
            with fitz.open(source) as pdf:
                if len(pdf) != len(pages):
                    warnings.append({"page": None, "kind": "page_count_mismatch",
                                     "source_pages": len(pdf), "parsed_pages": len(pages)})
        except ImportError:
            warnings.append({"page": None, "kind": "visual_inspection_unavailable"})
    return {"source": source.name, "page_count": len(pages),
            "characters": sum(len(t) for _, t in pages), "warnings": warnings}


def save_parsed(conn: sqlite3.Connection, source_id: str, source_hash: str,
                backend: str, pages: list[tuple[int, str]]) -> None:
    if not pages:
        raise ValueError("Cannot save empty parsed document")
    with conn:
        conn.execute("DELETE FROM pages WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM pages_fts WHERE source_id=?", (source_id,))
        conn.executemany("INSERT INTO pages VALUES(?,?,?,?)",
                         [(source_id, n, text, backend) for n, text in pages])
        conn.executemany("INSERT INTO pages_fts VALUES(?,?,?)",
                         [(source_id, n, text) for n, text in pages])
        conn.execute("""
          INSERT INTO parsed VALUES(?,?,?,?)
          ON CONFLICT(source_id) DO UPDATE SET
          source_hash=excluded.source_hash,
          backend=excluded.backend,
          backend_version=excluded.backend_version
        """, (source_id, source_hash, backend, BACKEND_VERSION))


def parse_registry(registry_db: Path, source_root: Path, parsed_db: Path,
                   backend: str = "docling") -> dict:
    """Run after the Phase-1 scanner. Process only new/changed sources."""
    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        raise NotADirectoryError(source_root)
    registry = sqlite3.connect(registry_db)
    registry.row_factory = sqlite3.Row
    conn = connect(parsed_db)
    reports, failures, skipped = [], [], 0
    try:
        sources = registry.execute(
            "SELECT * FROM sources WHERE status='active' ORDER BY relative_path"
        ).fetchall()
        for source in sources:
            current = conn.execute("SELECT * FROM parsed WHERE source_id=?",
                                   (source["source_id"],)).fetchone()
            if current and current["source_hash"] == source["sha256"] and (
                current["backend"], current["backend_version"]
            ) == (backend, BACKEND_VERSION):
                skipped += 1
                continue
            path = source_root / source["relative_path"]
            try:
                pages = extract_pdf(path, backend)
                report = quality_report(path, pages)
                save_parsed(conn, source["source_id"], source["sha256"], backend, pages)
                reports.append(report)
            except Exception as exc:
                failures.append({"source": source["relative_path"], "error": str(exc)})
    finally:
        conn.close()
        registry.close()
    return {"parsed": len(reports), "unchanged": skipped,
            "failed": failures, "reports": reports, "backend": backend}


def search(parsed_db: Path, query: str, limit: int = 10) -> list[dict]:
    words = [t.replace('"', '') for t in query.split() if t.replace('"', '')]
    if not words:
        return []
    expr = " OR ".join('"' + word + '"' for word in words)
    with connect(parsed_db) as conn:
        results = conn.execute("""
          SELECT source_id, page_no, text, bm25(pages_fts) AS score
          FROM pages_fts WHERE pages_fts MATCH ? ORDER BY score LIMIT ?
        """, (expr, limit)).fetchall()
        return [{"source_id": r["source_id"], "page": r["page_no"],
                 "excerpt": r["text"][:500], "score": r["score"]} for r in results]


def export_project(registry_db: Path, parsed_db: Path, destination: Path,
                   max_chars: int = 150000) -> dict:
    """Export source/page-provenance content, not a native ChatGPT index."""
    if max_chars < 1000:
        raise ValueError("max_chars must be at least 1000")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for old in destination.glob("course_sources_*.md"):
        old.unlink()
    register = sqlite3.connect(registry_db)
    register.row_factory = sqlite3.Row
    conn = connect(parsed_db)
    manifest, bundles, parts, length = [], [], [], 0

    def flush():
        nonlocal parts, length
        if not parts:
            return
        filename = f"course_sources_{len(bundles)+1:03d}.md"
        (destination / filename).write_text("\n\n".join(parts), encoding="utf-8")
        bundles.append(filename)
        parts, length = [], 0

    try:
        for source in register.execute(
            "SELECT * FROM sources WHERE status='active' ORDER BY relative_path"
        ):
            pages = conn.execute(
                "SELECT * FROM pages WHERE source_id=? ORDER BY page_no",
                (source["source_id"],)
            ).fetchall()
            if not pages:
                continue
            manifest.append({"source_id": source["source_id"],
                             "source": source["relative_path"], "pages": len(pages),
                             "sha256": source["sha256"]})
            for page in pages:
                header = (f"## {source['relative_path']} — page {page['page_no']}"
                          f" — source_id {source['source_id']}\n")
                body = page["text"].strip() or "[NO EXTRACTED TEXT: CHECK ORIGINAL PDF]"
                pieces = [body[i:i+max_chars-500] for i in range(0, len(body), max_chars-500)]
                for i, piece in enumerate(pieces):
                    note = f"\n[part {i+1}/{len(pieces)}]" if len(pieces)>1 else ""
                    section = header + note + "\n" + piece
                    if length + len(section) > max_chars:
                        flush()
                    parts.append(section)
                    length += len(section)
        flush()
    finally:
        conn.close()
        register.close()
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (destination / "INDEX.md").write_text(
        "# Source inventory (not semantic index)\n\n" +
        "\n".join(f"- {m['source']}: {m['pages']} pages" for m in manifest) +
        "\n\nKeep original PDFs for diagrams and visual verification.\n", encoding="utf-8")
    return {"sources": len(manifest), "bundles": bundles}
