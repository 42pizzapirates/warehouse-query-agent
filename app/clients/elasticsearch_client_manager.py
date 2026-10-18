from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    """Elasticsearch 异步客户端管理器。"""

    def __init__(self, es_config: ESConfig):
        """初始化 Elasticsearch 客户端管理器。"""
        self.es_config = es_config
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        """拼接 Elasticsearch 服务的访问地址。"""
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        """创建异步 Elasticsearch 客户端。"""
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        """关闭客户端并释放连接资源。"""
        await self.client.close()


es_client_manager = ESClientManager(app_config.es)
