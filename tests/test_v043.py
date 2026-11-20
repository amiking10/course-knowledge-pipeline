import json
from pathlib import Path
import pytest
import pymupdf
from course_pipeline.core import Page,Store
from course_pipeline.visual_evidence import build_visual_evidence
from course_pipeline.official_omni import prepare_official_evaluation

COMMIT='1'*40

def test_official_config_and_preflight(tmp_path):
    gt=tmp_path/'subset.json'
    gt.write_text(json.dumps([{'page_info':{'image_path':'images/alpha.png'}}]),encoding='utf-8')
    predictions=tmp_path/'run'/'predictions'
    predictions.mkdir(parents=True)
    (predictions/'alpha.md').write_text('Equation A=4',encoding='utf-8')
    run=tmp_path/'run'/'run.json'
    run.write_text(json.dumps({'dataset':'omnidocbench','dataset_revision':'pinned',
       'backend':'docling','cases':[{'id':'alpha','status':'ok','prediction_file':'predictions/alpha.md'}]}),encoding='utf-8')
    report=prepare_official_evaluation(gt,run,tmp_path/'official',evaluator_commit=COMMIT)
    assert report['status']=='prepared_not_scored'
    assert 'end2end_eval:' in (tmp_path/'official'/'official_end2end.yaml').read_text(encoding='utf-8')
    assert 'CDM' in (tmp_path/'official'/'official_end2end.yaml').read_text(encoding='utf-8')
    with pytest.raises(ValueError,match='40-digit'):
        prepare_official_evaluation(gt,run,tmp_path/'bad',evaluator_commit='main')
    (predictions/'alpha.md').unlink()
    with pytest.raises(ValueError,match='missing/failed'):
        prepare_official_evaluation(gt,run,tmp_path/'bad',evaluator_commit=COMMIT)

def test_visual_evidence_requires_review_and_keeps_source(tmp_path):
    root=tmp_path/'source';root.mkdir()
    pdf=root/'lec.pdf'
    doc=pymupdf.open()
    doc.new_page().insert_text((40,70),'Q=4 p1=24 p2=3')
    doc.save(pdf);doc.close()
    with Store(tmp_path/'test.sqlite3') as store:
        store.scan(root)
        source=store.sources()[0]
        store.save_pages(source['source_id'],
                         [Page(1,'Round Robin',[],['missing_numeric_evidence_review'],'hybrid')],
                         'hybrid',source['sha256'])
        result=build_visual_evidence(store,root,tmp_path/'review')
        assert result['items']==1 and result['reviewed']==0
        rows=json.loads((tmp_path/'review'/'review_queue.json').read_text(encoding='utf-8'))
        assert rows[0]['status']=='unreviewed'
        assert '24' in rows[0]['numbers_in_native_not_primary']
        assert (tmp_path/'review'/rows[0]['image']).is_file()
        assert (tmp_path/'review'/'INDEX.html').is_file()
        assert 'Round Robin' in (tmp_path/'review'/(Path(rows[0]['image']).stem+'_extracted.txt')).read_text(encoding='utf-8')

def test_visual_evidence_no_implicit_verification(tmp_path):
    root=tmp_path/'source';root.mkdir()
    doc=pymupdf.open();doc.new_page();doc.save(root/'empty.pdf');doc.close()
    with Store(tmp_path/'test.sqlite3') as store:
        store.scan(root)
        s=store.sources()[0]
        store.save_pages(s['source_id'],[Page(1,'',[],['both_extractors_empty_visual_review'],'hybrid')],
                         'hybrid',s['sha256'])
        result=build_visual_evidence(store,root,tmp_path/'review')
        assert result['reviewed']==0
        with pytest.raises(ValueError,match='Invalid severity'):
            build_visual_evidence(store,root,tmp_path/'bad',severity='confirmed')
