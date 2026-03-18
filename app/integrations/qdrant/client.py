from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SearchHit:
    candidate_id: str
    score: float
    payload: dict[str, Any]


class InMemoryVectorStore:
    """Fallback vector store used in tests and local environments without Qdrant."""

    def __init__(self) -> None:
        self.points: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def recreate_collection(self, collection_name: str) -> None:
        self.points[collection_name] = []

    def ensure_collection(self, collection_name: str) -> None:
        self.points.setdefault(collection_name, [])

    def upsert(self, collection_name: str, points: list[dict[str, Any]]) -> None:
        existing = [point for point in self.points[collection_name] if point["id"] not in {p["id"] for p in points}]
        self.points[collection_name] = existing + points

    def delete_candidate(self, collection_name: str, candidate_id: str) -> None:
        self.points[collection_name] = [
            point for point in self.points[collection_name] if point["payload"]["candidate_id"] != candidate_id
        ]

    def search(self, collection_name: str, vector: list[float], role_bucket: str, limit: int) -> list[SearchHit]:
        def cosine(a: list[float], b: list[float]) -> float:
            numerator = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            return numerator / (norm_a * norm_b) if norm_a and norm_b else 0.0

        hits = []
        for point in self.points.get(collection_name, []):
            if point["payload"].get("role_bucket") != role_bucket:
                continue
            hits.append(
                SearchHit(
                    candidate_id=point["payload"]["candidate_id"],
                    score=cosine(vector, point["vector"]),
                    payload=point["payload"],
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:limit]


class QdrantIndex:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.memory = InMemoryVectorStore()
        self.client: QdrantClient | None = None
        if self.settings.enable_qdrant:
            try:
                self.client = QdrantClient(url=self.settings.qdrant_url)
            except Exception as exc:
                logger.warning("qdrant_init_failed", error=str(exc))
                self.client = None

    def ensure_collection(self, vector_size: int = 1536) -> None:
        if self.client:
            try:
                collections = [collection.name for collection in self.client.get_collections().collections]
                if self.settings.qdrant_collection not in collections:
                    self.client.create_collection(
                        collection_name=self.settings.qdrant_collection,
                        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                    )
                return
            except Exception as exc:
                logger.warning("qdrant_ensure_collection_failed", error=str(exc))
                self.client = None
        self.memory.ensure_collection(self.settings.qdrant_collection)

    def recreate_collection(self, vector_size: int = 1536) -> None:
        if self.client:
            try:
                self.client.recreate_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )
                return
            except Exception as exc:
                logger.warning("qdrant_recreate_collection_failed", error=str(exc))
                self.client = None
        self.memory.recreate_collection(self.settings.qdrant_collection)

    def delete_candidate(self, candidate_id: str) -> None:
        if self.client:
            try:
                self.client.delete(
                    collection_name=self.settings.qdrant_collection,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[models.FieldCondition(key="candidate_id", match=models.MatchValue(value=candidate_id))]
                        )
                    ),
                )
                return
            except Exception as exc:
                logger.warning("qdrant_delete_failed", error=str(exc), candidate_id=candidate_id)
                self.client = None
        self.memory.delete_candidate(self.settings.qdrant_collection, candidate_id)

    def upsert_points(self, points: list[dict[str, Any]]) -> None:
        if not points:
            return
        if self.client:
            try:
                self.client.upsert(
                    collection_name=self.settings.qdrant_collection,
                    points=[models.PointStruct(**point) for point in points],
                )
                return
            except Exception as exc:
                logger.warning("qdrant_upsert_failed", error=str(exc), point_count=len(points))
                self.client = None
        self.memory.upsert(self.settings.qdrant_collection, points)

    def search(self, vector: list[float], role_bucket: str, limit: int) -> list[SearchHit]:
        if self.client:
            try:
                results = self.client.search(
                    collection_name=self.settings.qdrant_collection,
                    query_vector=vector,
                    limit=limit,
                    query_filter=models.Filter(
                        must=[models.FieldCondition(key="role_bucket", match=models.MatchValue(value=role_bucket))]
                    ),
                )
                return [
                    SearchHit(candidate_id=result.payload["candidate_id"], score=result.score, payload=result.payload)
                    for result in results
                ]
            except Exception as exc:
                logger.warning("qdrant_search_failed", error=str(exc), role_bucket=role_bucket)
                self.client = None
        return self.memory.search(self.settings.qdrant_collection, vector, role_bucket, limit)
