"""Read-only checks of an AI-ready export against its current local SQLite index.

Passing this gate means the files are complete and traceable; it does NOT
establish that OCR, tables, visual diagrams, or answers are correct.
"""
from __future__ import annotations

import json
from pathlib import Path


def verify_export(store, export_dir: Path, *, require_visuals: bool = False) -> dict:
    root = Path(export_dir)
    errors: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        return {"passed": False, "errors": [f"Export directory missing: {root}"],
                "warnings": [], "sources": 0, "bundles": 0,
                "status": "package_integrity_only_not_content_accuracy"}
    manifest_path = root / "manifest.json"
    try:
        manifests = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifests, list):
            raise ValueError("Expected a list")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"passed": False, "errors": [f"Invalid manifest.json: {exc}"],
                "warnings": [], "sources": 0, "bundles": 0,
                "status": "package_integrity_only_not_content_accuracy"}
    active = {s["source_id"]: s for s in store.sources()
              if s["state"] == "active" and s["last_parsed_hash"] == s["sha256"]}
    manifest_ids: set[str] = set()
    for item in manifests:
        if not isinstance(item, dict):
            errors.append("Manifest contains a non-object source"); continue
        sid = item.get("source_id")
        if not isinstance(sid, str) or sid in manifest_ids:
            errors.append("Invalid or duplicate manifest source ID"); continue
        manifest_ids.add(sid)
        source = active.get(sid)
        if source is None:
            errors.append(f"Manifest source is no longer an active parsed source: {sid}")
            continue
        if (item.get("source_path") != source["relative_path"] or
                item.get("source_sha256") != source["sha256"] or
                item.get("pages") != len(store.pages(sid)) or
                item.get("backend") != source["last_backend"]):
            errors.append(f"Stale source metadata or page count: {source['relative_path']}")
    if manifest_ids != set(active):
        errors.append("Export manifest does not match currently parsed active sources")
    bundles = sorted(root.glob("course_sources_*.md"))
    if not bundles or not manifests:
        errors.append("No source bundles or no parsed sources available for study")
    index = root / "INDEX.md"
    if not index.is_file():
        errors.append("INDEX.md missing")
    else:
        text = index.read_text(encoding="utf-8")
        for entry in manifests:
            if isinstance(entry, dict) and isinstance(entry.get("source_path"), str):
                if entry["source_path"] not in text:
                    errors.append(f"Index missing source: {entry['source_path']}")
    # Require source+original page provenance in exported text, not just a directory listing.
    # Stream only provenance headers instead of joining entire lecture corpora.
    headings = set()
    for file in bundles:
        with file.open(encoding="utf-8") as stream:
            for line in stream:
                if line.startswith("## Source: "):
                    headings.add(line.rstrip("\r\n"))
    for entry in manifests:
        if not isinstance(entry, dict): continue
        sid = entry.get("source_id")
        if sid not in active or not isinstance(entry.get("source_path"), str): continue
        for page in store.pages(sid):
            heading = (f"## Source: {entry['source_path']} | page "
                       f"{page['page_no']} | id {sid}")
            if heading not in headings:
                errors.append(f"Missing exported source/page heading: {entry['source_path']}:"
                              f"{page['page_no']}")
    archive = root / "course_original_visuals.pdf"
    if not archive.exists():
        (errors if require_visuals else warnings).append(
            "Original visual PDF archive missing; figures and equations may be unavailable")
    else:
        try:
            import pymupdf
            with pymupdf.open(archive) as doc:
                actual_pages = len(doc)
            pdf_manifest = archive.with_suffix(".manifest.json")
            if not pdf_manifest.is_file():
                errors.append("Visual PDF source-page mapping manifest is missing")
            else:
                mapping = json.loads(pdf_manifest.read_text(encoding="utf-8"))
                if mapping.get("total_pages") != actual_pages:
                    errors.append("Visual PDF page count does not match its mapping")
                for source in mapping.get("sources", []):
                    sid = source.get("source_id")
                    if sid not in active or source.get("source_sha256") != active[sid]["sha256"]:
                        errors.append(f"Visual PDF mapping references stale source: {sid}")
        except ImportError:
            warnings.append("Cannot inspect visual archive: install the [inspect] extra")
        except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
            errors.append(f"Cannot validate visual PDF: {exc}")
    qa = root / "QUALITY_REPORT.json"
    if not qa.is_file():
        warnings.append("QUALITY_REPORT.json absent; run the full pipeline for QA diagnostics")
    else:
        try:
            report = json.loads(qa.read_text(encoding="utf-8"))
            if report.get("flagged_pages", 0):
                warnings.append(f"{report['flagged_pages']} pages carry unresolved extraction warnings")
        except (OSError, json.JSONDecodeError, ValueError):
            errors.append("QUALITY_REPORT.json is invalid")
    if any(s["state"] == "active" and s["last_parsed_hash"] != s["sha256"]
           for s in store.sources()):
        errors.append("Database contains active sources not yet parsed for current SHA")
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "sources": len(manifests),
        "bundles": len(bundles),
        "visual_pdf_present": archive.exists(),
        "status": "package_integrity_only_not_content_accuracy",
        "next_step": ("Fix package integrity errors before uploading"
                      if errors else
                      "Upload Markdown bundles, original visual PDF and index; "
                      "retain the SQLite database locally"),
    }
