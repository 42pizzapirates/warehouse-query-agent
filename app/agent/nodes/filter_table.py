import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """用大模型筛除与问题无关的表和字段。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "过滤表格", "status": "running"})

    try:
        table_infos: list[TableInfoState] = state["table_infos"]
        query = state["query"]
        prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=["query", "table_infos"])
        chain = prompt | llm | JsonOutputParser()
        # 模型返回 {"表名": ["字段名", ...]}，未出现的表或字段视为无关。
        result = await chain.ainvoke({"query":query, "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False)})

        for table_info in table_infos[:]:
            table_name = table_info["name"]
            if table_name not in result:
                table_infos.remove(table_info)
            else:
                columns = table_info["columns"]
                for column in columns[:]:
                    column_name = column["name"]
                    if column_name not in result[table_name]:
                        table_info["columns"].remove(column)
        write({"type": "progress", "step": "过滤表格", "status": "success"})
        logger.info(f"过滤表格成功，表信息：{[table_info["name"] for table_info in table_infos]}")
        logger.info(f"过滤表格成功，字段信息：{[column['name'] for ti in table_infos for column in ti['columns']]}")
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(f"过滤表格发生异常：{e}")
        write({"type": "progress", "step": "过滤表格", "status": "error"})
        raise
