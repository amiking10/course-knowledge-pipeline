import json
from course_pipeline.omnidoc_diagnostics import measure_prose_tokens


def test_nonofficial_prose_token_recall_and_failure_accounting(tmp_path):
    pages=[
        {'page_info':{'image_path':'a.png'},'layout_dets':[
            {'category_type':'title','text':'round robin scheduling','ignore':False},
            {'category_type':'equation_isolated','latex':'\\frac{2}{3}','text':'2/3','ignore':False}]},
        {'page_info':{'image_path':'b.png'},'layout_dets':[
            {'category_type':'text_block','text':'process state','ignore':False}]}
    ]
    (tmp_path/'subset.json').write_text(json.dumps(pages),encoding='utf-8')
    folder=tmp_path/'pred';folder.mkdir()
    (folder/'a.md').write_text('round robin scheduling',encoding='utf-8')
    run={'backend':'docling','dataset_revision':'sha','cases':[
        {'id':'a','status':'ok','prediction_file':'pred/a.md'},
        {'id':'b','status':'error'}]}
    (tmp_path/'run.json').write_text(json.dumps(run),encoding='utf-8')
    result=measure_prose_tokens(tmp_path/'subset.json',tmp_path/'run.json',tmp_path/'score.json')
    assert result['pages']==2
    assert result['micro_recall']==0.6
    assert result['macro_recall']==0.5
    assert result['metric']=='unofficial_prose_token_multiset_recall'
    assert result['cases'][1]['matched_tokens']==0
    assert json.loads((tmp_path/'score.json').read_text(encoding='utf-8'))['micro_recall']==0.6
