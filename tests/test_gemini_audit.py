import json
import hashlib
import pytest
import pymupdf

from course_pipeline.core import Page, Store
from course_pipeline.gemini_audit import audit_pages, _validate_response, _choose_pages

def fake_answer(image,extracted,model):
    assert image.startswith(b'\x89PNG')
    assert 'Round Robin' in extracted
    assert model in {'gemini-2.5-flash','gemini-3.8-flash'}
    return {'summary':'Gantt chart omits quantum 4','missing_important_content':True,
            'uncertain':False,'issues':[{'category':'number',
             'visible_evidence':'q=4','extraction_evidence':'No quantum',
             'location':'upper right','confidence':'high'}]}

def make_store(tmp_path):
    root=tmp_path/'pdfs';root.mkdir()
    pdf=root/'scheduling.pdf'
    doc=pymupdf.open()
    for p in range(1,4):
        doc.new_page().insert_text((40,65),f'Round Robin q = {p+3}')
    doc.save(pdf);doc.close()
    store=Store(tmp_path/'db.sqlite3')
    store.scan(root)
    src=store.sources()[0]
    store.save_pages(src['source_id'],[
        Page(1,'Round Robin',[],['missing_numeric_evidence_review'],'hybrid'),
        Page(2,'Round Robin',[],['missing_numeric_evidence_review'],'hybrid'),
        Page(3,'Round Robin',[],['low_text_density'],'hybrid')],'hybrid',src['sha256'])
    return root,store,pdf

def test_dry_run_does_not_send_requests(tmp_path):
    root,store,pdf=make_store(tmp_path)
    try:
        out=tmp_path/'audit'
        result=audit_pages(store,root,out,limit=2,reviewer=lambda *a:pytest.fail('Unexpected API call'))
        assert result['actual_api_attempts']==0
        assert result['counts']['not_run']==2
        assert (out/'GEMINI_QA_REPORT.json').exists()
        assert (out/'GEMINI_QA_REPORT.html').exists()
    finally:store.conn.close()

def test_live_audit_cap_cache_and_no_source_mutation(tmp_path):
    root,store,pdf=make_store(tmp_path)
    original=hashlib.sha256(pdf.read_bytes()).hexdigest()
    try:
        out=tmp_path/'audit'
        r=audit_pages(store,root,out,live=True,limit=2,max_requests=1,reviewer=fake_answer)
        assert r['actual_api_attempts']==1
        assert r['counts']=={'audited':1,'cached':0,'not_run':0,'invalid_cache':0,
                              'skipped_request_cap':1,'error':0}
        r=audit_pages(store,root,out,live=True,limit=2,max_requests=1,reviewer=fake_answer)
        assert r['cache_hits']==1
        assert r['actual_api_attempts']==1
        assert r['counts']['cached']==1
        assert r['counts']['audited']==1
        report=json.loads((out/'GEMINI_QA_REPORT.json').read_text(encoding='utf-8'))
        assert report['pages'][0]['review_status']=='automatically_audited_not_human_verified'
        assert report['pages'][0]['result']['issues'][0]['confidence']=='high'
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==original
    finally:store.conn.close()

def test_stale_pdf_source_rejected(tmp_path):
    root,store,pdf=make_store(tmp_path)
    pdf.write_bytes(b'changed file')
    try:
        with pytest.raises(ValueError,match='SHA changed'):
            audit_pages(store,root,tmp_path/'out')
    finally:store.conn.close()

def test_response_schema_and_escaping(tmp_path):
    assert _validate_response(fake_answer(b'\x89PNG', 'Round Robin','gemini-2.5-flash'))['issues'][0]['category']=='number'
    with pytest.raises(ValueError):
        _validate_response({'summary':'hi','missing_important_content':'yes',
                            'uncertain':False,'issues':[]})
    root,store,_=make_store(tmp_path)
    try:
        malicious=lambda *a:{'summary':'<script>alert(1)</script>',
            'missing_important_content':False,'uncertain':True,
            'issues':[]}
        audit_pages(store,root,tmp_path/'audit',live=True,max_requests=1,limit=1,reviewer=malicious)
        html=(tmp_path/'audit'/'GEMINI_QA_REPORT.html').read_text(encoding='utf-8')
        assert '&lt;script&gt;' in html
        assert '<script>alert(1)</script>' not in html
    finally:store.conn.close()

def test_errors_consume_request_budget_and_are_not_cached(tmp_path):
    root,store,_=make_store(tmp_path)
    try:
        def error(*a):raise RuntimeError('test unavailable')
        result=audit_pages(store,root,tmp_path/'audit',live=True,limit=2,max_requests=1,reviewer=error)
        assert result['counts']['error']==1
        assert result['counts']['skipped_request_cap']==1
        assert result['actual_api_attempts']==1
        assert not list((tmp_path/'audit'/'cache').glob('*.json'))
    finally:store.conn.close()


def test_google_sdk_adapter_uses_env_key_and_image(monkeypatch):
    import sys
    from types import ModuleType, SimpleNamespace
    from course_pipeline.gemini_audit import _gemini_call
    calls={}
    class FakeParts:
        @staticmethod
        def from_bytes(data,mime_type):
            assert data==b'image';assert mime_type=='image/png'
            return ('image',data)
        @staticmethod
        def from_text(text):
            assert 'Round Robin' in text
            return ('text',text)
    class FakeConfig:
        def __init__(self,**kwargs):
            assert kwargs['response_mime_type']=='application/json'
            assert kwargs['max_output_tokens']<=4096
    class FakeClient:
        def __init__(self,api_key,http_options=None):
            calls['api_key']=api_key
            calls['http_options']=http_options
            self.models=SimpleNamespace(generate_content=self.generate_content)
        def generate_content(self,model,contents,config):
            calls['model']=model;calls['parts']=contents
            return SimpleNamespace(text=json.dumps(fake_answer(bytes([137])+b'PNG','Round Robin',model)))
        def close(self):calls['closed']=True
    genai=ModuleType('google.genai')
    genai.Client=FakeClient
    types=ModuleType('google.genai.types')
    types.Part=FakeParts
    types.GenerateContentConfig=FakeConfig
    types.HttpRetryOptions=lambda **kwargs: SimpleNamespace(**kwargs)
    types.HttpOptions=lambda **kwargs: SimpleNamespace(**kwargs)
    genai.types=types
    google=ModuleType('google')
    google.genai=genai
    monkeypatch.setitem(sys.modules,'google',google)
    monkeypatch.setitem(sys.modules,'google.genai',genai)
    monkeypatch.setitem(sys.modules,'google.genai.types',types)
    monkeypatch.setenv('GEMINI_API_KEY','not-a-real-key')
    result=_gemini_call(b'image','Round Robin','gemini-2.5-flash')
    assert result['missing_important_content'] is True
    assert calls['api_key']=='not-a-real-key'
    assert calls['closed'] is True
    assert calls['http_options'].timeout==45000
    assert calls['http_options'].retry_options.attempts==1
