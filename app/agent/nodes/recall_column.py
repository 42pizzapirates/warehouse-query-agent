from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """扩展关键词并从字段向量库召回相关字段。"""

    writer = get_stream_writer()
    writer({"type": "progress", "step": "召回字段", "status": "running"})

    try:
        query = state["query"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_column_recall"), input_variables=["query"])
        output = JsonOutputParser()
        chain = prompt | llm | output
        result = await chain.ainvoke({"query": query})
        logger.info(f"recall_column节点，大模型扩充字段结果：{result}")
        keywords = state["keywords"]
        keywords = list(set(result + keywords))
        # 以字段 ID 去重，保留首次召回结果。
        retrieved_columns_map: dict[str, ColumnInfo] = {}
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            colunm_infos: list[ColumnInfo] = await column_qdrant_repository.search(embedding)
            for colunm_info in colunm_infos:
                colunm_id = colunm_info.id
                if colunm_id not in retrieved_columns_map:
                    retrieved_columns_map[colunm_id] = colunm_info
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info(f"召回字段成功，字段信息：{list(retrieved_columns_map.keys())}")
        return {"retrieved_columns": list(retrieved_columns_map.values())}
    except Exception as e:
        logger.error(f"召回字段节点执行异常:{e}")
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        raise
