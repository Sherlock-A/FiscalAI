"""
Moroccan address normalization engine.

Handles the non-trivial problem of matching addresses across:
  - French transliterations ("Hay Salam", "Hay Al Salam", "Hay Essalam")
  - Arabic script ("حي السلام")
  - Darija variants and abbreviations
  - Inconsistent ordering (number before/after street)
  - Common abbreviations (Av., Bd., Lot, Res., Douar, Qr.)

Output: a normalized string used for fuzzy matching and record linkage.
"""

import re
import unicodedata
from typing import Optional
from unidecode import unidecode

try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False


# ── Moroccan-specific normalization tables ────────────────────────────────────

# Common Arabic-origin words with variant French spellings
ARABIC_VARIANTS: dict[str, str] = {
    # neighborhood prefixes
    r"\bhay\b": "hay",
    r"\bhai\b": "hay",
    r"\bhay el\b": "hay",
    r"\bhai al\b": "hay",
    r"\bhai es\b": "hay",
    r"\bhayy\b": "hay",
    # street types
    r"\brue\b": "rue",
    r"\bavenue\b": "avenue",
    r"\bboulevard\b": "boulevard",
    r"\bbd\b": "boulevard",
    r"\bav\b": "avenue",
    r"\bave\b": "avenue",
    # settlement types
    r"\bdouar\b": "douar",
    r"\bdwâr\b": "douar",
    r"\bdwar\b": "douar",
    r"\bqartier\b": "quartier",
    r"\bqr\b": "quartier",
    r"\bquartier\b": "quartier",
    r"\blotissement\b": "lotissement",
    r"\blot\b": "lotissement",
    r"\blos\b": "lotissement",
    r"\bres\b": "residence",
    r"\brésidence\b": "residence",
    r"\bresidence\b": "residence",
    r"\bcite\b": "cite",
    r"\bcité\b": "cite",
    # Arabic definite article variants before sun/moon letters
    r"\b(el|al|es|er|en|ech|ej|ez|ed|et|en|el-|al-)\b": "",
    # common Moroccan toponym tokens
    r"\bsidi\b": "sidi",
    r"\bsid\b": "sidi",
    r"\bmoulay\b": "moulay",
    r"\bmy\b": "moulay",
    r"\boulad\b": "oulad",
    r"\boulad\b": "oulad",
    r"\bait\b": "ait",
    r"\bben\b": "ben",
    r"\bbni\b": "bni",
    r"\bbeni\b": "bni",
}

# Precompile patterns for performance
_COMPILED_VARIANTS = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in ARABIC_VARIANTS.items()]

# Whitespace / punctuation noise
_NOISE_RE = re.compile(r"[،,;:\.'\"\(\)\[\]{}/\\|@#\$%\^&\*\+\=`~<>]")
_MULTI_SPACE_RE = re.compile(r"\s{2,}")
_DIGIT_STREET_RE = re.compile(r"^(\d+)\s+(.+)$")   # "47 Hay Salam" → normalize ordering


def strip_diacritics(text: str) -> str:
    """Remove Arabic harakat (tashkeel) and French accents."""
    if HAS_PYARABIC:
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
    # Normalize unicode and remove combining marks
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def arabic_to_latin(text: str) -> str:
    """Transliterate Arabic script to Latin using unidecode."""
    return unidecode(text)


def normalize_address(raw: str | None) -> str | None:
    """
    Main entry point. Returns a normalized, lowercase ASCII string
    suitable for fuzzy matching.

    Examples:
        "Lot 47, Hay Es-Salam, Salé"   → "lotissement 47 hay salam sale"
        "حي السلام رقم 47 سلا"          → "hay alsalam 47 sla"
        "Qr. SALAM N°47 SALÉ"          → "quartier salam 47 sale"
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # 1. Strip Arabic diacritics, then transliterate Arabic script to Latin
    text = strip_diacritics(text)
    text = arabic_to_latin(text)

    # 2. Lower-case everything
    text = text.lower()

    # 3. Remove punctuation noise
    text = _NOISE_RE.sub(" ", text)

    # 4. Normalize "N° 47" → "47", "num 47" → "47"
    text = re.sub(r"\bn[°o]?\s*(\d+)", r"\1", text)
    text = re.sub(r"\bnum\b\.?\s*(\d+)", r"\1", text)

    # 5. Apply Moroccan variant normalization
    for pattern, replacement in _COMPILED_VARIANTS:
        text = pattern.sub(replacement, text)

    # 6. Standardize number position: "47 hay salam" → keep as-is (number first is fine)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()

    # 7. Remove single-character tokens (noise after normalization)
    tokens = [t for t in text.split() if len(t) > 1 or t.isdigit()]
    text = " ".join(tokens)

    return text or None


def address_similarity(a: str | None, b: str | None) -> float:
    """
    Returns a similarity score 0.0–1.0 between two normalized addresses.
    Uses token sort ratio (order-independent) for robustness.
    """
    if not a or not b:
        return 0.0
    try:
        from fuzzywuzzy import fuzz
        return fuzz.token_sort_ratio(a, b) / 100.0
    except ImportError:
        # Fallback: Jaccard similarity over token sets
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)


def batch_normalize(addresses: list[str | None]) -> list[str | None]:
    """Normalize a list of addresses efficiently."""
    return [normalize_address(addr) for addr in addresses]


# ── Utility: extract numeric part of address for spatial join fallback ────────

def extract_number(normalized: str | None) -> Optional[int]:
    """Extract the primary street/lot number from a normalized address."""
    if not normalized:
        return None
    match = re.search(r"\b(\d+)\b", normalized)
    return int(match.group(1)) if match else None
