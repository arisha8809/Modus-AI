"""
Vector store wrapper (ChromaDB, local + persistent, free/open-source).

This gives the knowledge base semantic search: once findings from many research
runs pile up, a user can ask a free-text follow-up question ("what have we
learned about demand forecasting?") and retrieve the most relevant findings
even if they don't share exact keywords. This is what makes the knowledge base
genuinely *reusable* across research runs, not just a per-run log.

Embeddings: deliberately NOT Chroma's default embedding function -- that
downloads an ONNX model from the internet on first use, which can fail (hash
mismatches, blocked hosts) on restricted networks, corporate proxies, or an
evaluator's machine, and would break the whole knowledge-base search feature
at the worst possible time (a live demo). Instead we use a scikit-learn
HashingVectorizer: a stateless, fixed-formula hashing scheme that turns text
into vectors with no training, no model file, and no network call ever. It's
weaker than a trained embedding model semantically, but it never breaks, and
combined with TF-IDF-style term weighting it's good enough for topical
similarity search over research findings.
"""

import os
import chromadb
from chromadb import EmbeddingFunction
from sklearn.feature_extraction.text import HashingVectorizer

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

_VECTOR_DIM = 384  # arbitrary fixed size, matches typical small embedding models
_hasher = HashingVectorizer(n_features=_VECTOR_DIM, alternate_sign=False, norm="l2")


class OfflineHashingEmbeddingFunction(EmbeddingFunction):
    """Fully offline embedding function -- no downloads, no external calls."""

    def __call__(self, input):
        vectors = _hasher.transform(input)
        return vectors.toarray().tolist()


_client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma"))
_collection = _client.get_or_create_collection(
    name="findings",
    embedding_function=OfflineHashingEmbeddingFunction(),
)


def add_finding(finding_id: int, text: str, metadata: dict):
    """Index a finding for semantic retrieval. Called right after a Finding
    row is written to SQLite, keeping both stores in sync."""
    _collection.upsert(
        ids=[str(finding_id)],
        documents=[text],
        metadatas=[metadata],
    )


def query_findings(query_text: str, n_results: int = 8, where: dict | None = None):
    """Semantic search over all indexed findings. Optionally filter by
    metadata (e.g. {'domain': 'retail'}) to scope the search."""
    results = _collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
    )
    return results
