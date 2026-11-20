import json
import pytest
from course_pipeline.core import Page,Store
from course_pipeline.review_sample import sample_pages
from course_pipeline.review_evaluate import evaluate_review_labels

def test_labels_scored_only_when_reviewed_and_source_hash_matches(tmp_path):
    source_dir=tmp_path/'sources';source_dir.mkdir()
    path=source_dir/'sample.pdf';path.write_bytes(b'page contents')
    with Store(tmp_path/'db.sqlite3') as store:
        store.scan(source_dir)
        source=store.sources()[0]
        store.save_pages(source['source_id'],[
            Page(1,'omitted table',[],['probable_text_omission'],'hybrid'),
            Page(2,'complete text',[],[],'hybrid'),
            Page(3,'short',[],['extractor_disagreement_ambiguous'],'hybrid')],
            'hybrid',source['sha256'])
        cases=sample_pages(store,quotas={'major':1,'minor':1,'none':1})
        for case in cases:
            case['labels']['missing_content']=case['page'] in {1,2}
        data={'schema_version':'1.0','pages':cases}
        label_file=tmp_path/'review.json'
        label_file.write_text(json.dumps(data),encoding='utf-8')
        r=evaluate_review_labels(store,label_file,tmp_path/'score.json')
        assert r['human_labeled_pages']==3
        assert r['confusion']=={'TP':1,'FP':1,'FN':1,'TN':0}
        assert r['precision']==0.5 and r['recall']==0.5
        # The old snapshot cannot be applied to changed source bytes.
        case=cases[0];case['source_sha256']='modified'
        label_file.write_text(json.dumps(data),encoding='utf-8')
        with pytest.raises(ValueError,match='changed PDF source'):
            evaluate_review_labels(store,label_file,tmp_path/'score.json')

def test_absent_labels_dont_become_automatic_gold(tmp_path):
    source_dir=tmp_path/'sources';source_dir.mkdir()
    (source_dir/'sample.pdf').write_bytes(b'sample')
    with Store(tmp_path/'db.sqlite3') as store:
        store.scan(source_dir)
        source=store.sources()[0]
        store.save_pages(source['source_id'],[Page(1,'content',[],[],'hybrid')],
                         'hybrid',source['sha256'])
        cases=sample_pages(store,quotas={'none':1})
        f=tmp_path/'labels.json'
        f.write_text(json.dumps({'schema_version':'1.0','pages':cases}),encoding='utf-8')
        result=evaluate_review_labels(store,f,tmp_path/'scores.json')
        assert result['human_labeled_pages']==0
        assert result['precision'] is None
        assert result['recall'] is None
