"""
Splits raw knowledge base documents into chunks for embedding.

We chunk by paragraph (splitting on blank lines) rather than a fixed
character count. Each paragraph in our source docs already represents
one complete idea, so splitting there keeps each chunk coherent instead
of cutting a sentence in half.
"""

import os

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")


def load_documents() -> dict[str, str]:
    """Reads every .txt file in knowledge_base/. Returns {filename: full_text}."""
    documents = {}

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            documents[filename] = f.read()

    return documents


def chunk_text(text: str) -> list[str]:
    """
    Splits one document's text into paragraph-level chunks.
    A short heading-like paragraph (few words, no ending period) is merged
    into the paragraph that follows it, so no chunk is just a bare title.
    """
    raw_paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    chunks = []
    pending_heading = None

    for paragraph in paragraphs:
        looks_like_heading = len(paragraph.split()) <= 6 and not paragraph.endswith(".")

        if looks_like_heading:
            pending_heading = paragraph
            continue

        if pending_heading:
            chunks.append(f"{pending_heading}\n{paragraph}")
            pending_heading = None
        else:
            chunks.append(paragraph)

    if pending_heading:
        # File ended with a heading and nothing after it - keep it rather than lose it.
        chunks.append(pending_heading)

    return chunks


def chunk_all_documents() -> list[dict]:
    """Loads and chunks every document, tagging each chunk with its source."""
    documents = load_documents()
    all_chunks = []

    for filename, text in documents.items():
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": filename,
                "chunk_id": f"{filename}-{i}",
            })

    return all_chunks


if __name__ == "__main__":
    chunks = chunk_all_documents()
    print(f"Total chunks: {len(chunks)}\n")
    for chunk in chunks:
        print(f"[{chunk['chunk_id']}]")
        print(chunk["text"])
        print()
