"""Mixed-direction line candidates that preserve contiguous Latin runs.

The outer line is visually right-to-left. Within an RTL-dominant line,
English *word* runs have left-to-right ordering. Preserve original token boxes
and never normalize punctuation semantically without verification.
"""
from __future__ import annotations
import re

HEBREW=re.compile(r"[\u0590-\u05ff]")
LATIN=re.compile(r"^[A-Za-z][A-Za-z0-9_.+-]*$")

def fix_latin_runs_in_rtl_line(texts):
    """Reorder only adjacent unambiguous Latin word tokens within an RTL row.

    Input tokens are already right-to-left by their x-coordinates.
    A token containing punctuation is deliberately excluded, to avoid unsafe
    mutations of abbreviations, formula punctuation and parentheses.
    """
    tokens=list(texts);out=[];i=0
    while i<len(tokens):
        if LATIN.fullmatch(tokens[i]):
            j=i
            while j<len(tokens) and LATIN.fullmatch(tokens[j]):
                j+=1
            out.extend(reversed(tokens[i:j]))
            i=j
        else:
            out.append(tokens[i]);i+=1
    return out


def line_candidates(page):
    words=page.get_text("words",sort=False)
    grouped={}
    for word in words:
        if len(word)<8:continue
        x0,y0,x1,y1,txt,block,line,index=word[:8]
        token=str(txt).strip()
        if token:
            grouped.setdefault((int(block),int(line)),[]).append({
                "text":token,"bbox":[round(float(x),2) for x in (x0,y0,x1,y1)],
                "x":(x0+x1)/2,"index":int(index),
            })
    result=[]
    for (block,line),tokens in grouped.items():
        if not any(HEBREW.search(t["text"]) for t in tokens):continue
        rtl=sorted(tokens,key=lambda t:-t["x"])
        candidate=fix_latin_runs_in_rtl_line([t["text"] for t in rtl])
        raw=[t["text"] for t in sorted(tokens,key=lambda t:t["index"])]
        result.append({
            "line_id":f"{block}:{line}",
            "text_candidate":" ".join(candidate),
            "pdf_native_text":" ".join(raw),
            "source_boxes":[t["bbox"] for t in rtl],
            "status":"bilingual_visual_candidate_not_grammatically_verified",
        })
    return sorted(result,key=lambda x:x["line_id"])
