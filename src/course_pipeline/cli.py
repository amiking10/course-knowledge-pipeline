"""Command line pipeline; explicit backend prevents silent quality downgrade."""
import argparse
import json
import sys
import time
from .progress_display import parsing_heartbeat
from pathlib import Path
from .core import Store
from .parsers import parse
from .quality import assess
from .exporter import export_project
from .retrieval import hybrid_search
from .benchmark import evaluate
from .visuals import render_review
from .pdf_bundle import export_pdf_bundle
from .semantic import semantic_search, DEFAULT_MODEL
from .topic_index import make_index
from .quality_report import write_report
from .visual_queue import build_queue
from .import_export import import_and_reconcile
from .recovery_gate import validate_recovery
from .public_benchmarks import run_manifest
from .omnidoc_prep import prepare_omnidocbench
from .benchmark_compare import compare_runs
from .omnidoc_diagnostics import measure_prose_tokens
from .official_omni import prepare_official_evaluation
from .visual_evidence import build_visual_evidence
from .knowledge import build_knowledge
from .prepared_retrieval import PreparedRetrievalIndex
from .review_sample import create_review_set
from .review_evaluate import evaluate_review_labels
from .gemini_audit import audit_pages
from .structural_recovery import build_structural_recovery
from .structural_reconstruction import reconstruct_report
from .timeline_validation import validate_reconstruction_report
from .release_validation import verify_export


def main(argv=None):
    ap=argparse.ArgumentParser(description='Course knowledge pipeline')
    ap.add_argument('--db',type=Path,default=Path('data/course.sqlite3'))
    commands=ap.add_subparsers(dest='command',required=True)
    s=commands.add_parser('scan');s.add_argument('source_dir',type=Path)
    p=commands.add_parser('parse');p.add_argument('source_dir',type=Path)
    p.add_argument('--progress',action='store_true',help='Display completed-document progress while parsing')
    p.add_argument('--backend',choices=['docling','hybrid','docling-no-ocr','hybrid-no-ocr','docling-formula','hybrid-formula','pymupdf-diagnostic'],default='docling')
    evidence=commands.add_parser('grounded-search');evidence.add_argument('query');evidence.add_argument('--limit',type=int,default=5)
    q=commands.add_parser('search');q.add_argument('query');q.add_argument('--limit',type=int,default=10)
    h=commands.add_parser('hybrid-search');h.add_argument('query');h.add_argument('--limit',type=int,default=10)
    n=commands.add_parser('semantic-search');n.add_argument('query');n.add_argument('--model',default=DEFAULT_MODEL);n.add_argument('--cache',type=Path,default=Path('data/embeddings'));n.add_argument('--limit',type=int,default=10)
    ready=commands.add_parser('verify-export')
    ready.add_argument('export_dir',type=Path)
    ready.add_argument('--require-visuals',action='store_true')
    ready.add_argument('--strict-indexes',action='store_true',help='Verify course indexes against the current SQLite source pages')
    ready.add_argument('--source-dir',type=Path)
    ready.add_argument('--quality-report',type=Path,help='Optional QA report in the INTERNAL directory')
    tv=commands.add_parser('validate-timelines')
    tv.add_argument('prior_report',type=Path)
    tv.add_argument('output_dir',type=Path)
    sc=commands.add_parser('reconstruct-structures')
    sc.add_argument('source_dir',type=Path)
    sc.add_argument('prior_report',type=Path)
    sc.add_argument('output_dir',type=Path)
    sc.add_argument('--limit',type=int,default=7)
    sr=commands.add_parser('structural-recovery')
    sr.add_argument('source_dir',type=Path)
    sr.add_argument('output_dir',type=Path)
    sr.add_argument('--audit-report',type=Path)
    sr.add_argument('--severity',choices=['critical','major','minor','informational','none','all'],default='critical')
    sr.add_argument('--limit',type=int,default=7)
    ga=commands.add_parser('gemini-audit')
    ga.add_argument('source_dir',type=Path)
    ga.add_argument('output_dir',type=Path)
    ga.add_argument('--severity',choices=['critical','major','minor','informational','all'],default='critical')
    ga.add_argument('--limit',type=int,default=7)
    ga.add_argument('--max-requests',type=int,default=7)
    ga.add_argument('--model',default='gemini-3.8-flash')
    ga.add_argument('--live',action='store_true',help='Explicitly send rendered PDF pages and extracted text to Gemini API')
    revscore=commands.add_parser('evaluate-review-labels');revscore.add_argument('labels',type=Path);revscore.add_argument('output',type=Path)
    reviewset=commands.add_parser('review-gold-sample');reviewset.add_argument('source_dir',type=Path);reviewset.add_argument('output',type=Path);reviewset.add_argument('--seed',type=int,default=42)
    kg=commands.add_parser('build-knowledge');kg.add_argument('destination',type=Path)
    official=commands.add_parser('benchmark-official-config');official.add_argument('ground_truth',type=Path);official.add_argument('run',type=Path);official.add_argument('output',type=Path);official.add_argument('--evaluator-commit',required=True)
    evidence=commands.add_parser('visual-evidence');evidence.add_argument('source_dir',type=Path);evidence.add_argument('output',type=Path);evidence.add_argument('--severity',default='critical',choices=['critical','major','minor','informational','all']);evidence.add_argument('--limit',type=int,default=30)
    diag=commands.add_parser('benchmark-text-diagnostic');diag.add_argument('ground_truth',type=Path);diag.add_argument('run',type=Path);diag.add_argument('output',type=Path)
    cmp=commands.add_parser('benchmark-compare');cmp.add_argument('output',type=Path);cmp.add_argument('runs',type=Path,nargs='+')
    prep=commands.add_parser('prepare-omnidocbench');prep.add_argument('output',type=Path);prep.add_argument('--revision',required=True);prep.add_argument('--count',type=int,default=200);prep.add_argument('--seed',type=int,default=42)
    pub=commands.add_parser('benchmark-public');pub.add_argument('manifest',type=Path);pub.add_argument('output',type=Path);pub.add_argument('--backend',choices=['docling','hybrid','docling-formula','hybrid-formula','pymupdf-diagnostic'],default='hybrid');pub.add_argument('--sample',type=int);pub.add_argument('--seed',type=int,default=42)
    b=commands.add_parser('benchmark');b.add_argument('dataset',type=Path);b.add_argument('--k',type=int,default=5)
    v=commands.add_parser('render-review');v.add_argument('pdf',type=Path);v.add_argument('destination',type=Path);v.add_argument('--pages',nargs='+',type=int,required=True)
    a=commands.add_parser('export-pdf');a.add_argument('source_dir',type=Path);a.add_argument('output_pdf',type=Path)
    e=commands.add_parser('export');e.add_argument('destination',type=Path);e.add_argument('--annotations',type=Path)
    gate=commands.add_parser('validate-recovery');gate.add_argument('targets',type=Path)
    imp=commands.add_parser('reconcile-export');imp.add_argument('source_dir',type=Path);imp.add_argument('previous_export',type=Path)
    t=commands.add_parser('build-index');t.add_argument('destination',type=Path)
    qr=commands.add_parser('quality-report');qr.add_argument('destination',type=Path)
    rq=commands.add_parser('review-queue');rq.add_argument('source_dir',type=Path);rq.add_argument('destination',type=Path);rq.add_argument('--render',action='store_true')
    args=ap.parse_args(argv)
    if args.command=='validate-timelines':
        outcome=validate_reconstruction_report(args.prior_report,args.output_dir)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        return outcome
    if args.command=='benchmark-official-config':
        outcome=prepare_official_evaluation(args.ground_truth,args.run,args.output,evaluator_commit=args.evaluator_commit)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        return outcome
    if args.command=='benchmark-text-diagnostic':
        outcome=measure_prose_tokens(args.ground_truth,args.run,args.output)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        return outcome
    if args.command=='benchmark-compare':
        outcome=compare_runs(args.runs,args.output)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        return outcome
    if args.command=='prepare-omnidocbench':
        outcome=prepare_omnidocbench(args.output,revision=args.revision,count=args.count,seed=args.seed)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        return outcome
    if args.command=='benchmark-public':
        outcome=run_manifest(args.manifest,args.output,args.backend,sample=args.sample,seed=args.seed)
        print(json.dumps(outcome,ensure_ascii=False,indent=2))
        if outcome['failed']: raise SystemExit(2)
        return outcome
    with Store(args.db) as store:
        if args.command=='verify-export':
            outcome=verify_export(store,args.export_dir,require_visuals=args.require_visuals,
                                  source_dir=args.source_dir, quality_report_path=args.quality_report,
                                  strict_indexes=args.strict_indexes)
        elif args.command=='scan':
            outcome=store.scan(args.source_dir)
        elif args.command=='parse':
            root=args.source_dir.resolve();store.scan(root)
            failures=[]; reports=[]
            pending=store.pending(args.backend)
            total=len(pending)
            if args.progress:
                print(f'[PARSE] {total} document(s) require processing; unchanged documents are reused.', file=sys.stderr,flush=True)
            for completed,source in enumerate(pending,1):
                if args.progress:
                    print(f'[PARSE] Starting {completed}/{total}: {source["relative_path"]}', file=sys.stderr,flush=True)
                path=root/source['relative_path']
                try:
                    started=time.monotonic()
                    if args.progress:
                        with parsing_heartbeat(source["relative_path"]):
                            pages=parse(path,args.backend)
                    else:
                        pages=parse(path,args.backend)
                    elapsed=time.monotonic()-started
                    if args.progress:
                        print(f'[PARSE] Converted {source["relative_path"]}: {len(pages)} page(s) in {elapsed:.1f}s', file=sys.stderr,flush=True)
                    report=assess(pages,path)
                    flags_by_page={}
                    for w in report['warnings']:
                        if w['page'] is not None:flags_by_page.setdefault(w['page'],[]).append(w['kind'])
                    for page in pages:
                        page.flags=sorted(set(page.flags + flags_by_page.get(page.page_no,[])))
                    store.save_pages(source['source_id'],pages,args.backend,source['sha256'])
                    reports.append(report)
                except Exception as exc:
                    failures.append({'source':source['relative_path'],'error':str(exc)})
                finally:
                    if args.progress:
                        percent=round(completed*100/total)
                        print(f'[PARSE {percent:3d}%] {completed}/{total} processed: {source["relative_path"]}', file=sys.stderr,flush=True)
            if args.progress and not total:
                print('[PARSE 100%] No new or modified documents to parse.', file=sys.stderr,flush=True)
            outcome={'parsed':len(reports),'failures':failures,'reports':reports,
                     'backend':args.backend,'production_ready':False, 'note':'Requires verified visual/text fidelity and retrieval benchmark'}
        elif args.command=='search':
            outcome=[{'source':r['relative_path'],'page':r['page_no'],
                      'rank':round(r['rank'],3),'excerpt':r['body'][:350]} for r in store.search(args.query,args.limit)]
        elif args.command=='grounded-search':
            index=PreparedRetrievalIndex(store)
            hits=index.search(args.query,limit=args.limit)
            outcome={'question':args.query,'evidence':hits,'has_supporting_pages':bool(hits),
                     'answer_generated':False,'note':'Search results are candidates, not verified answers.'}
        elif args.command=='hybrid-search': outcome=hybrid_search(store,args.query,args.limit)
        elif args.command=='benchmark': outcome=evaluate(store,args.dataset,args.k)
        elif args.command=='semantic-search': outcome=semantic_search(store,args.query,args.cache,args.model,args.limit)
        elif args.command=='reconstruct-structures':
            outcome=reconstruct_report(store,args.source_dir,args.prior_report,
                                       args.output_dir,limit=args.limit)
        elif args.command=='structural-recovery':
            outcome=build_structural_recovery(
                store,args.source_dir,args.output_dir,
                audit_report_path=args.audit_report,limit=args.limit,
                severity=args.severity)
        elif args.command=='gemini-audit':
            outcome=audit_pages(store,args.source_dir,args.output_dir,
                limit=args.limit,severity=args.severity,model=args.model,
                max_requests=args.max_requests,live=args.live)
        elif args.command=='evaluate-review-labels': outcome=evaluate_review_labels(store,args.labels,args.output)
        elif args.command=='review-gold-sample': outcome=create_review_set(store,args.source_dir,args.output,seed=args.seed)
        elif args.command=='build-knowledge': outcome=build_knowledge(store,args.destination)
        elif args.command=='visual-evidence': outcome=build_visual_evidence(store,args.source_dir,args.output,severity=args.severity,limit=args.limit)
        elif args.command=='validate-recovery': outcome=validate_recovery(store,args.targets)
        elif args.command=='reconcile-export': outcome=import_and_reconcile(store,args.source_dir,args.previous_export)
        elif args.command=='build-index': outcome=make_index(store,args.destination)
        elif args.command=='quality-report': outcome=write_report(store,args.destination)
        elif args.command=='review-queue': outcome=build_queue(store,args.destination,args.source_dir,render=args.render)
        elif args.command=='render-review': outcome=render_review(args.pdf,args.pages,args.destination)
        elif args.command=='export-pdf': outcome=export_pdf_bundle(store,args.source_dir,args.output_pdf)
        else: outcome=export_project(store,args.destination,annotations_path=args.annotations)
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
    if args.command in ("validate-recovery","verify-export") and not outcome["passed"]:
        raise SystemExit(3)
    if args.command == "parse" and outcome["failures"]:
        raise SystemExit(2)
    return outcome

if __name__=='__main__':main()
