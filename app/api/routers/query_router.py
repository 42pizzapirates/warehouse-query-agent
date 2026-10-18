from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

query_router = APIRouter(tags=["查询接口"])


@query_router.post("/api/query")
async def query(query_schema: QuerySchema, query_service:Annotated[QueryService, Depends(get_query_service)]):
    """以 SSE 流式返回查询执行进度与最终结果。"""
    return StreamingResponse(query_service.query_answer(query_schema.query), media_type="text/event-stream")
