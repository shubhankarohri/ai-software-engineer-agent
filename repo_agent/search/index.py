
import pickle
from pathlib import Path

import faiss
import numpy as np

from .chunker import CodeChunk


class CodeSearchIndex:

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: list[CodeChunk] = []

    def add(self, chunks: list[CodeChunk], embeddings: np.ndarray) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})"
            )

        # Force numpy array with exact dtype and memory layout FAISS expects
        embeddings = np.array(embeddings, dtype=np.float32)
        embeddings = np.ascontiguousarray(embeddings)

        self.index.add(embeddings)
        self.chunks.extend(chunks)
        print(f"  ✓ Added {len(chunks)} chunks. Total: {self.index.ntotal}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[dict]:

        if self.index.ntotal == 0:
            return []

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        scores, indices = self.index.search(
            query_embedding,
            top_k,
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            chunk = self.chunks[idx]

            results.append(
                {
                    "score": float(score),
                    "chunk_id": chunk.chunk_id,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name,
                    "parent_class": chunk.parent_class,
                    "module": chunk.module_name,
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "docstring": chunk.docstring,
                    "source_preview": chunk.source_code[:300],
                }
            )

        return results

    def save(
        self,
        directory: str = "data/indexes",
    ) -> None:
        Path(directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            f"{directory}/index.faiss",
        )

        with open(
            f"{directory}/chunks.pkl",
            "wb",
        ) as f:
            pickle.dump(self.chunks, f)

        print(f"  ✓ Index saved to {directory}/")

    def load(
        self,
        directory: str = "data/indexes",
    ) -> None:
        self.index = faiss.read_index(
            f"{directory}/index.faiss"
        )

        with open(
            f"{directory}/chunks.pkl",
            "rb",
        ) as f:
            self.chunks = pickle.load(f)

        print(
            f"  ✓ Index loaded. "
            f"{self.index.ntotal} vectors."
        )
