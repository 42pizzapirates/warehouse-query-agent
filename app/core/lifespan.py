from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.elasticsearch_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.core.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("启动服务,执行各个客户端管理器初始化")
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()
    embedding_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()
    yield
    logger.info("项目关闭,执行各个客户端管理器关闭操作")
    await dw_mysql_client_manager.close()
    await meta_mysql_client_manager.close()
    await es_client_manager.close()
    await qdrant_client_manager.close()
