from contextvars import ContextVar

# 请求级追踪标识；中间件会在每个请求中覆盖默认值。
request_id_ctx_var = ContextVar("request_id", default=1)
