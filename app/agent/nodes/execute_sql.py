from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """执行最终 SQL，并通过流写入器返回进度和结果。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "执行SQL", "status": "running"})

    try:
        sql = state["sql"]
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        data = await dw_mysql_repository.execute_sql(sql)
        write({"type": "progress", "step": "执行SQL", "status": "success"})
        write({"type": "result", "data": data})
    except Exception as e:
        logger.error(f"执行SQL发生异常：{e}")
        write({"type": "progress", "step": "执行SQL", "status": "error"})
        raise
