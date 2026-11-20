"""Course separation regression: OS and RX_TX must never share content or headings."""
import json

import pytest

from course_pipeline.core import Page, Store
from course_pipeline.topic_index import make_index
from course_pipeline.knowledge import build_knowledge
from course_pipeline.exporter import export_project


def _add_course(root, db_path, content):
    root.mkdir()
    (root / "lecture.pdf").write_bytes(content.encode("utf-8"))
    with Store(db_path) as store:
        store.scan(root)
        source = store.sources()[0]
        store.save_pages(source["source_id"], [Page(1, content, [], [], "hybrid")],
                         "hybrid", source["sha256"])


def test_course_indexes_are_source_derived_and_separate(tmp_path):
    os_root = tmp_path / "OS"
    rx_root = tmp_path / "RX_TX"
    os_db = tmp_path / "courses" / "OS" / "INTERNAL" / "course.sqlite3"
    rx_db = tmp_path / "courses" / "RX_TX" / "INTERNAL" / "course.sqlite3"
    _add_course(os_root, os_db, "פסיקות זימונים איתותים kernel scheduling")
    _add_course(rx_root, rx_db, "modulation carrier frequency demodulation receiver")

    for root, db, present, absent in [
        (os_root, os_db, "פסיקות", "modulation"),
        (rx_root, rx_db, "modulation", "פסיקות"),
    ]:
        dest = tmp_path / "export" / root.name
        with Store(db) as store:
            make_index(store, dest)
            build_knowledge(store, dest)
            export_project(store, dest)
        index = (dest / "COURSE_INDEX.md").read_text(encoding="utf-8")
        knowledge = (dest / "COURSE_KNOWLEDGE.md").read_text(encoding="utf-8")
        bundle = (dest / "course_sources_001.md").read_text(encoding="utf-8")
        assert present in index and present in knowledge and present in bundle
        assert absent not in index and absent not in knowledge and absent not in bundle
        data = json.loads((dest / "COURSE_INDEX.json").read_text(encoding="utf-8"))
        assert all(data.values())


def test_reusing_another_courses_database_is_rejected(tmp_path):
    os_root = tmp_path / "OS"
    rx_root = tmp_path / "RX_TX"
    db = tmp_path / "shared.sqlite3"
    _add_course(os_root, db, "kernel interrupts")
    rx_root.mkdir()
    (rx_root / "lecture.pdf").write_bytes(b"carrier modulation")
    with Store(db) as store:
        with pytest.raises(ValueError, match="belongs to"):
            store.scan(rx_root)


def test_legacy_unbound_database_with_unrelated_files_is_rejected(tmp_path):
    root = tmp_path / "OS"
    db = tmp_path / "legacy.sqlite3"
    _add_course(root, db, "process scheduling")
    with Store(db) as store:
        store.conn.execute("DELETE FROM course_metadata")
        store.conn.commit()
    other = tmp_path / "RX_TX"
    other.mkdir()
    (other / "lecture.pdf").write_bytes(b"carrier modulation")
    with Store(db) as store:
        with pytest.raises(ValueError, match="another course"):
            store.scan(other)
