from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import QueryResponse, VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:
    """操作指标向量索引库持久层"""

    coll_name = "data-agent-metric"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client


    async def ensure_collection(self):
        if not await self.client.collection_exists(collection_name=self.coll_name):
            await self.client.create_collection(
                collection_name=self.coll_name,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[MetricInfo],
                     batch_size: int = 10):
        zipped = list(zip(ids, embeddings, payloads))

        for i in range(0, len(zipped), batch_size):
            batch = zipped[i: i + batch_size]
            points = [PointStruct(
                id=id,
                vector=embeding,
                # Qdrant payload 必须是可序列化的字典。
                payload=asdict(payload)
            ) for id, embeding, payload in batch]
            await self.client.upsert(collection_name=self.coll_name, points=points)

    async def search(self, embedding: list[float], score: float = 0.6, limit: int = 10) ->list[MetricInfo]:
        result: QueryResponse = await self.client.query_points(
            collection_name=self.coll_name,
            query=embedding,
            score_threshold=score,
            limit=limit
        )
        return [MetricInfo(**point.payload) for point in result.points]

