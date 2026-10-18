from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, QueryResponse

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:

    coll_name = "data-agent-column"

    def __init__(self, client:AsyncQdrantClient):
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

    async def upsert(self, ids:list[str], embeddings:list[list[float]], payloads:list[ColumnInfo], batch_size:int=10):
        zipped = list(zip(ids, embeddings, payloads))

        for i in range(0, len(zipped), batch_size):
            batch = zipped[i: i+batch_size]
            points = [PointStruct(
                id = id,
                vector=embeding,
                # Qdrant payload 必须是可序列化的字典。
                payload=asdict(payload)
            ) for id,embeding,payload in batch]
            await self.client.upsert(collection_name=self.coll_name, points=points)

    async def search(self, embedding: list[float], score: float = 0.6, limit: int = 10):
        result:QueryResponse = await self.client.query_points(
            collection_name=self.coll_name,
            query=embedding,
            score_threshold=score,
            limit=limit
        )
        return [ColumnInfo(**point.payload) for point in result.points]
