"""Score user-verified missing-content labels; never infer verification from QA flags.

A stratified sample is NOT a representative prevalence estimate.
"""
from __future__ import annotations
import json
from pathlib import Path

def evaluate_review_labels(store,labels_path:Path,output:Path)->dict:
    data=json.loads(Path(labels_path).read_text(encoding='utf-8'))
    if data.get('schema_version')!='1.0' or not isinstance(data.get('pages'),list):
        raise ValueError('Unsupported review-label schema')
    seen=set();rows=[]
    for case in data['pages']:
        key=(case['source_id'],int(case['page']))
        if key in seen:raise ValueError('Duplicate review page')
        seen.add(key)
        source=store.conn.execute('SELECT * FROM sources WHERE source_id=?',(case['source_id'],)).fetchone()
        if (source is None or source['state']!='active' or
            source['sha256']!=case['source_sha256'] or
            source['relative_path']!=case['source'] or
            source['sha256']!=source['last_parsed_hash']):
            raise ValueError(f'Unmatched or changed PDF source: {key}')
        page=store.conn.execute('SELECT flags FROM pages WHERE source_id=? AND page_no=?',key).fetchone()
        if page is None:raise ValueError('Source page missing from database')
        actual_flags=json.loads(page['flags'])
        if set(case.get('flags',[]))!=set(actual_flags):
            raise ValueError('QA flags have changed since review set creation')
        truth=case.get('labels',{}).get('missing_content')
        if truth is not None and not isinstance(truth,bool) and truth!='not_applicable':
            raise ValueError('missing_content must be true, false or not applicable')
        if not isinstance(truth,bool):continue
        predicted=any(f in actual_flags for f in (
             'probable_text_omission','secondary_native_text_disagrees_review',
             'extractor_disagreement_ambiguous','missing_numeric_evidence_review',
             'both_extractors_empty_visual_review','table_structure_review_required',
             'figure_content_review_required'))
        rows.append({'source':case['source'],'page':case['page'],
                     'predicted_omission':predicted,'human_labeled_omission':truth})
    tp=sum(r['predicted_omission'] and r['human_labeled_omission'] for r in rows)
    fp=sum(r['predicted_omission'] and not r['human_labeled_omission'] for r in rows)
    fn=sum(not r['predicted_omission'] and r['human_labeled_omission'] for r in rows)
    tn=sum(not r['predicted_omission'] and not r['human_labeled_omission'] for r in rows)
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    report={'status':'sample_evaluation_not_population_accuracy',
            'human_labeled_pages':len(rows),'review_cases':len(data['pages']),
            'confusion':{'TP':tp,'FP':fp,'FN':fn,'TN':tn},
            'precision':precision,'recall':recall,
            'warning':'Stratified reference set; metrics are exploratory and are not population-prevalence estimates.',
            'cases':rows}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
