import hashlib
import json
import pymupdf
import pytest
from course_pipeline.core import Page,Store
from course_pipeline.structural_reconstruction import (
    _rtl_paragraphs,_aligned_tables,_gantt_candidates,_consistency,_tokens,
    reconstruct_report,
)

def test_rtl_preserves_logical_words_and_flags_mixed_text():
    t=[
        {"text":"עולם","x":10,"y":10,"box":[5,5,15,15],"block":1,"line":0,"index":1},
        {"text":"שלום","x":40,"y":10,"box":[35,5,45,15],"block":1,"line":0,"index":0},
        {"text":"CPU","x":60,"y":10,"box":[55,5,65,15],"block":1,"line":0,"index":2},
    ]
    result=_rtl_paragraphs(t)
    assert result[0]["text_candidate"]=="CPU שלום עולם"
    assert result[0]["contains_latin"]
    assert result[0]["status"]=="geometry_only_not_verified"

def test_borderless_table_column_alignment_and_no_head_false_positive():
    def cell(t,x,y):
        return {"text":t,"x":x,"y":y,"box":[x-3,y-3,x+3,y+3],"block":0,"line":int(y),"index":0}
    tokens=[cell("תהליך",120,20),cell("p1",120,50),cell("24",35,50),
            cell("p2",120,70),cell("3",35,70),
            cell("p3",120,90),cell("3",35,90)]
    result=_aligned_tables(tokens)
    assert len(result)==1
    assert len(result[0]["rows"])==3
    assert result[0]["column_semantics"]==[None]
    assert _aligned_tables([x for x in tokens if x["text"]!="תהליך"])==[]

def test_gantt_requires_monotonic_ticks_and_nearby_process_labels():
    def tok(t,x,y,i=0):
        return {"text":t,"x":x,"y":y,"box":[x-2,y-3,x+2,y+3],
                "block":0,"line":int(y),"index":i}
    ticks=[tok("0",10,120),tok("4",80,120),tok("8",150,120),tok("12",220,120)]
    labels=[tok("p1",45,100),tok("p2",110,100),tok("p3",185,100)]
    r=_gantt_candidates(ticks+labels)
    assert len(r)==1
    assert len(r[0]["segments"])==3
    assert r[0]["segments"][0]["start"]==0
    assert r[0]["segments"][0]["end"]==4
    assert all(s["status"].endswith("not_verified") for s in r[0]["segments"])
    bad=[tok("0",10,120),tok("8",80,120),tok("4",150,120)]
    assert _gantt_candidates(bad+labels)==[]
    checks=_consistency([],r)
    assert checks and all(x["passed"] is True for x in checks)

def _fixture(tmp_path):
    root=tmp_path/"pdf";root.mkdir()
    pdf=root/"lecture.pdf"
    d=pymupdf.open()
    p=d.new_page(width=400,height=320)
    p.insert_text((200,50),"p1 p2")
    p.insert_text((20,100),"0 4 8 12")
    d.save(pdf);d.close()
    store=Store(tmp_path/"test.db")
    store.scan(root)
    src=store.sources()[0]
    store.save_pages(src["source_id"],[Page(1,"original content",[],
           ["missing_numeric_evidence_review"],"hybrid")],"hybrid",src["sha256"])
    report={"schema_version":"0.11.0","pages":[{
        "source":"lecture.pdf","source_id":src["source_id"],
        "source_sha256":src["sha256"],"page":1,
        "extraction_sha256":hashlib.sha256(b"original content").hexdigest()
    }]}
    old=tmp_path/"prior.json";old.write_text(json.dumps(report),encoding="utf8")
    return root,pdf,store,old

def test_reconstruct_reads_only_and_writes_separate_outputs(tmp_path):
    root,pdf,store,old=_fixture(tmp_path)
    before=pdf.read_bytes()
    try:
        r=reconstruct_report(store,root,old,tmp_path/"out")
        assert r["page_count"]==1
        assert r["sources_modified"] is False
        out=json.loads((tmp_path/"out"/"STRUCTURAL_RECONSTRUCTION.json").read_text())
        assert out["status"]=="unverified_structural_candidates"
        assert store.sources()[0]["last_backend"]=="hybrid"
        assert store.pages(store.sources()[0]["source_id"])[0]["body"]=="original content"
        assert pdf.read_bytes()==before
    finally:store.conn.close()

def test_reconstruct_rejects_changed_source_and_extraction(tmp_path):
    root,pdf,store,old=_fixture(tmp_path)
    try:
        report=json.loads(old.read_text());report["pages"][0]["extraction_sha256"]="0"*64
        old.write_text(json.dumps(report))
        with pytest.raises(ValueError,match="extraction changed"):
            reconstruct_report(store,root,old,tmp_path/"out")
        report["pages"][0]["extraction_sha256"]=hashlib.sha256(b"original content").hexdigest()
        old.write_text(json.dumps(report))
        pdf.write_bytes(b"modified PDF")
        with pytest.raises(ValueError,match="Original PDF SHA mismatch"):
            reconstruct_report(store,root,old,tmp_path/"out")
    finally:store.conn.close()
