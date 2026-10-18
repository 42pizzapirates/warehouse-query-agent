from typing import Optional
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddedClientManager:
    """HuggingFace 向量嵌入客户端管理器。"""

    def __init__(self, config: EmbeddingConfig):
        """初始化嵌入客户端管理器。"""
        self.config = config
        self.client: Optional[HuggingFaceEndpointEmbeddings] = None

    def _get_url(self):
        """拼接嵌入服务的访问地址。"""
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        """创建嵌入客户端实例。"""
        self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())


embedding_client_manager = EmbeddedClientManager(app_config.embedding)
