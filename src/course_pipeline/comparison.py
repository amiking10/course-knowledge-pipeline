"""Deterministic Unicode-aware comparison. Differences are never auto-verified."""
from collections import Counter
from dataclasses import dataclass
import re
import unicodedata

TOKEN = re.compile(r'[^\W_]+', re.UNICODE)
NUMERIC = re.compile(r'\d+(?:[.,]\d+)*')

def tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize('NFKC', text)
    normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Cf')
    return [t.casefold() for t in TOKEN.findall(normalized)]

@dataclass(frozen=True)
class Comparison:
    primary_tokens: int
    secondary_tokens: int
    missing_tokens: int
    missing_fraction: float
    new_numeric_tokens: tuple[str, ...]
    order_only: bool
    probable_omission: bool
    ambiguous: bool

def compare(primary: str, secondary: str, *, min_secondary: int = 140,
            min_novel_tokens: int = 3, missing_fraction_threshold: float = 0.30) -> Comparison:
    p, s = tokens(primary), tokens(secondary)
    additional = Counter(s) - Counter(p)
    missing = sum(additional.values())
    fraction = missing / max(len(s), 1)
    new_numbers = tuple(sorted(set(NUMERIC.findall(' '.join(s))) - set(NUMERIC.findall(' '.join(p)))))
    order_only = bool(p and s and Counter(p) == Counter(s) and p != s)
    length_gap = len(secondary.strip()) >= min_secondary and len(primary.strip()) < 0.30 * len(secondary.strip())
    probable = bool(s and (
        not p or
        (len(s) >= min_novel_tokens and missing >= min_novel_tokens and fraction >= missing_fraction_threshold
         and (length_gap or missing >= 6 or bool(new_numbers)))
    ))
    ambiguous = bool(p and s and not probable and not order_only and
                     (length_gap or (missing >= 3 and fraction >= missing_fraction_threshold)))
    return Comparison(len(p), len(s), missing, round(fraction, 4), new_numbers,
                      order_only, probable, ambiguous)
