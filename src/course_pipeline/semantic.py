"""Optional neural semantic retrieval with persistent, SHA-sensitive embedding cache.

Unlike the offline TF-IDF fallback, this uses a real multilingual sentence-embedding
model. A pretrained model must be installed/downloaded by the user. Original
source text and page provenance remain authoritative.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from .core import Store

DEFAULT_MODEL = 'intfloat/multilingual-e5-small'


def active_pages(store: Store) -> list[dict]:
    rows=store.conn.execute('''SELECT p.source_id,p.page_no,p.body,s.relative_path,
      s.sha256 FROM pages p JOIN sources s ON s.source_id=p.source_id
      WHERE s.state='active' AND s.last_parsed_hash=s.sha256
      ORDER BY s.relative_path,p.page_no''').fetchall()
    return [dict(r) for r in rows]


def document_fingerprint(docs: list[dict], model: str) -> str:
    sha=hashlib.sha256(model.encode('utf-8'))
    for d in docs:
        sha.update(json.dumps([d['source_id'],d['page_no'],d['sha256'],
            hashlib.sha256(d['body'].encode('utf-8')).hexdigest()],ensure_ascii=False).encode('utf-8'))
    return sha.hexdigest()


def _encode(encoder, texts: list[str]) -> np.ndarray:
    import numpy as np
    matrix=np.asarray(encoder.encode(texts,normalize_embeddings=True,
                                     show_progress_bar=False),dtype=np.float32)
    if matrix.ndim!=2 or matrix.shape[0]!=len(texts):
        raise ValueError('Unexpected embedding shape')
    norms=np.linalg.norm(matrix,axis=1,keepdims=True)
    return matrix / np.maximum(norms,1e-10)


def semantic_search(store: Store, query: str, cache_dir: Path,
                    model: str=DEFAULT_MODEL, limit: int=10,
                    encoder=None) -> dict:
    if not query.strip() or limit < 1:
        return {'hits':[], 'cache_hit':False, 'model':model}
    import numpy as np
    docs=active_pages(store)
    if not docs:
        return {'hits':[], 'cache_hit':False, 'model':model}
    if encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError('Install course-knowledge-pipeline[semantic]') from exc
        encoder=SentenceTransformer(model)
    cache_dir=Path(cache_dir)
    cache_dir.mkdir(parents=True,exist_ok=True)
    fingerprint=document_fingerprint(docs,model)
    cache=cache_dir/('embeddings_'+fingerprint[:24]+'.npz')
    cached=False
    if cache.exists():
        with np.load(cache,allow_pickle=False) as z:
            embeddings=z['embeddings'].copy()
        if embeddings.ndim!=2 or len(embeddings)!=len(docs):
            raise ValueError('Embedding cache corrupted or mismatched')
        cached=True
    else:
        passages=['passage: '+d['body'] for d in docs] if 'e5' in model.lower() else [d['body'] for d in docs]
        embeddings=_encode(encoder,passages)
        temp=cache.with_name(cache.name+'.tmp.npz')
        np.savez_compressed(temp,embeddings=embeddings)
        temp.replace(cache)
    qtext='query: '+query if 'e5' in model.lower() else query
    qvec=_encode(encoder,[qtext])[0]
    if len(qvec)!=embeddings.shape[1]:
        raise ValueError('Query embedding dimension mismatch')
    scores=embeddings @ qvec
    indices=np.argsort(-scores,kind='stable')[:limit]
    return {'hits':[{'source':docs[i]['relative_path'],'source_id':docs[i]['source_id'],
              'page':docs[i]['page_no'],'score':round(float(scores[i]),6),
              'excerpt':docs[i]['body'][:600]} for i in indices],
            'cache_hit':cached,'model':model, 'indexed_pages':len(docs)}
