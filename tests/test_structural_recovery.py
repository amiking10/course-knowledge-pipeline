import hashlib
import json

import pymupdf
import pytest

from course_pipeline.core import Page, Store
from course_pipeline.structural_recovery import (
    _geometry, _timeline_candidates, _issue_summary,
    build_structural_recovery,
)


def make_case(tmp_path):
    root=tmp_path/"sources";root.mkdir()
    pdf=root/"scheduling.pdf"
    doc=pymupdf.open()
    page=doc.new_page(width=600,height=800)
    page.insert_text((480,50),"CPU p1 p2",fontsize=11)
    page.insert_text((100,200),"p1 p2 p3",fontsize=12)
    page.insert_text((100,220),"0 4 8 12",fontsize=12)
    page.insert_text((440,100),"שלום עולם",fontsize=14,fontfile=None)
    doc.save(pdf);doc.close()
    db=tmp_path/"course.sqlite3"
    store=Store(db)
    store.scan(root)
    source=store.sources()[0]
    original="CPU p1 p2 \n 0 4 8 12"
    store.save_pages(source["source_id"],[
        Page(1,original,[],["missing_numeric_evidence_review"],"hybrid")
    ],"hybrid",source["sha256"])
    audit={
        "schema_version":"1.0",
        "pages":[{
            "source":source["relative_path"],"page":1,
            "source_sha256":source["sha256"],"status":"audited",
            "result":{"issues":[{"category":"figure",
                        "visible_evidence":"<script>tick labels</script>",
                        "extraction_evidence":"no coordinates","confidence":"high"}]}
        }]
    }
    a=tmp_path/"audit.json"
    a.write_text(json.dumps(audit,ensure_ascii=False),encoding="utf-8")
    return root,pdf,store,source,original,a


def test_seven_page_structural_sidecar_preserves_sources_and_db(tmp_path):
    root,pdf,store,source,original,audit=make_case(tmp_path)
    pdfhash=hashlib.sha256(pdf.read_bytes()).hexdigest()
    try:
        output=tmp_path/"results"
        outcome=build_structural_recovery(store,root,output,
                                          audit_report_path=audit,limit=7)
        assert outcome["selected_pages"]==1
        assert outcome["source_mutated"] is False
        assert outcome["total_ai_hypotheses"]==1
        report=json.loads((output/"STRUCTURAL_RECOVERY.json").read_text(encoding="utf-8"))
        record=report["pages"][0]
        assert record["original_extracted_text"]==original
        assert record["extraction_sha256"]==hashlib.sha256(original.encode()).hexdigest()
        assert record["gemini_issue_hypotheses"][0]["verification"]=="ai_hypothesis_not_ground_truth"
        assert record["status"].startswith("structural_evidence_unverified")
        assert record["proposals"]["timeline_candidates"]
        assert all(not c["intervals"] for c in record["proposals"]["timeline_candidates"])
        assert store.pages(source["source_id"])[0]["body"]==original
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==pdfhash
        html=(output/"STRUCTURAL_RECOVERY.html").read_text(encoding="utf-8")
        assert "&lt;script&gt;" in html
        assert "<script>tick labels</script>" not in html
    finally:store.conn.close()


def test_stale_pdf_rejected_and_no_output(tmp_path):
    root,pdf,store,*_=make_case(tmp_path)
    try:
        pdf.write_bytes(b"corrupted")
        with pytest.raises(ValueError,match="SHA changed"):
            build_structural_recovery(store,root,tmp_path/"output")
        assert not (tmp_path/"output"/"STRUCTURAL_RECOVERY.json").exists()
    finally:store.conn.close()


def test_mismatched_ai_report_rejected(tmp_path):
    root,pdf,store,source,original,a=make_case(tmp_path)
    audit=json.loads(a.read_text(encoding="utf-8"))
    audit["pages"][0]["source_sha256"]="0"*64
    a.write_text(json.dumps(audit),encoding="utf-8")
    try:
        with pytest.raises(ValueError,match="different source PDF SHA"):
            build_structural_recovery(store,root,tmp_path/"out",audit_report_path=a)
    finally:store.conn.close()


def test_audit_failed_status_not_trusted(tmp_path):
    root,pdf,store,source,original,a=make_case(tmp_path)
    audit=json.loads(a.read_text(encoding="utf-8"))
    audit["pages"][0]["status"]="error"
    a.write_text(json.dumps(audit),encoding="utf-8")
    try:
        result=build_structural_recovery(store,root,tmp_path/"out",audit_report_path=a)
        assert result["total_ai_hypotheses"]==0
    finally:store.conn.close()


def test_rtl_geometry_presents_both_orderings_not_auto_replacement():
    doc=pymupdf.open()
    page=doc.new_page()
    page.insert_text((30,50),"one two",fontsize=11)
    lines=_geometry(page)
    assert lines[0]["visual_ltr_candidate"]=="one two"
    assert lines[0]["visual_rtl_candidate"]=="two one"
    assert lines[0]["direction_candidate"]=="ltr"
    assert lines[0]["status"]=="unverified_candidate"
    doc.close()


def test_timeline_requires_label_and_monotonic_timestamps():
    def line(name,y,tokens):
        return {"id":name,"bbox":[10,y,300,y+10],
                "tokens":[{"text":text,"bbox":[x,y,x+10,y+10]} for x,text in tokens]}
    time=line("tick",100,[(20,"0"),(60,"4"),(100,"8")])
    label=line("label",120,[(20,"p1"),(70,"p2")])
    found=_timeline_candidates([time,label])
    assert len(found)==1
    assert found[0]["interval_assignment_status"]=="not_inferred"
    assert found[0]["intervals"]==[]
    assert _timeline_candidates([time])==[]
    backwards=line("non-monotonic",100,[(20,"4"),(60,"0"),(100,"8")])
    assert _timeline_candidates([backwards,label])==[]
