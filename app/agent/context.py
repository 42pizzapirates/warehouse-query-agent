from langchain_huggingface import HuggingFaceEndpointEmbeddings
from typing_extensions import TypedDict

from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class DataAgentContext(TypedDict):
    """Graph 运行时依赖；节点只读访问各存储的持久层与嵌入客户端。"""

    meta_mysql_repository: MetaMySQLRepository
    dw_mysql_repository: DWMySQLRepository
    embedding_client: HuggingFaceEndpointEmbeddings
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
    value_es_repository: ValueESRepository
