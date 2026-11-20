import json
from course_pipeline.core import Page, Store
from course_pipeline.knowledge import build_knowledge

def test_knowledge_has_source_and_is_not_fake_semantics(tmp_path):
    root=tmp_path/'inputs';root.mkdir()
    (root/'lecture.pdf').write_bytes(b'example')
    with Store(tmp_path/'kb.sqlite') as store:
        store.scan(root)
        source=store.sources()[0]
        store.save_pages(source['source_id'],[
            Page(1,'[DOCLING EXTRACTION — UNVERIFIED]\nRound Robin scheduling\n'
                 '[SECONDARY PYMUPDF EXTRACTION — UNVERIFIED; CHECK ORIGINAL PAGE]\n'
                 'Round Robin scheduling and process state',[],['probable_text_omission'],'hybrid'),
            Page(2,'Signals and interrupts',[],[],'docling')], 'hybrid',source['sha256'])
        outcome=build_knowledge(store,tmp_path/'out',terms={
            'round robin':['round robin'],
            'scheduling':['scheduling'],
            'process':['process'],
            'interrupts':['interrupts']})
        data=json.loads((tmp_path/'out'/'COURSE_KNOWLEDGE.json').read_text(encoding='utf-8'))
        assert outcome['source_pages_scanned']==2
        assert outcome['co_mention_edges']>0
        refs=data['topics'][0]['references']
        assert len(refs)==2
        assert {r['extractor'] for r in refs}=={'docling','secondary_native_pdf'}
        assert all(r['source_sha256']==source['sha256'] for r in refs)
        assert all(r['review_status']=='machine_extracted_unverified' for r in refs)
        assert all(edge['relation']=='co_mentioned_on_same_page_only' for edge in data['edges'])
        assert not any('prerequisite'==edge['relation'] for edge in data['edges'])

def test_empty_or_missing_pages_do_not_hallucinate(tmp_path):
    root=tmp_path/'inputs';root.mkdir()
    (root/'lecture.pdf').write_bytes(b'x')
    with Store(tmp_path/'kb.sqlite') as store:
        store.scan(root)
        source=store.sources()[0]
        store.save_pages(source['source_id'],[
            Page(1,'',[],['visual_review_required'],'hybrid')],
            'hybrid',source['sha256'])
        result=build_knowledge(store,tmp_path/'out',terms={'term':['foobar']})
        assert result['evidence_occurrences']==0
        assert result['co_mention_edges']==0
