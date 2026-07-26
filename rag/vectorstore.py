"""
Embeds knowledge base chunks and stores them in ChromaDB for similarity search.
"""

import os

import chromadb
from sentence_transformers import SentenceTransformer

from rag.chunk import chunk_all_documents

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "marketsense_knowledge"

_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path=CHROMA_DIR)


def build_vectorstore() -> None:
    """Embeds every knowledge base chunk and stores it in ChromaDB."""
    chunks = chunk_all_documents()

    collection = _client.get_or_create_collection(name=COLLECTION_NAME)

    texts = [chunk["text"] for chunk in chunks]
    embeddings = _embedding_model.encode(texts).tolist()
    ids = [chunk["chunk_id"] for chunk in chunks]
    metadatas = [{"source": chunk["source"]} for chunk in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB collection '{COLLECTION_NAME}'.")


def query_vectorstore(query: str, n_results: int = 3) -> list[dict]:
    """Finds the chunks most similar in meaning to the query."""
    collection = _client.get_or_create_collection(name=COLLECTION_NAME)

    query_embedding = _embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )

    matches = []
    for text, distance, metadata in zip(
        results["documents"][0], results["distances"][0], results["metadatas"][0]
    ):
        matches.append({
            "text": text,
            "distance": distance,
            "source": metadata["source"],
        })

    return matches


if __name__ == "__main__":
    build_vectorstore()

    query = "why do small companies move more than big companies"
    print(f"\nQuery: '{query}'")
    for match in query_vectorstore(query):
        print(f"  [{match['source']}] distance={match['distance']:.3f}")
        print(f"  {match['text'][:100]}...\n")
