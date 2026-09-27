"""
build_index.py
---------------
Offline utility to build the FAISS vector index consumed by the Lambda's
Retriever. Run this locally (or in a CI job) whenever the knowledge base
changes, then upload the resulting index files to S3.

Usage:
    python scripts/build_index.py --input docs/ --output index/faiss_index
"""

import argparse
import glob
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks


def main(input_dir: str, output_path: str):
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    all_chunks = []
    for filepath in glob.glob(os.path.join(input_dir, "**/*.txt"), recursive=True):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        for chunk in chunk_text(text):
            all_chunks.append({"text": chunk, "source": os.path.basename(filepath)})

    if not all_chunks:
        raise SystemExit(f"No .txt documents found under {input_dir}")

    print(f"Embedding {len(all_chunks)} chunks...")
    embeddings = embedder.encode(
        [c["text"] for c in all_chunks], normalize_embeddings=True
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype="float32"))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    faiss.write_index(index, f"{output_path}.faiss")
    np.save(f"{output_path}.meta.npy", np.array(all_chunks, dtype=object))

    print(f"Index written to {output_path}.faiss (+ .meta.npy)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory of .txt source docs")
    parser.add_argument("--output", required=True, help="Output path prefix for index files")
    args = parser.parse_args()
    main(args.input, args.output)
