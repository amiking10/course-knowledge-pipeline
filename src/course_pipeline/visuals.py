"""Create visual inspection images for pages, without OCR or invented descriptions."""
from __future__ import annotations
from pathlib import Path
import json


def render_review(source_pdf: Path, pages: list[int], output: Path, dpi: int = 120) -> dict:
    import fitz
    if not 72 <= dpi <= 240:
        raise ValueError('DPI must be between 72 and 240')
    source_pdf = Path(source_pdf)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = []
    with fitz.open(source_pdf) as pdf:
        for page in sorted(set(pages)):
            if page < 1 or page > len(pdf):
                raise ValueError(f'Page {page} outside source range 1..{len(pdf)}')
            name=f'page-{page:04d}.png'
            pdf[page-1].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72), alpha=False).save(output/name)
            artifacts.append({'page':page, 'image':name})
    manifest={'source':source_pdf.name,'dpi':dpi,'artifacts':artifacts}
    (output/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest
