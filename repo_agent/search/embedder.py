
import numpy as np
from sentence_transformers import SentenceTransformer
from .chunker import CodeChunk


MODEL_NAME = "all-MiniLM-L6-v2"


class CodeEmbedder:

    def __init__(self):
        print(f"  Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"  ✓ Model loaded. Embedding dimension: {self.dimension}")

    def embed_chunks(
        self,
        chunks: list[CodeChunk],
        batch_size: int = 64,
        show_progress: bool = True,
    ) -> np.ndarray:

        if not chunks:
            return np.array([])

        texts = [self._chunk_to_text(chunk) for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:

        embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.astype(np.float32)

    def _chunk_to_text(self, chunk: CodeChunk) -> str:

        parts = []

        if chunk.chunk_type == "method":
            parts.append(f"method {chunk.name} in class {chunk.parent_class}")
        elif chunk.chunk_type == "function":
            parts.append(f"function {chunk.name}")
        elif chunk.chunk_type == "class":
            parts.append(f"class {chunk.name}")

        if chunk.docstring:
            parts.append(chunk.docstring)

        parts.append(chunk.source_code)

        return "\n".join(parts)
