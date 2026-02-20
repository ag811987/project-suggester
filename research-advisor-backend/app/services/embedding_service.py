"""OpenAI embedding service for semantic search."""

import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 2048  # OpenAI supports up to 2048 inputs per request


class EmbeddingService:
    """Service for generating embeddings via OpenAI text-embedding-3-small."""

    def __init__(self, openai_client: AsyncOpenAI | None = None, api_key: str | None = None):
        """Initialize with optional client or API key."""
        self._client = openai_client
        if self._client is None:
            self._client = AsyncOpenAI(api_key=api_key)

    async def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            List of 1536 floats (embedding vector).
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("Cannot embed empty text")
        result = await self._client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return result.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts in a single API call (up to 2048 inputs).

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []
        # Filter empty texts and track indices for ordering
        non_empty = [(i, (t or "").strip()) for i, t in enumerate(texts)]
        valid = [(i, t) for i, t in non_empty if t]
        if not valid:
            raise ValueError("Cannot embed: all texts are empty")
        indices, clean_texts = zip(*valid, strict=True)
        response = await self._client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=list(clean_texts),
        )
        # Sort by original index; API returns in same order as input
        ordered = sorted(
            zip(indices, response.data, strict=True), key=lambda x: x[0]
        )
        return [d.embedding for _, d in ordered]
