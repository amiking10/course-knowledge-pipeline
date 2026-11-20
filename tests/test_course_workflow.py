"""Progress output and incremental parsing behavior for course updates."""
import json
from course_pipeline.cli import main
from course_pipeline.core import Page, Store
import pymupdf


def test_cli_progress_reports_completed_files_and_reuses_unchanged(tmp_path, monkeypatch, capsys):
    source=tmp_path/"RX_TX"
    source.mkdir()
    for name in ("lecture1.pdf", "lecture2.pdf"):
        doc=pymupdf.open()
        doc.new_page().insert_text((50,80),name)
        doc.save(source/name)
        doc.close()
    db=tmp_path/"course.sqlite3"
    calls=[]

    def fake_parse(path, backend):
        calls.append(path.name)
        return [Page(1, path.name+" content", [], [], backend)]

    monkeypatch.setattr("course_pipeline.cli.parse", fake_parse)
    main(["--db", str(db), "parse", str(source), "--backend", "hybrid", "--progress"])
    output=capsys.readouterr()
    assert "50%" in output.err
    assert "100%" in output.err
    assert "2 document(s)" in output.err
    assert len(calls)==2
    main(["--db", str(db), "parse", str(source), "--backend", "hybrid", "--progress"])
    output=capsys.readouterr()
    assert "No new or modified documents" in output.err
    assert len(calls)==2
    doc=pymupdf.open()
    doc.new_page().insert_text((50,80),"lecture3")
    doc.save(source/"lecture3.pdf")
    doc.close()
    main(["--db", str(db), "parse", str(source), "--backend", "hybrid", "--progress"])
    output=capsys.readouterr()
    assert "1 document(s)" in output.err
    assert calls[-1]=="lecture3.pdf"
    assert len(calls)==3


def test_progress_reports_failures_not_false_success(tmp_path, monkeypatch, capsys):
    source=tmp_path/"sources"
    source.mkdir()
    (source/"invalid.pdf").write_bytes(b"x")
    def fail(path, backend):
        raise RuntimeError("intentionally unavailable")
    monkeypatch.setattr("course_pipeline.cli.parse",fail)
    import pytest
    with pytest.raises(SystemExit) as exc:
        main(["--db",str(tmp_path/"course.sqlite3"),"parse",str(source),
              "--backend","hybrid","--progress"])
    assert exc.value.code==2
    displayed=capsys.readouterr()
    assert "processed" in displayed.err
    assert "intentionally unavailable" in displayed.out


def test_default_course_workflow_has_one_output_root():
    from pathlib import Path
    text=Path(__file__).resolve().parents[1].joinpath("scripts","run_pipeline.ps1").read_text(encoding="utf-8")
    assert "[string]$OutputRoot = 'data/courses'" in text
    assert "$courseRoot = Join-Path $OutputRoot $safeName" in text
    assert "$uploadDir = Join-Path $courseRoot 'UPLOAD_TO_CHATGPT'" in text
    assert "$internalDir = Join-Path $courseRoot 'INTERNAL'" in text
    assert "Join-Path $internalDir 'course.sqlite3'" in text
    assert "'export',$uploadDir" in text
    assert "'quality-report',$internalDir" in text
    assert "Join-Path $internalDir 'review'" in text
    assert "'--quality-report'" in text
    assert "Join-Path $internalDir 'COURSE_WORKFLOW.md'" in text
    assert "'--progress'" in text
    assert "'--source-dir'" in text
