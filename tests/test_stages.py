"""Cross-phase acceptance tests using synthetic PDFs and temporary databases."""
from pathlib import Path
import pytest
from course_pipeline.stages import (
    connect, extract_pdf, quality_report, save_parsed, search, export_project
)
from course_pipeline.ingestion import scan_sources
from course_pipeline.registry import SourceRegistry


def test_parser_qa_and_index(tmp_path: Path):
    import fitz
    pdf = tmp_path / "sample.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((70, 70), "interrupt descriptor table")
    doc.save(pdf)
    doc.close()
    pages = extract_pdf(pdf, "pymupdf-diagnostic")
    assert len(pages) == 1
    assert "interrupt" in pages[0][1]
    assert quality_report(pdf, pages)["warnings"] is not None
    db = tmp_path / "parsed.sqlite"
    with connect(db) as conn:
        save_parsed(conn, "stable-id", "hash", "pymupdf-diagnostic", pages)
        assert len(search(db, "interrupt")) == 1
        with pytest.raises(ValueError):
            save_parsed(conn, "stable-id", "hash", "pymupdf-diagnostic", [])
        assert len(search(db, "interrupt")) == 1


def test_export_and_stale_bundle_cleanup(tmp_path: Path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "lecture.pdf").write_bytes(b"pdf header only; parser is bypassed")
    registry_db = tmp_path / "registry.sqlite3"
    with SourceRegistry(registry_db) as registry:
        scan_sources(root, registry)
        row = registry.get("lecture.pdf")
    parsed_db = tmp_path / "parsed.sqlite3"
    with connect(parsed_db) as conn:
        save_parsed(conn, row.source_id, row.sha256, "docling",
                    [(1, "sample kernel text")])
    out = tmp_path / "exports"
    out.mkdir()
    (out / "course_sources_999.md").write_text("obsolete")
    assert export_project(registry_db, parsed_db, out)["sources"] == 1
    assert not (out / "course_sources_999.md").exists()
    assert "kernel text" in (out / "course_sources_001.md").read_text()
