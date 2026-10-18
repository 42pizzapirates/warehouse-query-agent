import argparse
import asyncio
from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.elasticsearch_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def build(meta_config_path:Path):
    """初始化依赖并构建元数据知识库。"""

    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()

    async with (dw_mysql_client_manager.session_factory() as dw_session,
                meta_mysql_client_manager.session_factory() as meta_session):
        meta_knowledge_service = MetaKnowledgeService(
            meta_mysql_repository  = MetaMySQLRepository(meta_session),
            dw_mysql_repository = DWMySQLRepository(dw_session),
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client),
            embedding_client = embedding_client_manager.client,
            value_es_repository=ValueESRepository(es_client_manager.client),
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
        )
        await meta_knowledge_service.build(meta_config_path)

        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='python -m app.scripts.build_meta_knowledge',
        description='通过脚本+额外脚本(-c 传递)参数实现',
        epilog='========结束==========')
    parser.add_argument('-c', '--conf')
    parse_args = parser.parse_args()
    config_path: Path = Path(parse_args.conf)

    asyncio.run(build(config_path))
