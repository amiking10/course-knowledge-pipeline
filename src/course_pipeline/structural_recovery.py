"""Conservative, evidence-linked structural recovery proposals for PDF pages.

Every suggestion is a *candidate sidecar*. No original PDF, parsed SQLite row,
search index, or user-visible course export is changed by this module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import html
import json
import re
import tempfile

from .core import hash_file
from .triage import classify

SCHEMA_VERSION="0.11.0"
HEBREW=re.compile(r"[\u0590-\u05ff]")
LATIN=re.compile(r"[A-Za-z]")
NUMBER=re.compile(r"(?<![\w.])(?:\d+(?:\.\d+)?)(?![\w.])")
PROCESS=re.compile(r"^(?:[pPtT]\d+)$")
SEVERITY={"critical":0,"major":1,"minor":2,"informational":3,"none":4}


def _atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=path.parent,
                                     suffix=".tmp",delete=False) as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
        tmp=Path(f.name)
    tmp.replace(path)


def _bbox(values):
    return [round(float(v),2) for v in values]


def _geometry(page):
    """Return coordinate-bearing word lines, preserving raw PDF token text.

    Sorting PDF words is not equivalent to reconstructing correct Hebrew
    sentences. Both visual orders are presented as hypotheses.
    """
    words=page.get_text("words",sort=False)
    groups=defaultdict(list)
    for raw in words:
        if len(raw)<8:continue
        x0,y0,x1,y1,token,block,line,word=raw[:8]
        token=str(token).strip()
        if token:
            groups[(int(block),int(line))].append({
                "text":token,"bbox":_bbox((x0,y0,x1,y1)),
                "word_index":int(word)})
    lines=[]
    for (block,line),tokens in groups.items():
        visual=sorted(tokens,key=lambda t:(t["bbox"][0],t["word_index"]))
        raw=sorted(tokens,key=lambda t:t["word_index"])
        heb=sum(len(HEBREW.findall(t["text"])) for t in tokens)
        lat=sum(len(LATIN.findall(t["text"])) for t in tokens)
        dominant="rtl" if heb>lat else "ltr" if lat>heb else "unknown"
        x0=min(t["bbox"][0] for t in tokens);x1=max(t["bbox"][2] for t in tokens)
        y0=min(t["bbox"][1] for t in tokens);y1=max(t["bbox"][3] for t in tokens)
        lines.append({
            "id":f"block-{block}-line-{line}",
            "bbox":_bbox((x0,y0,x1,y1)),
            "direction_candidate":dominant,
            "raw_pdf_order":" ".join(t["text"] for t in raw),
            "visual_ltr_candidate":" ".join(t["text"] for t in visual),
            "visual_rtl_candidate":" ".join(t["text"] for t in reversed(visual)),
            "tokens":raw,
            "status":"unverified_candidate",
        })
    return sorted(lines,key=lambda l:(l["bbox"][1],l["bbox"][0],l["id"]))


def _table_candidates(page):
    """Native vector table geometry only; no invented cell values."""
    try:
        result=page.find_tables()
        tables=getattr(result,"tables",[])
    except (AttributeError,ValueError,RuntimeError,TypeError):
        return [],"native_table_detection_unavailable"
    candidates=[]
    for idx,table in enumerate(tables):
        try:
            values=table.extract()
            bounds=_bbox(table.bbox)
        except (ValueError,RuntimeError,TypeError,AttributeError):
            continue
        if not isinstance(values,list) or not values:continue
        cells=[[cell if isinstance(cell,str) or cell is None else str(cell)
                for cell in (row or [])] for row in values]
        candidates.append({
            "id":f"table-{idx+1}","bbox":bounds,
            "rows":cells,"column_order":"visual_pdf_order_unverified",
            "status":"unverified_candidate",
            "source_method":"pymupdf_native_table_detection",
        })
    return candidates,"native_table_detection_attempted"


def _timeline_candidates(lines):
    """Associate nearby process labels and numeric ticks, never guess durations.

    A graphically grounded row-pair with >=2 numeric ticks and >=1 process
    label is a possible timeline. Tick-to-process assignment remains unknown.
    """
    rows=[]
    for line in lines:
        ticks=[]
        procs=[]
        for token in line["tokens"]:
            raw=token["text"].strip("()[],:;|")
            if re.fullmatch(r"\d+(?:\.\d+)?",raw):
                ticks.append({"text":raw,"bbox":token["bbox"]})
            if PROCESS.fullmatch(raw):
                procs.append({"text":raw,"bbox":token["bbox"]})
        rows.append({"id":line["id"],"bbox":line["bbox"],"ticks":ticks,
                     "processes":procs})
    found=[];seen=set()
    for timeline in rows:
        if len(timeline["ticks"])<2:continue
        ymid=sum(timeline["bbox"][1::2])/2
        for labels in rows:
            if labels["id"]==timeline["id"] or not labels["processes"]:continue
            labelmid=sum(labels["bbox"][1::2])/2
            # PDF coordinate units. Only propose geometrically nearby rows.
            if abs(ymid-labelmid)>54:continue
            key=(timeline["id"],labels["id"])
            if key in seen:continue
            seen.add(key)
            ticks=sorted(timeline["ticks"],key=lambda t:t["bbox"][0])
            try: nums=[float(t["text"]) for t in ticks]
            except ValueError:continue
            if not (all(b>=a for a,b in zip(nums,nums[1:])) or
                    all(b<=a for a,b in zip(nums,nums[1:]))):
                continue
            found.append({
                "id":f"timeline-{len(found)+1}",
                "time_row_id":timeline["id"],"process_row_id":labels["id"],
                "tick_candidates":ticks,
                "process_label_candidates":labels["processes"],
                "intervals":[],
                "interval_assignment_status":"not_inferred",
                "status":"unverified_candidate",
                "warning":"Times and process labels are nearby. This is NOT a verified Gantt chart or interval mapping.",
            })
    return found[:30]


def _issue_summary(report,source,page,expected_sha):
    if report is None:return []
    if report.get("schema_version")!="1.0" or not isinstance(report.get("pages"),list):
        raise ValueError("Unsupported Gemini audit report")
    matches=[r for r in report["pages"] if r.get("source")==source and r.get("page")==page]
    if len(matches)>1:raise ValueError("Duplicate audited page in report")
    if not matches:return []
    item=matches[0]
    if item.get("source_sha256")!=expected_sha:
        raise ValueError("Audit references a different source PDF SHA")
    if item.get("status") not in ("cached","audited"):
        return []
    issues=item.get("result",{}).get("issues",[])
    if not isinstance(issues,list):raise ValueError("Invalid Gemini issue list")
    return [{
        "category":str(i.get("category","other"))[:30],
        "visible_evidence":str(i.get("visible_evidence",""))[:600],
        "extraction_evidence":str(i.get("extraction_evidence",""))[:600],
        "confidence_claimed":str(i.get("confidence","unknown"))[:30],
        "verification":"ai_hypothesis_not_ground_truth",
    } for i in issues if isinstance(i,dict)]


def _page_record(page,extraction:str,metadata:dict,audit_report):
    lines=_geometry(page)
    tables,table_status=_table_candidates(page)
    timelines=_timeline_candidates(lines)
    gemini=_issue_summary(audit_report,metadata["source"],metadata["page"],metadata["source_sha256"])
    types=Counter(i["category"] for i in gemini)
    candidates=[l for l in lines if l["direction_candidate"]=="rtl" and
                l["visual_rtl_candidate"]!=l["visual_ltr_candidate"]]
    # A candidate is never an accepted replacement of SQLite page text.
    return {**metadata,
        "extraction_sha256":sha256(extraction.encode("utf-8")).hexdigest(),
        "original_extracted_text":extraction,
        "proposals":{
            "rtl_lines":candidates,
            "tables":tables,
            "table_detection_status":table_status,
            "timeline_candidates":timelines,
        },
        "gemini_issue_hypotheses":gemini,
        "counts":{"rtl_line_candidates":len(candidates),
                  "native_table_candidates":len(tables),
                  "timeline_candidates":len(timelines),
                  "gemini_issue_hypotheses":sum(types.values())},
        "status":"structural_evidence_unverified_no_database_mutation",
    }


def build_structural_recovery(store,source_dir:Path,destination:Path,*,
                              audit_report_path:Path|None=None,limit:int=7,
                              severity:str="critical")->dict:
    """Use original-PDF geometry + optional Gemini audit to generate candidates."""
    import pymupdf
    if not 1<=limit<=2140:raise ValueError("Limit must be 1..2140")
    if severity not in SEVERITY and severity!="all":raise ValueError("Invalid severity")
    root=Path(source_dir).resolve();out=Path(destination).resolve()
    if not root.is_dir():raise NotADirectoryError(root)
    audit=None
    if audit_report_path is not None:
        audit=json.loads(Path(audit_report_path).read_text(encoding="utf-8"))
    selected=[]
    for src in store.sources():
        if src["state"]!="active" or src["last_parsed_hash"]!=src["sha256"]:
            continue
        if src["ext"].lower()!=".pdf":continue
        for row in store.pages(src["source_id"]):
            flags=json.loads(row["flags"])
            level=classify(flags)
            if severity!="all" and level!=severity:continue
            selected.append(({
                "source_id":src["source_id"],
                "source":src["relative_path"],
                "source_sha256":src["sha256"],
                "page":int(row["page_no"]),
                "severity":level,
                "flags":flags,
                "backend":row["backend"],
            },row["body"]))
    selected.sort(key=lambda item:(SEVERITY[item[0]["severity"]],
                                  item[0]["source"],item[0]["page"]))
    selected=selected[:limit]
    if not selected:raise ValueError("No matching active PDF pages")
    docs={};hashes={};results=[]
    try:
        for meta,body in selected:
            src=(root/meta["source"]).resolve()
            if not src.is_relative_to(root) or not src.is_file():
                raise FileNotFoundError(f"Source PDF missing: {meta['source']}")
            if src not in hashes:hashes[src]=hash_file(src)
            if hashes[src]!=meta["source_sha256"]:
                raise ValueError(f"Source SHA changed: {meta['source']}")
            if src not in docs:docs[src]=pymupdf.open(src)
            pdf=docs[src]
            if not 1<=meta["page"]<=len(pdf):raise ValueError("PDF page out of bounds")
            results.append(_page_record(pdf[meta["page"]-1],body,meta,audit))
    finally:
        for pdf in docs.values():pdf.close()
    report={"schema_version":SCHEMA_VERSION,
            "status":"proposals_only_not_human_verified",
            "selected_pages":len(results),
            "source_root":str(root),
            "audit_report_used":audit is not None,
            "note":"No inferred text, table, or timeline is added to SQLite or exports. Candidate geometry requires source review.",
            "pages":results}
    _atomic_json(out/"STRUCTURAL_RECOVERY.json",report)
    sections=[]
    for item in results:
        name=html.escape(item["source"])
        counters=item["counts"]
        warnings="".join("<li>"+html.escape(i["category"])+": "+
            html.escape(i["visible_evidence"])+"</li>" for i in item["gemini_issue_hypotheses"])
        lines="".join("<li><code>"+html.escape(l["id"])+"</code> RTL: "+
            html.escape(l["visual_rtl_candidate"])+"</li>"
            for l in item["proposals"]["rtl_lines"][:12])
        sections.append("<section><h2>"+name+" — page "+str(item["page"])+"</h2>"+
            "<p>RTL line candidates: "+str(counters["rtl_line_candidates"])+
            "; native tables: "+str(counters["native_table_candidates"])+
            "; Gantt/timeline candidates: "+str(counters["timeline_candidates"])+
            "; AI hypotheses: "+str(counters["gemini_issue_hypotheses"])+
            "</p><h3>AI hypotheses (not verified)</h3><ul>"+warnings+
            "</ul><h3>Geometric RTL candidates (unverified)</h3><ul>"+lines+
            "</ul></section>")
    html_doc=("<!doctype html><html><head><meta charset='utf-8'>"+
       "<title>v0.11 structural evidence</title>"+
       "<style>body{font:15px system-ui;max-width:1100px;margin:2rem auto}"+
       "section{border:1px solid #bbb;padding:18px;margin:18px 0;border-radius:12px}"+
       "li{margin:.5rem 0}code{direction:ltr}</style></head><body>"+
       "<h1>Structural recovery — evidence only; NOT human verified</h1>"+
       "<p>Source PDF and extracted SQLite text remain unchanged. "+
       "Proposed RTL lines and graph associations are not accepted corrections.</p>"+
       "".join(sections)+"</body></html>")
    (out/"STRUCTURAL_RECOVERY.html").write_text(html_doc,encoding="utf-8")
    return {"selected_pages":len(results),
        "total_rtl_line_candidates":sum(p["counts"]["rtl_line_candidates"] for p in results),
        "total_native_table_candidates":sum(p["counts"]["native_table_candidates"] for p in results),
        "total_timeline_candidates":sum(p["counts"]["timeline_candidates"] for p in results),
        "total_ai_hypotheses":sum(p["counts"]["gemini_issue_hypotheses"] for p in results),
        "status":report["status"],"source_mutated":False}
