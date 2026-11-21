"""Offline lexical + character-ngram semantic-like retrieval.

Character TF-IDF is only an approximate text-similarity fallback, NOT neural
embeddings. It works without a network; optional embeddings are future work.
"""
from __future__ import annotations
from .core import Store

# This is a controlled *optional* bilingual vocabulary, not an AI translation.
# OS terms are opt-in; never expand other courses with them by default.
OS_SYNONYMS = {
    "interrupt": "פסיקה interrupts", "exception": "חריגה exceptions",
    "process": "תהליך processes", "program": "תוכנית",
    "operating system": "מערכת הפעלה", "system call": "קריאת מערכת",
    "scheduler": "מזמן זימון", "scheduling": "זימון",
    "context switch": "החלפת הקשר", "waiting": "המתנה",
    "signal": "איתות סיגנל", "kernel": "גרעין",
    "zombie": "זומבי", "fork": "fork", "policy": "מדיניות",
    "mechanism": "מנגנון", "memory": "זיכרון",
}

def expand_query(query: str, synonyms: dict[str, str] | None = None) -> str:
    # No OS-specific expansion for unrelated courses. Callers may opt in.
    lower=query.lower()
    additions=[v for k,v in (synonyms or {}).items() if k in lower]
    return query+" "+" ".join(additions) if additions else query



def hybrid_search(store: Store, query: str, limit: int = 10, lexical_weight: float = .65) -> list[dict]:
    if not 0 <= lexical_weight <= 1:
        raise ValueError('lexical_weight must be in [0,1]')
    if limit < 1 or not query.strip():
        return []
    expanded=expand_query(query)
    docs = store.conn.execute('''SELECT p.source_id, p.page_no, p.body, s.relative_path
      FROM pages p JOIN sources s ON p.source_id=s.source_id
      WHERE s.state='active' AND s.last_parsed_hash=s.sha256
      ORDER BY s.relative_path,p.page_no''').fetchall()
    if not docs:
        return []
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    corpus = [r['body'] for r in docs]
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 5), min_df=1,
                                 max_features=60000, sublinear_tf=True)
    matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(vectorizer.transform([expanded]), matrix).ravel()
    lex_rows = store.search(expanded, max(limit * 5, 100))
    lexical_ids = {(r['source_id'], r['page_no']): pos for pos, r in enumerate(lex_rows)}
    hits=[]
    for i, row in enumerate(docs):
        key=(row['source_id'], row['page_no'])
        lexical = (1/(1+lexical_ids[key])) if key in lexical_ids else 0.
        score = lexical_weight * lexical + (1-lexical_weight)*float(similarities[i])
        if score <= 0: continue
        hits.append({'source':row['relative_path'],'source_id':row['source_id'],
            'page':row['page_no'],'score':round(score,6),
            'excerpt':row['body'][:600]})
    return sorted(hits, key=lambda x:(-x['score'],x['source'],x['page']))[:limit]
