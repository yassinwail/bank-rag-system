import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import chromadb
from app.docs_retrieval.pdf_extractor import extract_text_from_pdf
from app.docs_retrieval.chunker import chunk_text
from app.docs_retrieval.embedder import embed_texts

POLICY_DOCS_DIR = "data/policy_docs"
CHROMA_PATH = "data/chroma_store"
COLLECTION_NAME = "bank_policy"

def ingest_all_pdfs():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    pdf_files = [f for f in os.listdir(POLICY_DOCS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {POLICY_DOCS_DIR}")
        return

    for filename in pdf_files:
        path = os.path.join(POLICY_DOCS_DIR, filename)
        print(f"Processing {filename}...")

        pages = extract_text_from_pdf(path)
        chunks = chunk_text(pages, source_name=filename)

        if not chunks:
            print(f"  No text extracted from {filename}, skipping.")
            continue

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        ids = [f"{filename}_p{c['page']}_{i}" for i, c in enumerate(chunks)]
        metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"  Added {len(chunks)} chunks from {filename}")

    print(f"\nIngestion complete. Total chunks in collection: {collection.count()}")

if __name__ == "__main__":
    ingest_all_pdfs()