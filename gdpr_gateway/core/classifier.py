import re

"""Classifier module for detecting PII data using regex and spaCy NER."""
# Optional spaCy import + guarded model load so app won't crash at import time
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_ENABLED = True
    except Exception:
        nlp = None
        SPACY_ENABLED = False
except Exception:
    spacy = None
    nlp = None
    SPACY_ENABLED = False

"""Regular expressions for detecting various types of PII data."""
# ===========================
# Email Pattern
# ===========================
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# ===========================
# International Phone Number Pattern (GDPR Detection)
#
# Detects likely international and domestic phone numbers.
# Designed for GDPR/PII detection — not strict validation.
#
# Supported formats:
#   +1 415 555 2671
#   +44 20 7946 0958
#   +61 412 345 678
#   +49 (30) 901820
#   (415) 555-2671
#   415-555-2671
#   415 555 2671
#
# Characteristics:
#   - Optional leading +
#   - Allows spaces, dashes, parentheses
#   - Requires 7–15 total digits (E.164 compatible)
#   - Avoids matching long IDs or timestamps
#
# Not supported:
#   - Extensions (x123)
#   - Shortcodes (911, 112)
#   - Alphanumeric vanity numbers
# ===========================
PHONE_RE = re.compile(
    r"""
    (?<!\d)                              # no digit before

    (                                   # full phone number
        \+?\d{1,3}[\s\-\.]?              # optional country code
        (?:\(\d{1,4}\)|\d{1,4})?         # optional area code
        (?:[\s\-\.]?\d{2,4}){2,4}        # number groups
    )

    (?!\d)                              # no digit after
    """,
    re.VERBOSE
)




# ===========================
# Credit Card Patterns
# Visa, MasterCard, Amex generic
# ===========================
CREDIT_CARD_RE = re.compile(
    r"\b(?:\d[ -]*?){13,19}\b"
)

# ===========================
# IBAN (Basic validation)
# Starts with country code + 2 digits
# ===========================
IBAN_RE = re.compile(
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"
)

# ===========================
# IP Addresses
# ===========================
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b"
)

IPV6_RE = re.compile(
    r"\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b",
    re.IGNORECASE
)

# ===========================
# URL / Website detection
# ===========================
URL_RE = re.compile(
    r"\bhttps?://[^\s/$.?#].[^\s]*\b", re.IGNORECASE
)

# ===========================
# Dates — broad pattern
# ===========================
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE
)

# ===========================
# Generic Customer IDs
# Supports formats like:
#   CUST-1234
#   USER_82910
#   ID-998877
# ===========================
GENERIC_ID_RE = re.compile(
    r"\b(?:ID|CUST|USER|ACC)[-_]?\d{3,10}\b",
    re.IGNORECASE
)


# ==========================================================
# MAIN DETECTION FUNCTION
# ==========================================================

def detect_pii_regex(text: str):
    pii = {}

    patterns = {
        "email": EMAIL_RE,
        "phone": PHONE_RE,
        "credit_card": CREDIT_CARD_RE,
        "iban": IBAN_RE,
        "ipv4": IPV4_RE,
        "ipv6": IPV6_RE,
        "url": URL_RE,
        "date": DATE_RE,
        "customer_id": GENERIC_ID_RE
    }

    for key, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            pii[key] = matches

    return pii


def detect_pii_spacy(text: str):
    if not SPACY_ENABLED:
        return {}

    doc = nlp(text)

    entities = {
        "person": [],
        "org": [],
        "gpe": [],
        "loc": [],
        "date": []
    }

    skip_words = {"iban", "credit", "card", "visa", "mastercard"}

    for ent in doc.ents:
        label = ent.label_.lower()
        value = ent.text.strip()

        # --- 1. FILTER OUT BAD MATCHES ---
        # Remove IBAN mislabelled as ORG
        if value.lower() in skip_words:
            continue

        # Remove phone numbers misinterpreted as DATE
        if label == "date" and re.search(r"\d{2,} [\d\s]{2,}", value):
            continue

        # Remove single numbers incorrectly labeled DATE
        if label == "date" and value.isdigit():
            continue

        # Remove nonsense like "1111 1111"
        if label == "date" and len(value.replace(" ", "")) <= 4:
            continue

        # --- 2. ADD CLEAN LABELS ---
        if label in entities:
            entities[label].append(value)

    # --- 3. MERGE BROKEN PERSON NAMES ---
    entities["person"] = merge_person_names(entities["person"])

    # Remove empty lists
    cleaned = {k: v for k, v in entities.items() if v}

    return cleaned


def merge_person_names(names):
    """
    Merge split multi-word names such as:
    ["Mary-Anne van", "Merwe"] → ["Mary-Anne van Merwe"]
    """
    if not names:
        return []

    merged = []
    buffer = ""

    for name in names:
        # If the name ends with lowercase (e.g. 'van'),
        # it is likely part of a multi-word surname.
        if name.split()[-1].islower():
            buffer = (buffer + " " + name).strip()
        else:
            # Complete the buffer if building a surname
            if buffer:
                merged.append((buffer + " " + name).strip())
                buffer = ""
            else:
                merged.append(name)

    if buffer:
        merged.append(buffer)

    return merged

# Merged classifier function
def classify_text(text: str):
    regex_hits = detect_pii_regex(text)
    ner_hits = detect_pii_spacy(text)

    return {
        "regex": regex_hits,
        "ner": ner_hits
    }


