"""
Semantic cache: avoids paying for a new LLM generation when we've already
written a story for a near-identical situation recently.
"""

import os

import chromadb
from sentence_transformers import SentenceTransformer

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "rag", "chroma_db")
CACHE_COLLECTION_NAME = "marketsense_cache"

# How close two situations must be to count as a cache "hit". Distance is
# lower-is-more-similar (same idea as Step 4's RAG retrieval) - this is
# intentionally tight, since we only want near-identical repeats to hit,
# not just "vaguely related" stocks.
SIMILARITY_THRESHOLD = 0.05

_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path=CACHE_DIR)


def _situation_key(mover: dict) -> str:
    """Describes this mover's situation as text, rounded so near-identical moves collide."""
    rounded_pct = round(mover["pct_change"] * 2) / 2  # rounds to the nearest 0.5
    return f"{mover['ticker']} price change {rounded_pct}%"


def get_cached_story(mover: dict) -> str | None:
    """Returns a cached story for a near-identical past situation, or None if no hit."""
    collection = _client.get_or_create_collection(name=CACHE_COLLECTION_NAME)

    if collection.count() == 0:
        return None

    key_text = _situation_key(mover)
    query_embedding = _embedding_model.encode([key_text]).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=1)

    if not results["documents"][0]:
        return None

    distance = results["distances"][0][0]
    if distance <= SIMILARITY_THRESHOLD:
        return results["documents"][0][0]

    return None


def store_in_cache(mover: dict, story: str) -> None:
    """Saves a generated story so a future near-identical situation can reuse it."""
    collection = _client.get_or_create_collection(name=CACHE_COLLECTION_NAME)

    key_text = _situation_key(mover)
    embedding = _embedding_model.encode([key_text]).tolist()

    collection.upsert(
        ids=[key_text],
        embeddings=embedding,
        documents=[story],
    )
