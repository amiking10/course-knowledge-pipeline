"""Create a reproducible and human-labelable stratified PDF review set.

No page is marked verified during sampling. The standalone HTML can export
human labels as JSON; it cannot overwrite source files or the SQLite database.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import html
import json
import random
from zipfile import ZipFile, ZIP_DEFLATED
from .quality_report import collect
from .triage import classify

DEFAULT_QUOTAS={'critical':7,'major':7,'minor':5,'informational':5,'none':6}

def sample_pages(store, *, quotas=None, seed:int=42, pdf_only:bool=False):
    quotas=DEFAULT_QUOTAS if quotas is None else quotas
    if not quotas or any(k not in DEFAULT_QUOTAS or not isinstance(v,int) or v<0 for k,v in quotas.items()):
        raise ValueError('Invalid review-sample quotas')
    rng=random.Random(seed)
    candidates=defaultdict(list)
    for source in store.sources():
        if source['state']!='active' or source['last_parsed_hash']!=source['sha256']:continue
        if pdf_only and source['ext'].lower()!='.pdf':continue
        for page in store.pages(source['source_id']):
            flags=json.loads(page['flags'])
            level=classify(flags)
            candidates[level].append({
                'source_id':source['source_id'],'source':source['relative_path'],
                'source_sha256':source['sha256'],'page':page['page_no'],
                'severity':level,'flags':flags,'status':'unreviewed',
                'labels':{'missing_content':None,'numbers_correct':None,
                          'tables_correct':None,'formulas_correct':None,
                          'figures_correct':None,'rtl_order_correct':None},
                'reviewer_note':'',
            })
    selected=[]
    for level,count in quotas.items():
        by_source=defaultdict(list)
        for x in candidates.get(level,[]):by_source[x['source']].append(x)
        for rows in by_source.values():
            rows.sort(key=lambda r:r['page'])
            rng.shuffle(rows)
        sources=sorted(by_source)
        rng.shuffle(sources)
        while count and any(by_source.values()):
            for source in sources:
                if count and by_source[source]:
                    x=by_source[source].pop()
                    selected.append(x)
                    count-=1
    # Document shortages remain visible; never silently invent sampled pages.
    priority={name:i for i,name in enumerate(DEFAULT_QUOTAS)}
    selected.sort(key=lambda x:(priority[x['severity']],x['source'],x['page']))
    return selected

def create_review_set(store, source_root:Path, destination:Path, *,seed:int=42,
                      quotas=None, scale:float=1.25):
    if not .5<=scale<=3:raise ValueError('Review image scale must be in [0.5,3]')
    import pymupdf
    source_root=Path(source_root).resolve();destination=Path(destination).resolve()
    if not source_root.is_dir():raise NotADirectoryError(source_root)
    destination.mkdir(parents=True,exist_ok=True)
    records=sample_pages(store,quotas=quotas,seed=seed,pdf_only=True)
    if not records:raise ValueError('No active parsed pages available for review')
    documents={}
    try:
        for row in records:
            file=(source_root/row['source']).resolve()
            if not file.is_relative_to(source_root) or not file.is_file():
                raise FileNotFoundError(f'Source not available: {row["source"]}')
            if file.suffix.lower()!='.pdf':
                raise ValueError('Only PDFs supported for rendered review set')
            if file not in documents:documents[file]=pymupdf.open(file)
            document=documents[file]
            number=int(row['page'])
            if not 1<=number<=len(document):raise ValueError('Source page out of range')
            image=f"{row['source_id']}_{number:04d}.png"
            document[number-1].get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False).save(destination/image)
            row['image']=image
            parsed=store.conn.execute('SELECT body FROM pages WHERE source_id=? AND page_no=?',(row['source_id'],number)).fetchone()
            row['extracted_text']=parsed['body'] if parsed else ''
    finally:
        for document in documents.values():document.close()
    template={'schema_version':'1.0','seed':seed,'status':'awaiting_human_labels',
              'pages':records,
              'note':'Unreviewed labels are null. The author must compare original PDF with extraction.'}
    (destination/'REVIEW_LABELS_TEMPLATE.json').write_text(
        json.dumps(template,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['missing_content','numbers_correct','tables_correct',
            'formulas_correct','figures_correct','rtl_order_correct']
    cards=[]
    for i,row in enumerate(records):
        selectors=''.join('<label>'+html.escape(field.replace('_',' '))+
         '<select data-field="'+field+'"><option value="">Unreviewed</option>'
         '<option value="true">Yes</option><option value="false">No</option>'
         '<option value="na">Not applicable</option></select></label>' for field in fields)
        cards.append(f'<article data-index="{i}"><h2>{html.escape(row["source"])} — page {row["page"]}</h2>'
         f'<p>Stratum: {html.escape(row["severity"])}. Flags: {html.escape(", ".join(row["flags"]))}</p>'
         f'<div class="comparison"><div><h3>Original PDF page</h3><img loading="lazy" src="{html.escape(row["image"],quote=True)}" alt="original source slide"></div>'
         f'<div><h3>Extracted text (unverified)</h3><pre style="white-space:pre-wrap;direction:auto;max-height:600px;overflow:auto">{html.escape(row["extracted_text"])}</pre></div></div>'
         f'<div class="labels">{selectors}</div><label>Reviewer note<textarea rows="2"></textarea></label></article>')
    safe_json=json.dumps(template,ensure_ascii=False).replace('<','\\u003c')
    js="""const data=JSON.parse(document.getElementById('dataset').textContent);
async function loadSavedLabels(event){
 try {
  const file=event.target.files?.[0];if(!file)return;
  const uploaded=JSON.parse(await file.text());
  if(uploaded.schema_version!=='1.0'||!Array.isArray(uploaded.pages))throw Error('Unsupported label file');
  const byKey=new Map(uploaded.pages.map(r=>[r.source_id+':'+r.page,r]));
  for(const [i,current] of data.pages.entries()){
   const past=byKey.get(current.source_id+':'+current.page);
   if(!past||past.source_sha256!==current.source_sha256)throw Error('File contains changed/missing source');
   current.labels={...current.labels,...past.labels};
   current.reviewer_note=past.reviewer_note||'';
   const element=document.querySelector('article[data-index="'+i+'"]');
   element.querySelectorAll('select[data-field]').forEach(input=>{
    const value=current.labels[input.dataset.field];
    input.value=value===null||value===undefined?'':value==='not_applicable'?'na':String(value);
   });
   element.querySelector('textarea').value=current.reviewer_note;
  }
  alert('Previously saved labels restored.');
 } catch(err){alert('Could not restore labels: '+err.message);}
}
function saveLabels(){
 document.querySelectorAll('article[data-index]').forEach(el=>{
  const item=data.pages[Number(el.dataset.index)];
  el.querySelectorAll('select[data-field]').forEach(s=>{
   item.labels[s.dataset.field]=s.value===''?null:(s.value==='na'?'not_applicable':s.value==='true');
  });
  item.reviewer_note=el.querySelector('textarea').value;
  item.status=Object.values(item.labels).every(v=>v!==null)?'human_labeled':'partially_labeled';
 });
 data.status=data.pages.every(p=>p.status==='human_labeled')?'human_labels_complete':'human_labels_incomplete';
 const file=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
 const url=URL.createObjectURL(file),a=document.createElement('a');
 a.href=url;a.download='REVIEW_LABELS_COMPLETED.json';a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}"""
    output='<!doctype html><html><head><meta charset="utf-8"><title>PDF human gold review</title>'
    output+='<style>body{font:15px system-ui;max-width:1120px;margin:2rem auto}article{border:1px solid #ccc;padding:20px;margin:24px 0;border-radius:12px}img{max-width:100%}.comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}.comparison>div{min-width:0}.comparison pre{background:#f7f7f7;padding:12px;border-radius:8px}.labels{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media(max-width:820px){.comparison{grid-template-columns:1fr}.labels{grid-template-columns:1fr 1fr}}label{display:grid;gap:4px}select,textarea{padding:6px}button{padding:12px}</style></head><body>'
    output+='<h1>PDF extraction gold-reference review</h1><p>Compare each original slide to the generated extraction. A label is not a factual claim until you submit it after review. The generated JSON stays on your machine.</p>'
    output+='<button onclick="saveLabels()">Download review labels JSON</button><label>Resume existing review<input type="file" accept=".json" onchange="loadSavedLabels(event)"></label>'+''.join(cards)
    output+='<script type="application/json" id="dataset">'+safe_json+'</script><script>'+js+'</script></body></html>'
    (destination/'REVIEW.html').write_text(output,encoding='utf-8')
    # Portable offline review: HTML references local PNGs, so the HTML alone
    # cannot represent the visual content when moved or uploaded elsewhere.
    archive = destination / 'CONTENT_AUDIT.zip'
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as package:
        package.write(destination / 'REVIEW.html', arcname='REVIEW.html')
        package.write(destination / 'REVIEW_LABELS_TEMPLATE.json',
                      arcname='REVIEW_LABELS_TEMPLATE.json')
        for row in records:
            package.write(destination / row['image'], arcname=row['image'])
    return {'archive':str(archive),'pages':len(records),'seed':seed,
            'by_severity':{severity:sum(x['severity']==severity for x in records) for severity in DEFAULT_QUOTAS},
            'status':'awaiting_human_labels','output':str(destination)}
