import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """根据校验错误调用大模型修正 SQL。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "校正SQL", "status": "running"})

    try:
        query = state["query"]
        table_infos = state["table_infos"]
        metric_infos = state["metric_infos"]
        db_info = state["db_info"]
        date_info = state["date_info"]
        sql = state["sql"]
        error = state["error"]
        prompt = PromptTemplate(template=load_prompt("correct_sql"),
                                input_variables=["query", "table_infos", "metric_infos", "db_info", "date_info", "sql",
                                                 "error"])
        str_output_parse = StrOutputParser()
        chain = prompt | llm | str_output_parse
        sql = await chain.ainvoke({"query": query,
                                   "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
                                   "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
                                   "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
                                   "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
                                   "sql": sql,
                                   "error": error
                                   })

        logger.info(f"修正SQL成功：{sql}")
        write({"type": "progress", "step": "校正SQL", "status": "success"})
        return {"sql": sql}
    except Exception as e:
        logger.error(f"校正SQL发生异常：{e}")
        write({"type": "progress", "step": "校正SQL", "status": "error"})
        raise
