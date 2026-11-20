"""Reusable char-ngram retrieval index for deterministic multi-query evaluations.

A prepared index matches the original hybrid_search ranking while avoiding
refitting the same 214-page corpus for every benchmark question.
"""
from __future__ import annotations
from .core import Store
from .retrieval import expand_query

class PreparedRetrievalIndex:
    def __init__(self, store: Store):
        self.store=store
        self.docs=store.conn.execute('''SELECT p.source_id,p.page_no,p.body,s.relative_path,s.sha256,p.flags
          FROM pages p JOIN sources s ON p.source_id=s.source_id
          WHERE s.state='active' AND s.last_parsed_hash=s.sha256
          ORDER BY s.relative_path,p.page_no''').fetchall()
        self.vectorizer=None
        self.matrix=None
        if self.docs:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer=TfidfVectorizer(analyzer='char',ngram_range=(2,5),min_df=1,
                max_features=60000,sublinear_tf=True)
            self.matrix=self.vectorizer.fit_transform([r['body'] for r in self.docs])

    def search(self, query: str, limit: int=10, lexical_weight: float=.65) -> list[dict]:
        if not 0<=lexical_weight<=1:
            raise ValueError('lexical_weight must be in [0,1]')
        if limit<1 or not query.strip() or not self.docs:return []
        from sklearn.metrics.pairwise import cosine_similarity
        expanded=expand_query(query)
        similarities=cosine_similarity(self.vectorizer.transform([expanded]),self.matrix).ravel()
        lexical_rows=self.store.search(expanded,max(limit*5,100))
        lexical_pos={(r['source_id'],r['page_no']):i for i,r in enumerate(lexical_rows)}
        hits=[]
        for i,row in enumerate(self.docs):
            key=(row['source_id'],row['page_no'])
            lexical=1/(1+lexical_pos[key]) if key in lexical_pos else 0.
            score=lexical_weight*lexical+(1-lexical_weight)*float(similarities[i])
            if score<=0:continue
            hits.append({'source':row['relative_path'],'source_id':row['source_id'],
                'source_sha256':row['sha256'],'page':row['page_no'],
                'flags':__import__('json').loads(row['flags']),
                'score':round(score,6),'excerpt':row['body'][:600],
                'provenance_status':'machine_extracted_unverified'})
        return sorted(hits,key=lambda x:(-x['score'],x['source'],x['page']))[:limit]
