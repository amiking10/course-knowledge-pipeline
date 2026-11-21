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


def test_progress_heartbeat_reports_elapsed_without_fake_page_percentage(monkeypatch):
    import io
    import threading
    from course_pipeline.progress_display import parsing_heartbeat

    class InteractiveStream(io.StringIO):
        def isatty(self):
            return True

    output = InteractiveStream()
    with parsing_heartbeat("slow_lecture.pdf", stream=output, interval=0.005):
        assert threading.current_thread().is_alive()
        import time
        time.sleep(0.025)
    text = output.getvalue()
    assert "slow_lecture.pdf" in text
    assert "elapsed" in text
    assert "page progress unavailable" in text
    assert "100%" not in text


def test_progress_heartbeat_stops_on_exception():
    import io
    import pytest
    from course_pipeline.progress_display import parsing_heartbeat

    with pytest.raises(RuntimeError):
        with parsing_heartbeat("bad.pdf", stream=io.StringIO(), interval=0.001):
            raise RuntimeError("failure")


def test_brief_cli_writes_detailed_stage_report(tmp_path,capsys):
    from course_pipeline.cli import main
    root=tmp_path/'RX_TX'
    root.mkdir()
    (root/'lecture.pdf').write_bytes(b'demo')
    db=tmp_path/'db.sqlite3'
    detail=tmp_path/'INTERNAL'/'scan.json'
    outcome=main(['--db',str(db),'--brief','--report-file',str(detail),'scan',str(root)])
    terminal=capsys.readouterr().out
    assert 'scan:' in terminal
    assert '"added": 1' in terminal
    assert '"added": 1' in detail.read_text(encoding='utf-8')
    assert outcome['added']==1


def test_runner_generates_private_audit_and_stage_logs():
    from pathlib import Path
    script=Path(__file__).resolve().parents[1].joinpath('scripts','run_pipeline.ps1').read_text(encoding='utf-8')
    assert "'--brief'" in script
    assert "'--report-file'" in script
    assert "'stage_reports'" in script
    assert "'review-gold-sample'" in script
    assert "'content_audit'" in script
    assert "'project-instructions'" in script
    assert "'PROJECT_INSTRUCTIONS.md'" in script
