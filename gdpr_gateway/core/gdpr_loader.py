import chromadb
import os
from chromadb.utils import embedding_functions
from core import embeddings
import re

"""Creates a ChromaDB database of GDPR text chunks for RAG classification
with both structural metadata (Article/Recital) and semantic metadata (spaCy)."""


# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data/GDPR_regs.txt")
DB_DIR = os.path.join(SCRIPT_DIR, "gdpr_db")


# ---------------------------------------------------------
# REGEX PATTERNS FOR STRUCTURAL DETECTION
# ---------------------------------------------------------
ARTICLE_RE = re.compile(r"(?m)^\s*Article\s+(\d+)\b", re.IGNORECASE)
RECITAL_RE = re.compile(r"(?m)^\s*Recital\s+(\d+)\b", re.IGNORECASE)


# ---------------------------------------------------------
# OPTIONAL spaCy LOADING
# ---------------------------------------------------------
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_ENABLED = True
    print("spaCy loaded successfully.")
except:
    nlp = None
    SPACY_ENABLED = False
    print("spaCy NOT available — semantic enrichment disabled.")


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def load_gdpr_text():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text, chunk_size=250, overlap=50):
    """Split into overlapping word chunks."""
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


def extract_structural_metadata(chunk):
    """Extract Article/Recital labels using regex."""
    article = None
    recital = None

    a = ARTICLE_RE.search(chunk)
    r = RECITAL_RE.search(chunk)

    if a:
        article = f"Article {a.group(1)}"
    if r:
        recital = f"Recital {r.group(1)}"

    return {
        "article": article,
        "recital": recital
    }

def sanitize_metadata(metadata: dict):
    """ChromaDB does not allow None values, so replace them with valid defaults."""
    clean = {}
    for key, value in metadata.items():
        if value is None:
            clean[key] = ""  # empty string is allowed
        else:
            clean[key] = value
    return clean



def extract_spacy_metadata(chunk):
    """
    Uses spaCy to detect:
      - named entities (PERSON, ORG, LAW, DATE, etc.)
      - key legal terms (controller, processor, consent, etc.)
      - sentence count
    Converts lists to strings for Chroma compatibility.
    """
    if not SPACY_ENABLED:
        return {
            "entities": None,
            "keywords": None,
            "sentence_count": None
        }

    doc = nlp(chunk)

    entities = [ent.text for ent in doc.ents]

    LEGAL_TERMS = {
        "controller", "processor", "data subject", "consent",
        "legitimate interest", "profiling", "supervisory authority",
        "personal data", "processing"
    }

    keywords = [
        token.text for token in doc 
        if token.lemma_.lower() in LEGAL_TERMS
    ]

    return {
        "entities": ", ".join(entities) if entities else None,
        "keywords": ", ".join(keywords) if keywords else None,
        "sentence_count": len(list(doc.sents))
    }



# ---------------------------------------------------------
# MAIN BUILD FUNCTION
# ---------------------------------------------------------

def build_gdpr_chroma_db():

    # Initialize DB
    client = chromadb.PersistentClient(path=DB_DIR)

    # Reset collection to avoid stale metadata
    existing = [c.name for c in client.list_collections()]
    if "gdpr_chunks" in existing:
        client.delete_collection("gdpr_chunks")

    collection = client.get_or_create_collection(
        name="gdpr_chunks",
        embedding_function=embeddings.embedder
    )

    # Load + chunk
    text = load_gdpr_text()
    chunks = chunk_text(text)
    print(f"Loaded {len(chunks)} chunks.")

    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        struct_meta = extract_structural_metadata(chunk)
        spacy_meta = extract_spacy_metadata(chunk)

        documents.append(chunk)

        metadata = {**struct_meta, **spacy_meta}
        metadata = sanitize_metadata(metadata)
        metadatas.append(metadata)

        
        ids.append(f"chunk_{i}")

    # Insert into DB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print("GDPR ChromaDB build complete with semantic metadata.")


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

if __name__ == "__main__":
    build_gdpr_chroma_db()
