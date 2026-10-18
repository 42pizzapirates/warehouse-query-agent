from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """注入当前日期和数仓环境信息，供 SQL 生成与校验使用。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "添加额外上下文", "status": "running"})

    try:
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        quarter = f"Q{(today.month - 1) // 3 + 1}"
        date_state = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter
        )

        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        db_info: dict[str, str] = await dw_mysql_repository.get_db_info()

        db_info_state = DBInfoState(
            version=db_info["version"],
            dialect=db_info["dialect"]
        )
        write({"type": "progress", "step": "添加额外上下文", "status": "success"})
        logger.info(f"添加额外上下文成功：{db_info_state}, {date_state}")

        return {"date_info": date_state, "db_info": db_info_state}
    except Exception as e:
        logger.error(f"添加上下文发生异常：{e}")
        write({"type": "progress", "step": "添加上下文", "status": "error"})
        raise
