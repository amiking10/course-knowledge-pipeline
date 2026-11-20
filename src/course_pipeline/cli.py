"""Command line pipeline; explicit backend prevents silent quality downgrade."""
import argparse
import json
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


def main(argv=None):
    ap=argparse.ArgumentParser(description='Course knowledge pipeline')
    ap.add_argument('--db',type=Path,default=Path('data/course.sqlite3'))
    commands=ap.add_subparsers(dest='command',required=True)
    s=commands.add_parser('scan');s.add_argument('source_dir',type=Path)
    p=commands.add_parser('parse');p.add_argument('source_dir',type=Path)
    p.add_argument('--backend',choices=['docling','pymupdf-diagnostic'],default='docling')
    q=commands.add_parser('search');q.add_argument('query');q.add_argument('--limit',type=int,default=10)
    h=commands.add_parser('hybrid-search');h.add_argument('query');h.add_argument('--limit',type=int,default=10)
    n=commands.add_parser('semantic-search');n.add_argument('query');n.add_argument('--model',default=DEFAULT_MODEL);n.add_argument('--cache',type=Path,default=Path('data/embeddings'));n.add_argument('--limit',type=int,default=10)
    b=commands.add_parser('benchmark');b.add_argument('dataset',type=Path);b.add_argument('--k',type=int,default=5)
    v=commands.add_parser('render-review');v.add_argument('pdf',type=Path);v.add_argument('destination',type=Path);v.add_argument('--pages',nargs='+',type=int,required=True)
    a=commands.add_parser('export-pdf');a.add_argument('source_dir',type=Path);a.add_argument('output_pdf',type=Path)
    e=commands.add_parser('export');e.add_argument('destination',type=Path);e.add_argument('--annotations',type=Path)
    args=ap.parse_args(argv)
    with Store(args.db) as store:
        if args.command=='scan':
            outcome=store.scan(args.source_dir)
        elif args.command=='parse':
            root=args.source_dir.resolve();store.scan(root)
            failures=[]; reports=[]
            for source in store.pending(args.backend):
                path=root/source['relative_path']
                try:
                    pages=parse(path,args.backend)
                    report=assess(pages,path)
                    store.save_pages(source['source_id'],pages,args.backend,source['sha256'])
                    reports.append(report)
                except Exception as exc:
                    failures.append({'source':source['relative_path'],'error':str(exc)})
            outcome={'parsed':len(reports),'failures':failures,'reports':reports,
                     'backend':args.backend,'production_ready':False, 'note':'Requires verified visual/text fidelity and retrieval benchmark'}
        elif args.command=='search':
            outcome=[{'source':r['relative_path'],'page':r['page_no'],
                      'rank':round(r['rank'],3),'excerpt':r['body'][:350]} for r in store.search(args.query,args.limit)]
        elif args.command=='hybrid-search': outcome=hybrid_search(store,args.query,args.limit)
        elif args.command=='benchmark': outcome=evaluate(store,args.dataset,args.k)
        elif args.command=='semantic-search': outcome=semantic_search(store,args.query,args.cache,args.model,args.limit)
        elif args.command=='render-review': outcome=render_review(args.pdf,args.pages,args.destination)
        elif args.command=='export-pdf': outcome=export_pdf_bundle(store,args.source_dir,args.output_pdf)
        else: outcome=export_project(store,args.destination,annotations_path=args.annotations)
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
    if args.command == "parse" and outcome["failures"]:
        raise SystemExit(2)
    return outcome

if __name__=='__main__':main()
