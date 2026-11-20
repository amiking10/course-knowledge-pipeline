import json
import pytest
from course_pipeline.benchmark_compare import compare_runs

def make_run(backend,hash_value='abc',error=False):
    cases=[{'id':'p1','source_sha256':hash_value,'status':'error' if error else 'ok',
            'duration_seconds':1.23}]
    return {'dataset':'omnidocbench','dataset_revision':'pinned-rev',
            'backend':backend,'total_cases':1,'successful':0 if error else 1,
            'failed':1 if error else 0,'cases':cases}

def test_same_sample_run_comparison(tmp_path):
    paths=[]
    for name in ['docling','hybrid']:
        p=tmp_path/f'{name}.json';p.write_text(json.dumps(make_run(name)));paths.append(p)
    result=compare_runs(paths,tmp_path/'summary.json')
    assert result['identical_source_bytes']
    assert len(result['results'])==2
    assert result['results'][0]['median_seconds_per_success']==1.23
    assert result['results'][0]['official_score'] is None

def test_compare_rejects_mismatched_bytes(tmp_path):
    a=tmp_path/'a.json';b=tmp_path/'b.json'
    a.write_text(json.dumps(make_run('docling')))
    b.write_text(json.dumps(make_run('hybrid','different')))
    with pytest.raises(ValueError,match='different samples'):
        compare_runs([a,b],tmp_path/'out.json')

def test_compare_counts_failures(tmp_path):
    a=tmp_path/'a.json';b=tmp_path/'b.json'
    a.write_text(json.dumps(make_run('docling',error=True)))
    b.write_text(json.dumps(make_run('hybrid')))
    result=compare_runs([a,b],tmp_path/'out.json')
    assert result['results'][0]['failed_ids']==['p1']
    assert result['results'][0]['median_seconds_per_success'] is None
