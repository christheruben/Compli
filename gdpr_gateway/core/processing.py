import os
import json
from datetime import datetime
from typing import Dict, List

from gdpr_gateway.core import classifier
from gdpr_gateway.core import special_classifier
from gdpr_gateway.core import rag_classifier

# ==========================================================
# AUDIT LOG CONFIG
# ==========================================================

LOG_DIR = os.getenv("GDPR_AUDIT_DIR", "./logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "audit_log.jsonl")


# ==========================================================
# MASKING
# ==========================================================

def mask_sensitive_text(
    text: str,
    regex_hits: Dict[str, List[str]],
    ner_hits: Dict[str, List[str]],
    special_categories: List[str]
) -> str:
    """
    Inline masking of sensitive content using placeholders.
    """
    masked = text

    # --- Regex-based PII ---
    for pii_type, matches in regex_hits.items():
        for match in set(matches):
            masked = masked.replace(match, f"[{pii_type.upper()}]")

    # --- spaCy NER ---
    for ent_type, entities in ner_hits.items():
        for entity in set(entities):
            masked = masked.replace(entity, f"[{ent_type.upper()}]")

    # --- Special GDPR categories (prefix tags) ---
    for category in special_categories:
        tag = f"[SPECIAL_CATEGORY:{category.upper()}]"
        if tag not in masked:
            masked = f"{tag} {masked}"

    return masked


# ==========================================================
# MAIN PROCESSOR
# ==========================================================

def process_text(text: str) -> Dict:
    """
    Full GDPR processing pipeline.
    Returns a response object suitable for API output.
    """

    # --- 1. Classification ---
    regex_hits = classifier.detect_pii_regex(text)
    ner_hits = classifier.detect_pii_spacy(text)
    special_categories = special_classifier.detect_special_categories(text)

    has_sensitive_data = bool(regex_hits or ner_hits or special_categories)

    # --- 2. Masking ---
    masked_text = mask_sensitive_text(
        text=text,
        regex_hits=regex_hits,
        ner_hits=ner_hits,
        special_categories=special_categories
    )

    # --- 3. RAG Explanation (only if special categories detected) ---
    rag_info = {}
    if special_categories:
        rag_info = rag_classifier.explain_with_rag(
            special_categories,
            text
        )

    # --- 4. Audit Log ---
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "blocked" if has_sensitive_data else "allowed",
        "original_text": text,
        "masked_text": masked_text,
        "regex_hits": regex_hits,
        "ner_hits": ner_hits,
        "special_categories": special_categories,
        "rag_info": rag_info
    }

    _write_audit_log(log_entry)

    # --- 5. Response ---
    return {
        "blocked": has_sensitive_data,
        "masked_text": masked_text,
        "detections": {
            "regex": regex_hits,
            "ner": ner_hits,
            "special_categories": special_categories
        },
        "rag": rag_info
    }


# ==========================================================
# LOGGING
# ==========================================================

def _write_audit_log(entry: Dict):
    """
    Append-only audit logging.
    Rotation/retention can be added here later.
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
