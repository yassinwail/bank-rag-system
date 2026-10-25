def chunk_text(pages: list[dict], source_name: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Splits page text into overlapping word-based chunks.
    Returns list of {"text": str, "source": str, "page": int} dicts.
    """
    chunks = []

    for page_data in pages:
        words = page_data["text"].split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append({
                "text": " ".join(chunk_words),
                "source": source_name,
                "page": page_data["page"],
            })
            start += chunk_size - overlap

    return chunks