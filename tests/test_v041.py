import json
from course_pipeline.comparison import compare, tokens
from course_pipeline.core import Page, Store
from course_pipeline.hybrid import reconcile
from course_pipeline.quality_report import write_report
from course_pipeline.visual_queue import build_queue

def test_hebrew_and_bidi_normalization():
    assert tokens('\u200fתהליכים\u200e ו־פסיקות') == tokens('תהליכים ו־פסיקות')

def test_same_tokens_different_order_do_not_claim_omission():
    primary='kernel process scheduler timer interrupt signal handler '
    secondary='handler signal interrupt timer scheduler process kernel '
    c=compare(primary,secondary)
    assert c.order_only and not c.probable_omission
    pages=reconcile([Page(1,primary,[],[],'docling')],[Page(1,secondary,[],[],'native')])
    assert 'secondary_native_text_disagrees_review' not in pages[0].flags
    assert 'word_order_difference_informational' in pages[0].flags

def test_lost_number_and_concepts_detected_even_when_lengths_similar():
    p='scheduler runs process and executes tasks, processes have states and switch context often '
    s='scheduler runs process and executes tasks; Q=4 p1=24 p2=3 p3=3 turnaround=30 context switch '
    c=compare(p,s)
    assert c.probable_omission and '24' in c.new_numeric_tokens
    page=reconcile([Page(1,p,[],[],'docling')],[Page(1,s,[],[],'native')])[0]
    assert 'missing_numeric_evidence_review' in page.flags
    assert p.strip() in page.body and s.strip() in page.body

def test_ambiguous_difference_still_preserves_primary():
    p='processor handles signals in different situations and programs'
    s='processor handles processes in different situations and programs'
    result=reconcile([Page(1,p,[],[],'docling')],[Page(1,s,[],[],'native')])[0]
    assert p in result.body

def test_priority_report_and_queue(tmp_path):
    root=tmp_path/'src'; root.mkdir(); (root/'lec.pdf').write_bytes(b'placeholder')
    with Store(tmp_path/'db.sqlite3') as store:
        store.scan(root)
        row=store.sources()[0]
        store.save_pages(row['source_id'],[
            Page(1,'Q=4',[],['missing_numeric_evidence_review'],'hybrid'),
            Page(2,'',[],['low_text_density'],'hybrid'),
            Page(3,'uncertain',[],['extractor_disagreement_ambiguous'],'hybrid')],
            'hybrid',row['sha256'])
        report=write_report(store,tmp_path/'out')
        assert report['by_severity']['critical']==1
        assert report['by_severity']['minor']==1
        assert report['by_severity']['informational']==1
        q=build_queue(store,tmp_path/'out'/'review',root,limit=2)
        records=json.loads((tmp_path/'out'/'review'/'review_queue.json').read_text(encoding='utf-8'))
        assert q['items']==2
        assert [r['page'] for r in records]==[1,3]
