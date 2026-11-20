import json
from pathlib import Path
import pytest
from course_pipeline.public_benchmarks import load_manifest,pick_stratified,token_diagnostics,run_manifest

def fixture(tmp_path):
    root=tmp_path/'cases';root.mkdir();(root/'pages').mkdir()
    import pymupdf
    cases=[]
    for i,(category,content) in enumerate([('formula','a = b + 2'),('table','cells 3 4'),
                                             ('text','Operating systems'),('formula','x 5')]):
        path=root/'pages'/f'p{i}.pdf'
        doc=pymupdf.open();doc.new_page().insert_text((50,80),content);doc.save(path);doc.close()
        cases.append({'id':f'p{i}','pdf':f'pages/p{i}.pdf','stratum':category})
    manifest=root/'manifest.json'
    manifest.write_text(json.dumps({'dataset':'omnidocbench','revision':'test-local','cases':cases}))
    return manifest

def test_reject_traversal_and_duplicate(tmp_path):
    m=fixture(tmp_path)
    obj=json.loads(m.read_text())
    obj['cases'][0]['pdf']='../outside.pdf'
    m.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='safe relative'):load_manifest(m)
    obj['cases'][0]['pdf']='pages/p0.pdf'
    obj['cases'][1]['id']=obj['cases'][0]['id']
    m.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='Duplicate'):load_manifest(m)

def test_sampling_reproducible_and_balanced(tmp_path):
    m=fixture(tmp_path);cases=load_manifest(m)['cases']
    a=pick_stratified(cases,3,42);b=pick_stratified(cases,3,42)
    assert a==b
    assert set(c['stratum'] for c in a)=={'formula','table','text'}

def test_diagnostics_not_official():
    result=token_diagnostics('המתנה process 4','process המתנה 4')
    assert result['token_recall']==1
    assert 'not_official' in result['metric']
    assert token_diagnostics('','')['token_recall'] is None

def test_native_benchmark_creates_predictions(tmp_path):
    m=fixture(tmp_path)
    output=tmp_path/'out'
    result=run_manifest(m,output,backend='pymupdf-diagnostic',sample=3,seed=42)
    assert result['total_cases']==3 and result['successful']==3 and result['failed']==0
    assert result['official_score'] is None
    assert len(list((output/'predictions').glob('*.md')))==3
    assert json.loads((output/'run.json').read_text(encoding='utf-8'))['dataset_revision']=='test-local'

def test_failure_is_recorded_not_silently_skipped(tmp_path):
    m=fixture(tmp_path)
    obj=json.loads(m.read_text());obj['cases'][0]['pdf']='pages/absent.pdf'
    m.write_text(json.dumps(obj))
    with pytest.raises(FileNotFoundError):
        run_manifest(m,tmp_path/'out',backend='pymupdf-diagnostic')
