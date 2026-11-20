"""Release gate exercises real source registration, page export and archive mapping."""
import json
import pytest
import pymupdf

from course_pipeline.core import Page, Store
from course_pipeline.exporter import export_project
from course_pipeline.pdf_bundle import export_pdf_bundle
from course_pipeline.quality_report import write_report
from course_pipeline.release_validation import verify_export
from course_pipeline.cli import main


def package(tmp_path):
    source=tmp_path/"sources"; source.mkdir()
    pdf=source/"Lecture.pdf"
    doc=pymupdf.open()
    doc.new_page().insert_text((50,80),"scheduling example")
    doc.new_page().insert_text((50,80),"round robin")
    doc.save(pdf); doc.close()
    store=Store(tmp_path/"course.db")
    store.scan(source)
    row=store.sources()[0]
    store.save_pages(row["source_id"],[
        Page(1,"scheduling example",[],[],"hybrid"),
        Page(2,"round robin",[],[],"hybrid")],"hybrid",row["sha256"])
    dest=tmp_path/"export"
    export_project(store,dest)
    export_pdf_bundle(store,source,dest/"course_original_visuals.pdf")
    write_report(store,dest)
    return source,store,dest


def test_valid_complete_project_passes_integrity_gate(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        report=verify_export(store,dest,require_visuals=True)
        assert report["passed"],report["errors"]
        assert report["sources"]==1
        assert report["bundles"]==1
        assert report["visual_pdf_present"]
        assert report["status"]=="package_integrity_only_not_content_accuracy"
    finally:store.conn.close()


def test_missing_visual_pdf_fails_when_required(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        (dest/"course_original_visuals.pdf").unlink()
        result=verify_export(store,dest,require_visuals=True)
        assert not result["passed"]
        assert any("visual pdf" in x.lower() for x in result["errors"])
    finally:store.conn.close()


def test_stale_source_manifest_fails_even_with_old_export(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        (src/"Lecture.pdf").write_bytes(b"changed bytes")
        store.scan(src)
        result=verify_export(store,dest)
        assert not result["passed"]
        assert result["errors"]
    finally:store.conn.close()


def test_partial_page_bundle_fails(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        name=dest/"course_sources_001.md"
        name.write_text("## Source: Lecture.pdf | page 1 | id INVALID",encoding="utf-8")
        result=verify_export(store,dest)
        assert not result["passed"]
        assert any("Missing exported source/page" in e for e in result["errors"])
    finally:store.conn.close()


def test_tampered_visual_page_map_fails(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        path=dest/"course_original_visuals.manifest.json"
        mapping=json.loads(path.read_text(encoding="utf-8"))
        mapping["total_pages"]=999
        path.write_text(json.dumps(mapping),encoding="utf-8")
        result=verify_export(store,dest,require_visuals=True)
        assert not result["passed"]
        assert any("page count" in e for e in result["errors"])
    finally:store.conn.close()


def test_bad_manifest_returns_structured_error(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        (dest/"manifest.json").write_text("{invalid")
        result=verify_export(store,dest)
        assert not result["passed"]
        assert "Invalid manifest" in result["errors"][0]
    finally:store.conn.close()


def test_cli_has_nonzero_exit_on_invalid_package(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["--db",str(tmp_path/"empty.db"),
              "verify-export",str(tmp_path/"missing"),
              "--require-visuals"])
    assert exc.value.code==3


def test_source_bytes_changed_without_rescan_are_rejected(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        (src/"Lecture.pdf").write_bytes(b"changed after scan")
        result=verify_export(store,dest,require_visuals=True,source_dir=src)
        assert not result["passed"]
        assert any("changed since scan" in error for error in result["errors"])
    finally:
        store.conn.close()


def test_qa_report_from_old_export_is_rejected(tmp_path):
    src,store,dest=package(tmp_path)
    try:
        qa=dest/"QUALITY_REPORT.json"
        report=json.loads(qa.read_text(encoding="utf-8"))
        report["total_pages"]=999
        qa.write_text(json.dumps(report),encoding="utf-8")
        result=verify_export(store,dest,source_dir=src)
        assert not result["passed"]
        assert any("QUALITY_REPORT page count" in error for error in result["errors"])
    finally:
        store.conn.close()


def test_private_quality_report_can_be_verified_outside_upload_folder(tmp_path):
    src,store,upload=package(tmp_path)
    try:
        internal=tmp_path/"INTERNAL"
        internal.mkdir()
        qa=upload/"QUALITY_REPORT.json"
        private_qa=internal/qa.name
        qa.replace(private_qa)
        assert not qa.exists()
        result=verify_export(store,upload,require_visuals=True,
                             source_dir=src,quality_report_path=private_qa)
        assert result["passed"], result["errors"]
        assert not any("QUALITY_REPORT.json absent" in warning
                       for warning in result["warnings"])
    finally:
        store.conn.close()


def test_upload_folder_blocks_accidental_private_database(tmp_path):
    src,store,export=package(tmp_path)
    try:
        upload=export.parent/"UPLOAD_TO_CHATGPT"
        export.rename(upload)
        (upload/"COURSE_INDEX.md").write_text("# index",encoding="utf-8")
        (upload/"COURSE_KNOWLEDGE.md").write_text("# knowledge",encoding="utf-8")
        private=upload/"course.sqlite3"
        private.write_bytes(b"do not upload")
        report=verify_export(store,upload,require_visuals=True,source_dir=src)
        assert not report["passed"]
        assert any("course.sqlite3" in error for error in report["errors"])
        private.unlink()
        result=verify_export(store,upload,require_visuals=True,source_dir=src)
        assert result["passed"],result["errors"]
    finally:
        store.conn.close()
