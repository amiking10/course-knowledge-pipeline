"""Deterministic retrieval evaluation with author-reviewed gold citations."""
from __future__ import annotations
import json
from pathlib import Path
from .prepared_retrieval import PreparedRetrievalIndex
from .core import Store


def evaluate(store: Store, dataset: Path, k: int = 5) -> dict:
    """Gold items: {question, expected:[{source,page}]}.

    Exact expected page matching avoids mistaking a plausible answer for correct
    provenance. User-authored examples must be manually checked against PDFs.
    """
    cases=json.loads(Path(dataset).read_text(encoding='utf-8'))
    if not cases: raise ValueError('Benchmark dataset cannot be empty')
    results=[]
    index=PreparedRetrievalIndex(store)
    for case in cases:
        hits=index.search(case['question'],limit=k)
        expected={(x['source'],int(x['page'])) for x in case['expected']}
        actual=[(h['source'],h['page']) for h in hits]
        first=next((i+1 for i,hit in enumerate(actual) if hit in expected),None)
        results.append({'question':case['question'],'hit':first is not None,
                        'rank':first,'top':actual[:3]})
    return {'count':len(cases),'hit_at_k':sum(x['hit'] for x in results)/len(results),
            'mrr':sum(1/x['rank'] for x in results if x['rank'])/len(results),
            'k':k,'cases':results}
