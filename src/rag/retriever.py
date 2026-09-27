"""
Retriever
---------
Wraps a local FAISS vector index (loaded from S3/EFS at cold start in
production) and performs similarity search over document chunks.

In a real deployment:
  - The index is built offline by `scripts/build_index.py` from your
    knowledge base (PDFs, Confluence exports, S3 docs, etc.)
  - The index artifact is stored in S3 and pulled into /tmp (or mounted via
    EFS) on Lambda cold start.
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, index_path: str, top_k: int = 4):
        self.top_k = top_k
        self.embedder = SentenceTransformer(
            os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )

        self.index, self.metadata = self._load_index(index_path)

    def _load_index(self, index_path: str):
        """Loads a FAISS index + parallel metadata (text/source) from disk."""
        faiss_file = f"{index_path}.faiss"
        meta_file = f"{index_path}.meta.npy"

        if not os.path.exists(faiss_file):
            logger.warning("No index found at %s — retriever will return no results.", faiss_file)
            return None, []

        index = faiss.read_index(faiss_file)
        metadata = np.load(meta_file, allow_pickle=True).tolist()
        return index, metadata

    def retrieve(self, query: str) -> List[Dict]:
        if self.index is None:
            return []

        query_vec = self.embedder.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(np.array(query_vec, dtype="float32"), self.top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.metadata[idx]
            results.append(
                {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "score": float(score),
                }
            )
        return results
