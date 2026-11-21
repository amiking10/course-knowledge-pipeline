"""AI-assisted recovery is opt-in, source-bound, and never overwrites parser output."""
import hashlib
import json
import pytest
import pymupdf

from course_pipeline.ai_recovery import (
    recover_pages, validate_answer, select_pages, write_study_markdown,
)
from course_pipeline.core import Page, Store


def setup(tmp_path):
    root=tmp_path/"RX_TX"
    root.mkdir()
    pdf=root/"friis.pdf"
    doc=pymupdf.open()
    for i in range(3):
        doc.new_page().insert_text((40,75),"Cascaded noise factor Friis equation")
    doc.save(pdf)
    doc.close()
    store=Store(tmp_path/"course.sqlite3")
    store.scan(root)
    source=store.sources()[0]
    store.save_pages(source["source_id"],[
        Page(1,"[FORMULA DETECTED — no content]",[],["formula_structure_review_required"],"hybrid"),
        Page(2,"[FORMULA DETECTED — no content]",[],["missing_numeric_evidence_review"],"hybrid"),
        Page(3,"Normal narrative",[],[],"hybrid"),
    ],"hybrid",source["sha256"])
    return root,pdf,store


def proposal(*args):
    assert args[0].startswith(b"\x89PNG")
    return {"candidates":[{
        "kind":"equation",
        "content":r"F_T=F_1+\\frac{F_2-1}{G_1}",
        "status":"externally_inferred",
        "visible_evidence":"Slide mentions cascaded noise figure",
        "external_knowledge":"Standard Friis equation from communications theory",
        "uncertainty":"Exact stage symbols are not legible",
    }]}


def test_ai_recovery_is_off_by_default_and_does_not_mutate_sources(tmp_path):
    root,pdf,store=setup(tmp_path)
    original=hashlib.sha256(pdf.read_bytes()).hexdigest()
    try:
        result=recover_pages(store,root,tmp_path/"ai",limit=2,reviewer=lambda *a:pytest.fail("network"))
        assert result["actual_api_attempts"]==0
        assert result["candidates"]==0
        assert len(select_pages(store,19))==2
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==original
        assert "No AI recovery candidates" in (tmp_path/"ai"/"AI_RECOVERY.md").read_text()
    finally:
        store.conn.close()


def test_ai_recovery_caching_and_explicit_external_knowledge(tmp_path):
    root,pdf,store=setup(tmp_path)
    try:
        original=store.pages(store.sources()[0]["source_id"])[0]["body"]
        out=tmp_path/"ai"
        result=recover_pages(store,root,out,limit=2,max_requests=1,live=True,reviewer=proposal)
        assert result["actual_api_attempts"]==1
        assert result["candidates"]==1
        report=json.loads((out/"AI_RECOVERY.json").read_text(encoding="utf-8"))
        assert report["pages"][0]["page"]==2  # missing numeric evidence first
        assert report["pages"][1]["status"]=="skipped_request_cap"
        assert report["pages"][0]["result"]["candidates"][0]["status"]=="externally_inferred"
        text=(out/"AI_RECOVERY.md").read_text(encoding="utf-8")
        assert "Friis equation" in text
        assert "externally_inferred" in text
        assert "NOT verified source transcription" in text
        assert "Source SHA-256" in text
        assert store.pages(store.sources()[0]["source_id"])[0]["body"]==original
        again=recover_pages(store,root,out,limit=2,max_requests=1,live=True,reviewer=proposal)
        assert again["cache_hits"]==1
        assert again["actual_api_attempts"]==1
    finally:
        store.conn.close()


def test_stale_pdf_is_rejected(tmp_path):
    root,pdf,store=setup(tmp_path)
    try:
        pdf.write_bytes(b"changed")
        with pytest.raises(ValueError, match="changed since parsing"):
            recover_pages(store,root,tmp_path/"ai")
    finally:
        store.conn.close()


def test_validation_prevents_unattributed_external_inference():
    with pytest.raises(ValueError,match="external knowledge"):
        validate_answer({"candidates":[{
            "kind":"equation","content":"x=1","status":"externally_inferred",
            "visible_evidence":"","external_knowledge":"","uncertainty":"unknown"
        }]})
    with pytest.raises(ValueError,match="image evidence"):
        validate_answer({"candidates":[{
            "kind":"equation","content":"x=1","status":"visually_supported",
            "visible_evidence":"","external_knowledge":"","uncertainty":""
        }]})


def test_live_without_key_is_fail_closed(tmp_path,monkeypatch):
    root,_,store=setup(tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    try:
        with pytest.raises(RuntimeError,match="GEMINI_API_KEY"):
            recover_pages(store,root,tmp_path/"ai",live=True)
    finally:
        store.conn.close()
