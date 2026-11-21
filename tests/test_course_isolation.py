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

def test_strict_gate_rejects_foreign_course_index(tmp_path):
    root = tmp_path / "RX_TX"
    db = tmp_path / "rx.sqlite3"
    _add_course(root, db, "modulation carrier receiver")
    export = tmp_path / "UPLOAD_TO_CHATGPT"
    internal = tmp_path / "INTERNAL"
    with Store(db) as store:
        export_project(store, export)
        make_index(store, internal)
        build_knowledge(store, internal)
        for name in ("COURSE_INDEX.md", "COURSE_KNOWLEDGE.md"):
            (export / name).write_bytes((internal / name).read_bytes())
        from course_pipeline.release_validation import verify_export
        assert verify_export(store, export, source_dir=root,
                             strict_indexes=True)["passed"]
        (export / "COURSE_INDEX.md").write_text("# פסיקות זימונים איתותים", encoding="utf-8")
        result = verify_export(store, export, source_dir=root, strict_indexes=True)
        assert not result["passed"]
        assert any("foreign-course index" in error for error in result["errors"])


def test_topic_phrases_are_course_evidence_not_hardcoded(tmp_path):
    root=tmp_path/'Communications'
    root.mkdir()
    (root/'lecture.pdf').write_bytes(b'lecture')
    from course_pipeline.topic_index import discover_course_terms
    with Store(tmp_path/'communications.sqlite') as store:
        store.scan(root)
        src=store.sources()[0]
        store.save_pages(src['source_id'],[
            Page(1,'Quadrature amplitude modulation uses a constellation diagram.',[],[],'hybrid'),
            Page(2,'Quadrature amplitude modulation demodulator and carrier recovery.',[],[],'hybrid'),
            Page(3,'The constellation diagram illustrates quadrature amplitude modulation.',[],[],'hybrid'),
            Page(4,'Carrier recovery for digital communications.',[],[],'hybrid'),
        ],'hybrid',src['sha256'])
        terms=discover_course_terms(store)
        assert 'quadrature amplitude modulation' in terms
        assert 'constellation diagram' in terms
        assert 'פסיקות' not in terms
        make_index(store,tmp_path/'index')
        assert 'quadrature amplitude modulation' in (tmp_path/'index'/'COURSE_INDEX.md').read_text()
