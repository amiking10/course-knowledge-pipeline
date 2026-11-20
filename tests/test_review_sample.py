import json
import pymupdf
from course_pipeline.core import Page,Store
from course_pipeline.review_sample import sample_pages, create_review_set

def make_sources(tmp_path):
    root=tmp_path/'pdfs';root.mkdir()
    with Store(tmp_path/'db.sqlite3') as store:
        for n in ['lecture_a.pdf','lecture_b.pdf']:
            doc=pymupdf.open()
            for i in range(3): doc.new_page().insert_text((30,65),f'Original {n} page {i+1}')
            doc.save(root/n);doc.close()
        store.scan(root)
        for s in store.sources():
            store.save_pages(s['source_id'],[
                Page(1,'Scheduling',[],['missing_numeric_evidence_review'],'hybrid'),
                Page(2,'Interrupt',[],['extractor_disagreement_ambiguous'],'hybrid'),
                Page(3,'OS systems',[],[],'hybrid')],
                'hybrid',s['sha256'])
        selections=sample_pages(store,quotas={'critical':2,'minor':2,'none':2},seed=42)
        assert len(selections)==6
        assert {e['source'] for e in selections}=={'lecture_a.pdf','lecture_b.pdf'}
        assert all(e['status']=='unreviewed' and e['labels']['missing_content'] is None for e in selections)
        result=create_review_set(store,root,tmp_path/'gold',seed=42,
                                 quotas={'critical':2,'minor':2,'none':2})
        assert result['pages']==6
        data=json.loads((tmp_path/'gold'/'REVIEW_LABELS_TEMPLATE.json').read_text(encoding='utf-8'))
        assert data['status']=='awaiting_human_labels'
        assert len(data['pages'])==6
        assert all((tmp_path/'gold'/row['image']).is_file() for row in data['pages'])
        html=(tmp_path/'gold'/'REVIEW.html').read_text(encoding='utf-8')
        assert 'Download review labels JSON' in html
        assert 'saveLabels' in html
        assert 'human_labeled' in html
        assert '<details>' in html and 'Show extracted text' in html

def test_deterministic_sample_quota_and_distinct_pages(tmp_path):
    root=tmp_path/'pdfs';root.mkdir()
    (root/'lec.pdf').write_bytes(b'test')
    with Store(tmp_path/'db.sqlite3') as store:
        store.scan(root)
        s=store.sources()[0]
        store.save_pages(s['source_id'],
                         [Page(i,f'page {i}',[],[],'docling') for i in range(1,8)],
                         'docling',s['sha256'])
        a=sample_pages(store,quotas={'none':4},seed=99)
        b=sample_pages(store,quotas={'none':4},seed=99)
        assert a==b
        assert len({x['page'] for x in a})==4
