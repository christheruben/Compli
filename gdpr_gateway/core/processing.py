import os
import json
from datetime import datetime
from typing import Dict, List
import time

from gdpr_gateway.core import classifier
from gdpr_gateway.core.gdpr_semantic_classifier import detect_gdpr_violations

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
    gdpr_violations: List[Dict]
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

    # --- GDPR violations (prefix once) ---
    if gdpr_violations:
        articles = sorted({v.get("article") for v in gdpr_violations if v.get("article")})
        recitals = sorted({v.get("recital") for v in gdpr_violations if v.get("recital")})

        tags = []
        if articles:
            tags.append("Articles: " + ", ".join(articles))
        if recitals:
            tags.append("Recitals: " + ", ".join(recitals))

        prefix = "[GDPR_VIOLATION"
        if tags:
            prefix += " | " + " | ".join(tags)
        prefix += "]"

        masked = f"{prefix} {masked}"

    return masked


# ==========================================================
# MAIN PROCESSOR
# ==========================================================
def process_text(text: str) -> Dict:
    start_total = time.perf_counter()

    # --------------------------------------------------
    # 1. PII detection (regex + spaCy)
    # --------------------------------------------------
    t0 = time.perf_counter()
    regex_hits = classifier.detect_pii_regex(text)
    ner_hits = classifier.detect_pii_spacy(text)
    t_pii = time.perf_counter() - t0

    # --------------------------------------------------
    # 2. GDPR semantic detection (embedding-only)
    # --------------------------------------------------
    t0 = time.perf_counter()
    gdpr_violations = detect_gdpr_violations(text)
    t_semantic = time.perf_counter() - t0

    # --------------------------------------------------
    # 3. Blocking decision
    # --------------------------------------------------
    blocked = bool(regex_hits or ner_hits or gdpr_violations)

    # --------------------------------------------------
    # 4. Masking
    # --------------------------------------------------
    t0 = time.perf_counter()
    masked_text = mask_sensitive_text(
        text=text,
        regex_hits=regex_hits,
        ner_hits=ner_hits,
        gdpr_violations=gdpr_violations
    )
    t_masking = time.perf_counter() - t0

    # --------------------------------------------------
    # 5. Audit log (BLOCKING)
    # --------------------------------------------------
    t0 = time.perf_counter()
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "blocked" if blocked else "allowed",
        "original_text": text,
        "masked_text": masked_text,
        "regex_hits": regex_hits,
        "ner_hits": ner_hits,
        "gdpr_violations": gdpr_violations,
        "timings": {
            "pii_detection_ms": round(t_pii * 1000, 2),
            "semantic_detection_ms": round(t_semantic * 1000, 2),
            "masking_ms": round(t_masking * 1000, 2),
            "audit_log_ms": None  # filled below
        }
    }
    _write_audit_log(log_entry)
    t_audit = time.perf_counter() - t0
    log_entry["timings"]["audit_log_ms"] = round(t_audit * 1000, 2)

    total_time = time.perf_counter() - start_total

    # --------------------------------------------------
    # 6. API response
    # --------------------------------------------------
    return {
        "blocked": blocked,
        "masked_text": masked_text,
        "detections": {
            "regex": regex_hits,
            "ner": ner_hits,
            "gdpr_semantic": gdpr_violations
        },
        "timings": {
            "total_ms": round(total_time * 1000, 2),
            "pii_detection_ms": round(t_pii * 1000, 2),
            "semantic_detection_ms": round(t_semantic * 1000, 2),
            "masking_ms": round(t_masking * 1000, 2),
            "audit_log_ms": round(t_audit * 1000, 2)
        }
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
