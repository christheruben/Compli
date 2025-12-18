from typing import List, Dict
from gdpr_gateway.core.rag_classifier import semantic_gdpr_lookup

# Tune once, then lock it
GDPR_DISTANCE_THRESHOLD = 0.30

def detect_gdpr_violations(text: str) -> List[Dict]:
    """
    Detect GDPR violations via vector similarity only.
    Deterministic. Fast. Auditable.
    """
    results = semantic_gdpr_lookup(text)

    violations = []

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, dists):
        if dist <= GDPR_DISTANCE_THRESHOLD:
            violations.append({
                "article": meta.get("article"),
                "category": meta.get("category"),
                "distance": round(dist, 3),
                "gdpr_text": doc
            })

    return violations
