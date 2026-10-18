from typing import Optional

from qdrant_client import AsyncQdrantClient

from app.conf.app_config import QdrantConfig, app_config


class QdrantClientManager:
    """Qdrant 异步客户端管理器。"""

    def __init__(self, qdrant_config: QdrantConfig):
        """初始化 Qdrant 客户端管理器。"""
        self.qdrant_config = qdrant_config
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        """拼接 Qdrant 服务的访问地址。"""
        return f"http://{self.qdrant_config.host}:{self.qdrant_config.port}"

    def init(self):
        """创建异步 Qdrant 客户端。"""
        self.client = AsyncQdrantClient(self._get_url())

    async def close(self):
        """关闭客户端并释放连接资源。"""
        await self.client.close()


qdrant_client_manager = QdrantClientManager(app_config.qdrant)
