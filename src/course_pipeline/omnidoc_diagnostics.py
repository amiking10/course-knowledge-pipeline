"""Non-official token-recall diagnostic on OmniDocBench prose annotations.

Important: this is NOT OmniDocBench's end-to-end edit distance, table TEDS, or
formula CDM; no leaderboard comparisons can be inferred from these numbers.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from .comparison import tokens

TEXT_CATEGORIES={'text_block','title','equation_explanation','figure_caption','table_caption'}


def measure_prose_tokens(ground_truth: Path, run_path: Path, output: Path)->dict:
    ground_truth=Path(ground_truth)
    run_path=Path(run_path)
    run=json.loads(run_path.read_text(encoding='utf-8'))
    annotation=json.loads(ground_truth.read_text(encoding='utf-8'))
    page_by_stem={}
    for item in annotation:
        stem=Path(item['page_info']['image_path']).stem
        if stem in page_by_stem: raise ValueError('Duplicate ground-truth page stem')
        page_by_stem[stem]=item
    results=[]
    for case in run['cases']:
        stem=case['id']
        if stem not in page_by_stem: raise ValueError('Case missing in ground truth: '+stem)
        item=page_by_stem[stem]
        prose='\n'.join(block.get('text','') for block in item['layout_dets']
                        if not block.get('ignore') and block.get('category_type') in TEXT_CATEGORIES)
        reference=Counter(tokens(prose))
        total=sum(reference.values())
        if case['status']=='ok':
            prediction_file=run_path.parent/case['prediction_file']
            predicted=Counter(tokens(prediction_file.read_text(encoding='utf-8')))
        else:
            predicted=Counter()
        overlap=sum((reference & predicted).values())
        results.append({'id':stem,'reference_tokens':total,'matched_tokens':overlap,
                        'diagnostic_recall':round(overlap/total,4) if total else None,
                        'status':case['status']})
    valid=[x for x in results if x['reference_tokens']]
    micro=sum(x['matched_tokens'] for x in valid)/sum(x['reference_tokens'] for x in valid) if valid else None
    macro=sum(x['matched_tokens']/x['reference_tokens'] for x in valid)/len(valid) if valid else None
    report={'metric':'unofficial_prose_token_multiset_recall',
            'scope':'selected text, title, equation-explanation and caption annotations only',
            'excludes':'formulas, tables, layout order; use OmniDocBench official evaluator',
            'dataset_revision':run['dataset_revision'],'backend':run['backend'],
            'pages':len(results),'pages_with_prose':len(valid),
            'micro_recall':round(micro,4) if micro is not None else None,
            'macro_recall':round(macro,4) if macro is not None else None,
            'cases':results}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
