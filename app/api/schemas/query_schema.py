from pydantic import BaseModel


class QuerySchema(BaseModel):
    """查询接口请求体。"""

    query: str
