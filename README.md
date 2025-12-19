# GDPR Compliance Gateway

A high-performance, blocking GDPR compliance gateway for text inputs.
This system prevents any sensitive or GDPR-violating data from being sent to downstream LLMs or APIs by performing local, deterministic audits before data leaves your environment.

Key functionality: 
❌ No OpenAI / external LLM calls occur unless the text is deemed GDPR-safe.

## 🚀 Features 

- ### ✅ Hard-blocking GDPR enforcement (no “best effort”)

- ### ⚡ Sub-second classification (embedding-only, no LLM dependency)

- ### 🔍 Multi-layer detection

       Regex PII detection

       spaCy Named Entity Recognition

       Semantic GDPR violation detection via embeddings

- ### 🧠 Semantic GDPR understanding

       Detects violations regex/NER can’t catch
       
       Embedding similarity against GDPR Articles & Recitals

- ### 📝 Append-only audit logging

- ### 🎭 Automatic masking of sensitive content#

- ### 📊 Built-in performance timing

- ### 🧱 Designed for enterprise & regulatory use#

## 🧠 Why This Exists

Most “GDPR filters”:

Rely on LLMs (too slow, too risky)

Only catch obvious PII

Allow data through with explanations later

## This system:

Stops violations before they happen

Uses semantic embeddings, not LLM reasoning

Produces deterministic, auditable decisions

Works offline

## 🧩 Architecture Overview
```
┌──────────────┐
│ User Input   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ 1. Regex PII Detection       │
│ 2. spaCy NER                 │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 3. GDPR Semantic Classifier  │
│    (Embedding-only, Chroma)  │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ 4. Block / Mask / Audit      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ SAFE OUTPUT OR HARD BLOCK    │
└──────────────────────────────┘
```
## 📁 Project Structure
```
frontend/
gdpr_gateway/
├── api/
│   └── app.py                    # FastAPI entrypoint
├── core/
│   ├── classifier.py             # Regex + spaCy PII detection
│   ├── gdpr_semantic_classifier.py
│   │                              # Embedding-only GDPR detection
│   ├── embeddings.py             # Shared embedding model
│   ├── gdpr_loader.py            # Builds GDPR ChromaDB
│   ├── processing.py             # Main blocking pipeline
│   └── rag_classifier.py         # (Optional) Explanation layer
├── data/
│   └── GDPR_regs.txt             # Raw GDPR text
├── gdpr_db/                      # Persistent ChromaDB
├── logs/
│   └── audit_log.jsonl           # Append-only audit log
└── README.md
```
## 🔍 Detection Layers Explained
- ### 1️⃣ Regex PII Detection (classifier.py)

Detects:

Emails

Phone numbers (international)

IP addresses

Credit cards

IBANs

Dates

Customer IDs

Fast, deterministic, zero ML latency

- ### 2️⃣ spaCy Named Entity Recognition

Detects:

PERSON

ORG

GPE

LOC

DATE

Used for contextual PII that regex cannot capture.

- ### 3️⃣ GDPR Semantic Classifier (Embedding-Only)

Uses BAAI/bge-small-en-v1.5

Compares user text embeddings against pre-embedded GDPR Articles & Recitals

No LLM calls

No hallucination

No external network traffic

Detects policy violations, not just entities:

Health data misuse

Genetic data processing

Political opinion handling

Religious belief storage

Employment discrimination risks

- ### 🧱 Blocking Logic

The system blocks if ANY of the following are true:

blocked = bool(
    regex_hits or
    ner_hits or
    gdpr_violations
)


There is no soft-allow mode.

- ### 🎭 Masking Behavior

Sensitive data is replaced inline:

John Smith → [PERSON]
john@email.com → [EMAIL]
+44 7911 123456 → [PHONE]


GDPR violations are prefixed:

[GDPR_VIOLATION | Articles: Article 9 | Recitals: Recital 51]

- ### 📝  Audit Logging

Every request is logged to:

logs/audit_log.jsonl


Each entry includes:

Timestamp

Action (blocked / allowed)

Original text

Masked text

All detections

Performance timings

Append-only by design for regulatory auditability.

## ⏱ Performance

Typical timings on CPU:

Stage	Time
Regex + spaCy	5–20 ms
Semantic GDPR	20–60 ms
Masking	<5 ms
Total	<100 ms

Compared to:

❌ LLM pipelines: 10–90 seconds

## ▶️ Running the Project
### 1️⃣ Install Dependencies
pip install fastapi uvicorn spacy chromadb sentence-transformers
python -m spacy download en_core_web_sm

### 2️⃣ Build GDPR Vector Database
python gdpr_gateway/core/gdpr_loader.py


This runs once and persists embeddings to disk.

### 3️⃣ Start the API
uvicorn gdpr_gateway.api.app:app --reload

###  4️⃣ Test Request
POST /process_prompt
```
{
  "text": "I am analyzing patient medical records including depression and genetic risks."
}
```

Response:
```
{
  "blocked": true,
  "masked_text": "[GDPR_VIOLATION | Articles: Article 9] I am analyzing patient medical records...",
  "detections": { ... },
  "timings": { ... }
}
```
## 🔐 Security & Privacy

- ❌ No cloud dependency

- ❌ No external LLM calls

- ❌ No raw data persistence beyond audit logs

- ✅ Fully offline-capable

- ✅ Deterministic behavior

- ✅ Auditor-friendly

## 🧪 Example Test Prompts

_Should block:_

We store employee medical histories and genetic markers to evaluate job performance.


_Should allow:_

Summarize GDPR Article 6 in simple terms.

## 🔮 Future Extensions

- ⏳ Audit log rotation & retention policies

- 🔐 Hash-based PII storage

- 📊 Risk scoring instead of binary blocking

- 🧠 Optional explanation LLM (post-block only)

- 🌍 Multilingual GDPR support

## 📜 License

Internal / Enterprise Use
Not legal advice.
Always consult qualified legal counsel for compliance decisions.
