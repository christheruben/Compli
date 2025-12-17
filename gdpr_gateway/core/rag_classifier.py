import chromadb
import json
import requests
import os
from gdpr_gateway.core.embeddings import embedder

"""RAG Classifier for GDPR special-category data explanations."""

# Get the directory where this file is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, 'gdpr_db')

# Connect to ChromaDB
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(
    name="gdpr_chunks",
    embedding_function=embedder
)

OLLAMA_URL = "http://localhost:11434/api/generate"

# Prompts for LLM
QUERY_TEMPLATE = """
You are an expert GDPR legal assistant.

You will receive a list of special-category detections and the user's text that triggered them.

Your task is to generate a SEARCH QUERY that will be used to retrieve the correct GDPR Articles and Recitals for explanation.

Detected categories: {categories}

User text:
\"\"\"{text}\"\"\"

Format your answer as STRICT JSON with this schema:

{{
  "query": "<short semantic search query referencing GDPR requirements>"
}}

Examples of good queries:
- "GDPR Article 9 health data processing restrictions"
- "GDPR obligations for processing political opinions"
- "GDPR recital health special category definition"

DO NOT explain. DO NOT add extra fields.
"""

def generate_rag_query(categories, text):
    payload = {
        "model": "mistral",
        "prompt": QUERY_TEMPLATE.format(categories=categories, text=text),
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    raw = response.json().get("response", "").strip()
    print("\n=== RAW Llama Response ===\n", raw, "\n")


    try:
        data = json.loads(raw)
        return data["query"]
    except:
        # fallback: extract JSON substring
        try:
            json_str = raw[raw.index("{"):raw.rindex("}")+1]
            data = json.loads(json_str)
            return data["query"]
        except:
            return "GDPR Article 9 special category data processing rules"
        
def retrieve_gdpr_chunks(query, top_k=4):
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    documents = results["documents"][0]
    ids = results["ids"][0]

    return [{"id": doc_id, "text": doc} for doc_id, doc in zip(ids, documents)]

def explain_with_rag(categories, user_text):
    # 1. Generate semantic query
    query = generate_rag_query(categories, user_text)

    # 2. Retrieve GDPR matches
    matches = retrieve_gdpr_chunks(query, top_k=4)

    # 3. Build explanation payload
    return {
        "triggered_categories": categories,
        "semantic_query": query,
        "matching_gdpr_sections": matches
    }

