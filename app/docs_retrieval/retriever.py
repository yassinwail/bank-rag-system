import chromadb
from app.docs_retrieval.embedder import embed_texts

CHROMA_PATH = "data/chroma_store"
COLLECTION_NAME = "bank_policy"

_client = None
_collection = None

def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection

def retrieve_relevant_chunks(question: str, top_k: int = 3) -> list[str]:
    collection = get_collection()
    query_embedding = embed_texts([question])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    return documents

def retrieve_chunks_with_sources(question: str, top_k: int = 3) -> list[dict]:
    collection = get_collection()
    query_embedding = embed_texts([question])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return [
        {"text": d, "source": m.get("source", "unknown"), "page": m.get("page", "?")}
        for d, m in zip(docs, metas)
    ]