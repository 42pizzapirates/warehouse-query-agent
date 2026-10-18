from sqlalchemy import text, Result
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:
    """跟MySQL数据库（数仓数据库）交互持久层 必须通过Session对象进行CURD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_type_by_table_id(self, table_id: str) -> dict[str, str]:
        """根据表ID/表名称查询该表下所有字段信息 目的获取字段数据类型"""
        sql = f"show columns from {table_id}"
        result: Result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values_by_table_id(self, table_id: str, column_name: str, limit: int = 10) -> list[str]:
        """查询指定个数某张表某个字段取值"""
        sql = f"SELECT distinct {column_name} from {table_id} limit {limit}"
        result: Result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async def get_db_info(self):
        """返回数仓版本与 SQL 方言。"""

        result = await self.session.execute(text("select version()"))
        version = result.scalar()

        dialect = self.session.get_bind().dialect.name
        return {"version": version, "dialect": dialect}

    async def validate_sql(self, sql: str):
        """通过执行计划校验 SQL；语法错误会抛出异常。"""

        await self.session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql):
        """执行 SQL 并返回字典列表形式的结果。"""

        result:Result = await self.session.execute(text(sql))
        return [dict(row_mapping) for row_mapping in  result.mappings().fetchall()]
