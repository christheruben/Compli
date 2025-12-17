import chromadb
client = chromadb.PersistentClient(path="gdpr_db")
col = client.get_collection("gdpr_chunks")
print(col.count())