# rag_classifier.py
import chromadb
import os
from gdpr_gateway.core.embeddings import embedder

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "gdpr_db")

client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_or_create_collection(
    name="gdpr_chunks",
    embedding_function=embedder
)

def semantic_gdpr_lookup(text: str, top_k: int = 5):
    """
    Pure embedding-based GDPR similarity search.
    NO LLM.
    """
    return collection.query(
        query_texts=[text],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
