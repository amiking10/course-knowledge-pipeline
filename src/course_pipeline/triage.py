"""Explicit review severity. Severity is not a parser confidence score."""
from collections import Counter

SEVERITY_ORDER = {'critical': 0, 'major': 1, 'minor': 2, 'informational': 3}
SEVERITY = {
 'missing_numeric_evidence_review': 'critical',
 'probable_text_omission': 'major',
 'secondary_native_text_disagrees_review': 'major',
 'both_extractors_empty_visual_review': 'major',
 'replacement_characters': 'major',
 'page_count_mismatch': 'critical',
 'empty_document': 'critical',
 'visual_review_required': 'minor',
 'extractor_disagreement_ambiguous': 'minor',
 'empty_text': 'minor',
 'low_text_density': 'informational',
 'word_order_difference_informational': 'informational',
 'no_secondary_extractor_for_format': 'informational',
}
def classify(flags: list[str]) -> str:
    if not flags: return 'none'
    return min((SEVERITY.get(flag,'major') for flag in flags), key=SEVERITY_ORDER.__getitem__)

def summarize(problems: list[dict]) -> dict:
    counts=Counter(p['severity'] for p in problems)
    return {name: counts[name] for name in SEVERITY_ORDER}
