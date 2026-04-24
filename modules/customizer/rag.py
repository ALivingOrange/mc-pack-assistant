import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from .data import VALID_ITEM_IDS

logger = logging.getLogger(__name__)


class ItemIDSearcher:
    """Semantic search for Minecraft item IDs using embeddings."""

    def __init__(self, item_ids: list[str], model_name: str = "all-MiniLM-L6-v2"):
        logger.info("Loading embedding model for item search...")
        self.model = SentenceTransformer(model_name)
        self.item_ids = list(item_ids)

        self.item_texts = [self._format_item_for_embedding(item_id) for item_id in self.item_ids]

        logger.info("Computing embeddings for %d items...", len(self.item_ids))
        self.embeddings = self.model.encode(self.item_texts, show_progress_bar=True)
        logger.info("Item search ready!")

    def _format_item_for_embedding(self, item_id: str) -> str:
        return item_id.replace(":", " ").replace("_", " ")

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        query_embedding = self.model.encode([query])[0]

        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [(self.item_ids[idx], float(similarities[idx])) for idx in top_indices]


logger.info("Initializing item ID semantic search...")
ITEM_SEARCHER = ItemIDSearcher(list(VALID_ITEM_IDS))
