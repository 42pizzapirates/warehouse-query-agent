
import uuid

from fastapi import FastAPI, Request

from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan

app = FastAPI(title="掌柜问数", lifespan=lifespan)

app.include_router(query_router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id_ctx_var.set(uuid.uuid4())
    return await call_next(request)

