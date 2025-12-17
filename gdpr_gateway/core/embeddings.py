from chromadb.utils import embedding_functions


# Load embedding model
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)