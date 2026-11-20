import json
from course_pipeline.core import Store,Page
from course_pipeline.prepared_retrieval import PreparedRetrievalIndex
from course_pipeline.retrieval import hybrid_search
from course_pipeline.benchmark import evaluate

def make_store(tmp_path):
    directory=tmp_path/'sources';directory.mkdir()
    (directory/'lecture.pdf').write_bytes(b'lecture')
    store=Store(tmp_path/'db.sqlite')
    store.scan(directory)
    source=store.sources()[0]
    store.save_pages(source['source_id'],[
        Page(1,'Round Robin scheduling and processes',[],['probable_text_omission'],'hybrid'),
        Page(2,'Kernel interrupt signals and exceptions',[],[],'hybrid'),
        Page(3,'Process context switch and waiting time',[],[],'hybrid')],
        'hybrid',source['sha256'])
    return store,source

def test_prepared_index_matches_previous_scores(tmp_path):
    store,source=make_store(tmp_path)
    try:
        index=PreparedRetrievalIndex(store)
        for q in ['Round Robin','kernel','process context switch']:
            original=hybrid_search(store,q,limit=3)
            prepared=index.search(q,limit=3)
            assert [(r['page'],r['score']) for r in prepared]==[
                   (r['page'],r['score']) for r in original]
            assert all(r['source_sha256']==source['sha256'] for r in prepared)
            assert all(r['provenance_status']=='machine_extracted_unverified' for r in prepared)
        assert index.search('')==[]
        assert index.search('any',limit=0)==[]
    finally:
        store.conn.close()

def test_benchmark_reuses_one_index(monkeypatch,tmp_path):
    store,source=make_store(tmp_path)
    try:
        cases=[
            {'question':'Round Robin','expected':[{'source':'lecture.pdf','page':1}]},
            {'question':'kernel interrupt','expected':[{'source':'lecture.pdf','page':2}]}]
        dataset=tmp_path/'cases.json';dataset.write_text(json.dumps(cases))
        from course_pipeline import benchmark
        real=benchmark.PreparedRetrievalIndex
        seen=[]
        def counted(s):
            seen.append(1)
            return real(s)
        monkeypatch.setattr(benchmark,'PreparedRetrievalIndex',counted)
        result=evaluate(store,dataset,k=3)
        assert result['count']==2
        assert len(seen)==1
        assert result['hit_at_k']==1.0
    finally:
        store.conn.close()
