import json
from pathlib import Path
import pytest
from course_pipeline.core import Store,Page
from course_pipeline.hybrid import reconcile
from course_pipeline.topic_index import make_index
from course_pipeline.quality_report import write_report
from course_pipeline.visual_queue import build_queue


def test_hybrid_recovers_missing_text_without_erasing_primary():
    docling=[Page(1,'RR : examples',[],[],'docling')]
    native=[Page(1,'Round Robin Q=4 process p1=24 p2=3 p3=3; average waiting time=17. '
                      'The long burst is interrupted and resumed on later time slots. '
                      'The values are diagram labels.',[],[],'pymupdf-diagnostic')]
    result=reconcile(docling,native)
    assert 'RR : examples' in result[0].body
    assert 'average waiting time=17' in result[0].body
    assert 'SECONDARY PYMUPDF' in result[0].body
    assert 'secondary_native_text_disagrees_review' in result[0].flags


def test_hybrid_rejects_mismatched_pages():
    with pytest.raises(ValueError):reconcile([Page(1,'',[],[],'docling')],[])


def test_no_duplicate_when_both_extractors_agree():
    a=Page(1,'a very useful lecture summary about interrupt descriptors and handling',[],[],'docling')
    b=Page(1,a.body,[],[],'pymupdf-diagnostic')
    assert reconcile([a],[b])[0].body==a.body


def test_zero_text_forces_visual_review():
    a=Page(1,'',[],[],'docling');b=Page(1,'',[],[],'native')
    assert 'both_extractors_empty_visual_review' in reconcile([a],[b])[0].flags


def test_index_quality_and_review_queue(tmp_path):
    root=tmp_path/'src';root.mkdir();(root/'lec.pdf').write_bytes(b'fake PDF')
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root);s=store.sources()[0]
        store.save_pages(s['source_id'],[
            Page(1,'Round Robin scheduling and interrupts',[],['visual_review_required'],'hybrid'),
            Page(2,'signals and signal handling',[],[],'hybrid')], 'hybrid',s['sha256'])
        result=make_index(store,tmp_path/'out')
        assert result['references']>=2
        assert 'lec.pdf — page 1' in (tmp_path/'out'/'COURSE_INDEX.md').read_text(encoding='utf-8')
        result=write_report(store,tmp_path/'out');assert result['flagged_pages']==1
        report=json.loads((tmp_path/'out'/'QUALITY_REPORT.json').read_text(encoding='utf-8'))
        assert report['unresolved'][0]['page']==1
        assert build_queue(store,tmp_path/'out'/'review',root)['items']==1


def test_review_report_html_escaping(tmp_path):
    root=tmp_path/'s';root.mkdir();(root/'a&b.pdf').write_bytes(b'fake')
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root);s=store.sources()[0]
        store.save_pages(s['source_id'],[Page(1,'',[],['visual_review_required'],'hybrid')], 'hybrid',s['sha256'])
        write_report(store,tmp_path/'out')
        markup=(tmp_path/'out'/'QUALITY_REPORT.html').read_text(encoding='utf-8')
        assert 'a&amp;b.pdf' in markup
