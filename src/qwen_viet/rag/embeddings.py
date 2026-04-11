"""Embedding wrapper for bge-m3 via sentence-transformers."""

from sentence_transformers import SentenceTransformer

from qwen_viet.config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """Get or initialise the singleton bge-m3 embedding model.

    Returns:
        Initialised SentenceTransformer instance.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model, device="cpu")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using bge-m3 (dense vectors only).

    Args:
        texts: Texts to embed.

    Returns:
        List of dense embedding vectors (1024-dim each).
    """
    model = get_embedder()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
