from itertools import chain

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回字段真实取值，约束 SQL 中 WHERE 条件的字面量。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "召回字段取值", "status": "running"})
    try:
        query = state["query"]
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        json_output = JsonOutputParser()
        chain = prompt | llm | json_output
        result = await chain.ainvoke({"query": query})

        keywords = list(set(keywords + result))

        # 以取值文档 ID 去重，保留首次召回结果。
        retrieved_metrics_dict: dict[str, ValueInfo] = {}

        value_es_repository = runtime.context["value_es_repository"]

        if keywords:
            for keyword in keywords:
                value_infos: list[ValueInfo] = await value_es_repository.search(keyword)
                for value_info in value_infos:
                    value_id = value_info.id
                    if value_id not in retrieved_metrics_dict:
                        retrieved_metrics_dict[value_id] = value_info
        write({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"字段取值召回成功：{list(retrieved_metrics_dict.keys())}")
        return {"retrieved_values": list(retrieved_metrics_dict.values())}
    except Exception as e:
        logger.error(f"召回字段取值发生异常：{e}")
        write({"type": "progress", "step": "召回字段取值", "status": "error"})
        raise
