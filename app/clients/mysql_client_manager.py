from typing import Optional

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.conf.app_config import app_config, DBConfig


class MysqlClientManager:
    """MySQL 异步客户端管理器。"""

    def __init__(self, db_config: DBConfig):
        self.db_config = db_config
        self.engine: Optional[AsyncEngine] = None

    def _get_url(self):
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.db_config.user,
            password=self.db_config.password,
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.database,
            query={"charset": "utf8mb4"},
        )

    def init(self):
        self.engine = create_async_engine(
            self._get_url(),
            pool_size=10,
            # 提前探活，避免连接池返回失效连接。
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            # 事务边界由业务层显式控制，避免隐式 flush。
            autoflush=False,
            # 提交后仍可访问 ORM 对象属性，避免额外查询。
            expire_on_commit=False,
        )

    async def close(self):
        if self.engine is None:
            return
        await self.engine.dispose()


dw_mysql_client_manager = MysqlClientManager(app_config.db_dw)
meta_mysql_client_manager = MysqlClientManager(app_config.db_meta)
