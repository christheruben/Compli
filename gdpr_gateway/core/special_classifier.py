import json
import requests
import time
import chromadb
import os

"""OPTIONAL
Must Run asynchronously
Classifies text for GDPR special categories using Llama 3 LLM. """

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT_TEMPLATE = """
You are a GDPR compliance classifier.

Your task is to determine whether the following text contains ANY GDPR special categories of personal data.

Special categories include:
- health data
- political opinions
- religious or philosophical beliefs
- sexual orientation
- biometric data
- genetic data
- trade union membership

TEXT TO ANALYZE:
\"\"\"{text}\"\"\"

Respond in STRICT JSON format only:

{{
  "health": true/false,
  "political": true/false,
  "religious": true/false,
  "sexual_orientation": true/false,
  "biometric": true/false,
  "genetic": true/false,
  "union": true/false
}}

Do NOT add explanations.
Do NOT add commentary.
ONLY return valid JSON.
"""

def detect_special_categories(text: str):
    prompt = PROMPT_TEMPLATE.format(text=text)

    start_time = time.time()
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    end_time = time.time()
    print(f"Llama 3 response time: {end_time - start_time:.2f} seconds")

    raw = response.json().get("response", "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: try extracting first {...} block
        try:
            json_str = raw[raw.index("{"): raw.rindex("}") + 1]
            data = json.loads(json_str)
        except:
            raise ValueError(f"Invalid JSON from Llama 3:\n{raw}")

    detected = [k for k, v in data.items() if v]

    return detected

def create_vector_store():
    vector_store_path  = "chroma_db"
    embedding = HuggingFaceEmbeddings(model_name = 'BAAI/bge-small-en-v1.5')

    if os.path.exists(vector_store_path):
        print('Loading existing vector store...')
        vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=embedding
        )
        return vector_store_path,
    print('Creating new vector store...')
    
    # Create chunking for text file
    