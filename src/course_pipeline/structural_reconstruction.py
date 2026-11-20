"""v0.11.1: source-grounded *candidate* reconstruction for bilingual scheduling slides.

No model inference, no DB mutation, and no automatic promotion to trusted content.
Every table cell and Gantt interval must retain source PDF bounding-box evidence.
"""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import re
import tempfile
from .core import hash_file

PROC=re.compile(r"(?i)^[pt]\d+$")
NUM=re.compile(r"^\d+(?:\.\d+)?$")
HEBREW=re.compile("[\u0590-\u05ff]")
MAX_PAGES=500

def _tokens(page):
    rows=[]
    for w in page.get_text("words",sort=False):
        if len(w)<8:continue
        x0,y0,x1,y1,value,block,line,idx=w[:8]
        value=str(value).strip()
        if value:
            rows.append({"text":value,"box":[round(float(x),2) for x in (x0,y0,x1,y1)],
                         "x":(x0+x1)/2,"y":(y0+y1)/2,
                         "block":int(block),"line":int(line),"index":int(idx)})
    return rows

def _rtl_paragraphs(tokens):
    """Retain native line order; recover only well-supported RTL run candidates.

    Mixed Hebrew/English punctuation is *never* automatically normalized.
    """
    groups={}
    for t in tokens:groups.setdefault((t["block"],t["line"]),[]).append(t)
    result=[]
    for (block,line),group in sorted(groups.items()):
        heb=sum(len(HEBREW.findall(t["text"])) for t in group)
        if heb<2:continue
        raw=sorted(group,key=lambda t:t["index"])
        rtl=sorted(group,key=lambda t:-t["x"])
        text=" ".join(t["text"] for t in rtl)
        source=" ".join(t["text"] for t in raw)
        result.append({"line_id":f"{block}:{line}","text_candidate":text,
            "native_word_order":source,"source_boxes":[t["box"] for t in rtl],
            "contains_latin":bool(re.search("[A-Za-z]",text)),
            "status":"geometry_only_not_verified",
            "note":"Whole-word RTL reconstruction; punctuation and bidi semantics may require verification."})
    return result

def _aligned_tables(tokens, *, tol=18):
    """Find borderless scheduling table *candidates* from aligned pN rows.

    Column semantics use observed headings only; never infer meaning from a
    numeric column without a heading. Require >=2 labeled process rows.
    """
    groups={}
    for t in tokens:
        key=(t["block"],t["line"])
        groups.setdefault(key,[]).append(t)
    process_cells=[]
    for group in groups.values():
        for t in group:
            if PROC.fullmatch(t["text"].strip("():;")):
                process_cells.append(t)
    # An explicitly present header 'תהליך' is necessary, guarding Gantt labels.
    headers=[t for t in tokens if t["text"].strip(":")=="תהליך"]
    if not headers:return []
    results=[]
    for head in headers:
        candidates=[p for p in process_cells
             if abs(p["x"]-head["x"])<=tol and head["y"]<p["y"]<=head["y"]+250]
        candidates.sort(key=lambda t:t["y"])
        if len(candidates)<2:continue
        # A numeric entry is assigned only when its y-coordinate matches
        # exactly one process row and its x-column is stable across rows.
        rows=[]
        for p in candidates:
            numeric=[t for t in tokens if NUM.fullmatch(t["text"])
                and abs(t["y"]-p["y"])<=9 and abs(t["x"]-p["x"])>tol
                and 0<t["x"]<head["x"]+220]
            rows.append({"process":p["text"],"process_bbox":p["box"],
                "numeric_cells":[{"value":t["text"],"bbox":t["box"],
                                  "x":round(t["x"],2)} for t in sorted(numeric,key=lambda t:t["x"])]})
        # Only stable columns supported on >=2 rows are accepted as columns.
        cols=[]
        positions=sorted([c["x"] for row in rows for c in row["numeric_cells"]])
        while positions:
            seed=positions.pop(0);cluster=[seed]
            keep=[]
            for x in positions:
                (cluster if abs(x-seed)<=tol else keep).append(x)
            positions=keep
            if len(cluster)>=2:cols.append(round(sum(cluster)/len(cluster),2))
        if not cols:continue
        # Match explicit native PDF column headers to numeric column centres.
        # The Hebrew two-word header "זמן ריצה" spans the numeric column.
        header_words=[t for t in tokens if abs(t["y"]-head["y"])<=12]
        semantic_columns=[]
        for center in cols:
            nearby=[t["text"].strip(":") for t in header_words if abs(t["x"]-center)<=26]
            if "זמן" in nearby and "ריצה" in nearby:
                semantic_columns.append("run_time")
            elif "הגעה" in nearby:
                semantic_columns.append("arrival")
            else:
                semantic_columns.append(None)
        compact=[]
        for row in rows:
            cells=[]
            for center in cols:
                matches=[c for c in row["numeric_cells"] if abs(c["x"]-center)<=tol]
                cells.append(matches[0] if len(matches)==1 else None)
            compact.append({"process":row["process"],"process_bbox":row["process_bbox"],"cells":cells})
        results.append({"heading_bbox":head["box"],"column_centers":cols,
            "rows":compact,"status":"borderless_table_candidate",
            "column_semantics":semantic_columns,
            "semantics_status":"header_alignment_candidate_not_verified"})
    # Deduplicate tables with same process header.
    seen=set();unique=[]
    for r in results:
        key=tuple(r["heading_bbox"])
        if key not in seen:unique.append(r);seen.add(key)
    return unique

def _gantt_candidates(tokens, *, y_delta=55):
    """Recover tentative time-axis associations from geometry.

    Requires >=3 monotonically ordered ticks, >=2 process labels in a
    nearby band, and overlap of label centers with the timeline span.
    This does NOT assume every adjacent pair corresponds to a process.
    """
    groups={}
    for t in tokens:
        groups.setdefault((t["block"],t["line"]),[]).append(t)
    tick_lines=[]
    label_lines=[]
    for key,group in groups.items():
        ticks=sorted((t for t in group if NUM.fullmatch(t["text"])),key=lambda t:t["x"])
        labels=sorted((t for t in group if PROC.fullmatch(t["text"])),key=lambda t:t["x"])
        if len(ticks)>=3:
            vals=[float(t["text"]) for t in ticks]
            if all(b>a for a,b in zip(vals,vals[1:])):
                tick_lines.append((key,ticks))
        if len(labels)>=2:label_lines.append((key,labels))
    candidates=[]
    seen=set()
    for _,ticks in tick_lines:
        for _,labels in label_lines:
            ygap=abs(sum(t["y"] for t in labels)/len(labels)-sum(t["y"] for t in ticks)/len(ticks))
            if not 7<=ygap<=y_delta:continue
            if not all(ticks[0]["x"]-25<=p["x"]<=ticks[-1]["x"]+25 for p in labels):continue
            key=(tuple(t["text"] for t in ticks),tuple(p["text"] for p in labels),
                 round(ticks[0]["y"]),round(labels[0]["y"]))
            if key in seen:continue
            seen.add(key)
            # A process label is between boundary ticks, but its extent
            # may overlap other segments; don't invent unobserved blocks.
            spans=[]
            for p in labels:
                matching=[(a,b) for a,b in zip(ticks,ticks[1:])
                          if a["x"]<=p["x"]<=b["x"]]
                if len(matching)!=1:continue
                a,b=matching[0]
                spans.append({"process":p["text"],"start":float(a["text"]),
                    "end":float(b["text"]),
                    "process_bbox":p["box"],"start_tick_bbox":a["box"],
                    "end_tick_bbox":b["box"],
                    "status":"proposed_from_label_position_not_verified"})
            candidates.append({"ticks":[{"value":t["text"],"bbox":t["box"]} for t in ticks],
                 "labels":[{"value":t["text"],"bbox":t["box"]} for t in labels],
                 "segments":spans,"status":"geometric_hypothesis",
                 "warning":"Text positions alone do not prove Gantt block boundaries."})
    return candidates[:30]

def _consistency(tables,gantts):
    """Check mathematical invariants; no claim of ground-truth agreement."""
    checks=[]
    for g in gantts:
        for seg in g["segments"]:
            checks.append({"kind":"interval_positive","process":seg["process"],
                 "passed":seg["end"]>seg["start"],
                 "value":seg["end"]-seg["start"]})
        for table in tables:
            # Do not compare to an unidentified numeric column.
            checks.append({"kind":"table_to_timeline_consistency",
                "passed":None,"reason":"table numeric column semantics not established"})
    return checks

def reconstruct_report(store,source_dir:Path,old_report:Path,out_dir:Path,*,limit:int=7):
    import pymupdf
    if not 1<=limit<=MAX_PAGES:raise ValueError("Invalid page limit")
    source_dir=Path(source_dir).resolve();out_dir=Path(out_dir)
    report=json.loads(Path(old_report).read_text(encoding="utf-8"))
    if report.get("schema_version")!="0.11.0" or not isinstance(report.get("pages"),list):
        raise ValueError("Expected v0.11 structural recovery report")
    items=[];docs={};hashes={}
    try:
        for old in report["pages"][:limit]:
            path=(source_dir/old["source"]).resolve()
            if not path.is_relative_to(source_dir) or not path.is_file():
                raise FileNotFoundError(f"Source missing: {old['source']}")
            if path not in hashes:hashes[path]=hash_file(path)
            if hashes[path]!=old["source_sha256"]:raise ValueError("Original PDF SHA mismatch")
            row=store.conn.execute("SELECT s.sha256,s.state,s.last_parsed_hash,p.body FROM sources s JOIN pages p ON s.source_id=p.source_id WHERE s.source_id=? AND p.page_no=?",
                 (old["source_id"],old["page"])).fetchone()
            if row is None or row["sha256"]!=old["source_sha256"] or row["state"]!="active" or row["last_parsed_hash"]!=row["sha256"]:
                raise ValueError("Stale or missing SQLite source")
            if hashlib.sha256(row["body"].encode("utf-8")).hexdigest()!=old["extraction_sha256"]:
                raise ValueError("SQLite extraction changed since v0.11 report")
            if path not in docs:docs[path]=pymupdf.open(path)
            page=docs[path][int(old["page"])-1]
            tokens=_tokens(page)
            rtl=_rtl_paragraphs(tokens);tables=_aligned_tables(tokens);gantts=_gantt_candidates(tokens)
            items.append({"source":old["source"],"page":old["page"],
               "source_sha256":old["source_sha256"],"extraction_sha256":old["extraction_sha256"],
               "rtl_lines":rtl,"borderless_table_candidates":tables,
               "gantt_candidates":gantts,"consistency_checks":_consistency(tables,gantts),
               "status":"evidence_candidates_not_automatically_accepted"})
    finally:
        for doc in docs.values():doc.close()
    data={"schema_version":"0.11.1","page_count":len(items),
          "status":"unverified_structural_candidates",
          "note":"Read-only: neither PDF nor SQLite has been modified; no verified accuracy claim.",
          "pages":items}
    out_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf8",dir=out_dir,delete=False) as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        temp=Path(f.name)
    temp.replace(out_dir/"STRUCTURAL_RECONSTRUCTION.json")
    sections=[]
    for item in items:
        summaries=(f"RTL lines {len(item['rtl_lines'])}, borderless tables "+
                   f"{len(item['borderless_table_candidates'])}, Gantt candidates {len(item['gantt_candidates'])}")
        sections.append("<section><h2>"+html.escape(item["source"])+
            " — page "+str(item["page"])+"</h2><p>"+html.escape(summaries)+
            "</p><p>All results are unverified suggestions grounded in PDF text coordinates.</p></section>")
    (out_dir/"STRUCTURAL_RECONSTRUCTION.html").write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Structural Reconstruction</title></head>"+
        "<body><h1>v0.11.1 Structural reconstruction — candidates only</h1>"+
        "".join(sections)+"</body></html>",encoding="utf8")
    return {"page_count":len(items),
            "rtl_lines":sum(len(p["rtl_lines"]) for p in items),
            "borderless_table_candidates":sum(len(p["borderless_table_candidates"]) for p in items),
            "gantt_candidates":sum(len(p["gantt_candidates"]) for p in items),
            "status":data["status"],"sources_modified":False}
