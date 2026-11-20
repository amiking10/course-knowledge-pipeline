import hashlib
from pathlib import Path

import pytest

from course_pipeline.ingestion import scan_sources, sha256_file
from course_pipeline.models import SourceStatus
from course_pipeline.registry import SourceRegistry


def test_sha256_is_content_based(tmp_path: Path):
    p = tmp_path / "sample.pdf"
    p.write_bytes(b"abc")
    assert sha256_file(p) == hashlib.sha256(b"abc").hexdigest()


def test_initial_scan_and_idempotency(tmp_path: Path):
    root = tmp_path / "lectures"
    root.mkdir()
    (root / "L01.PDF").write_bytes(b"lecture")
    (root / "notes.txt").write_text("unsupported")
    with SourceRegistry(tmp_path / "registry.sqlite3") as registry:
        first = scan_sources(root, registry)
        assert (first.discovered, first.added, first.unsupported) == (1, 1, 1)
        source_id = registry.get("L01.PDF").source_id
        second = scan_sources(root, registry)
        assert (second.added, second.changed, second.unchanged) == (0, 0, 1)
        assert registry.get("L01.PDF").source_id == source_id


def test_changed_file_keeps_identity(tmp_path: Path):
    root = tmp_path / "sources"
    root.mkdir()
    p = root / "Lecture 1.pptx"
    p.write_bytes(b"before")
    with SourceRegistry(tmp_path / "registry.sqlite3") as registry:
        scan_sources(root, registry)
        original = registry.get(p.name)
        p.write_bytes(b"after")
        report = scan_sources(root, registry)
        assert report.changed == 1
        updated = registry.get(p.name)
        assert updated.source_id == original.source_id
        assert updated.sha256 != original.sha256


def test_missing_and_restored_source(tmp_path: Path):
    root = tmp_path / "sources"
    root.mkdir()
    p = root / "lecture.docx"
    p.write_bytes(b"content")
    with SourceRegistry(tmp_path / "registry.sqlite3") as registry:
        scan_sources(root, registry)
        source_id = registry.get(p.name).source_id
        p.unlink()
        missing = scan_sources(root, registry)
        assert missing.missing == 1
        assert registry.get(p.name).status is SourceStatus.MISSING
        p.write_bytes(b"content")
        restored = scan_sources(root, registry)
        assert restored.changed == 1
        assert registry.get(p.name).status is SourceStatus.ACTIVE
        assert registry.get(p.name).source_id == source_id


def test_nested_sources_and_unreadable_root(tmp_path: Path):
    root = tmp_path / "sources"
    (root / "week 1").mkdir(parents=True)
    (root / "week 1" / "slides.pdf").write_bytes(b"pdf")
    (root / ".cache").mkdir()
    (root / ".cache" / "ignored.pdf").write_bytes(b"ignore")
    with SourceRegistry(tmp_path / "registry.sqlite3") as registry:
        assert scan_sources(root, registry).discovered == 1
        assert registry.get("week 1/slides.pdf") is not None
        with pytest.raises(NotADirectoryError):
            scan_sources(root / "absent", registry)
        assert registry.get("week 1/slides.pdf").status is SourceStatus.ACTIVE
