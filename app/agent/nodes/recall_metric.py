from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """扩展关键词并从指标向量库召回相关指标。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "召回指标", "status": "running"})
    try:
        query = state["query"]
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"), input_variables=["query"])
        json_output = JsonOutputParser()
        chain = prompt | llm | json_output
        result = await chain.ainvoke({"query": query})

        keywords = list(set(keywords + result))

        # 以指标 ID 去重，保留首次召回结果。
        retrieved_metrics_dict: dict[str, MetricInfo] = {}

        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            metric_infos: list[MetricInfo] = await metric_qdrant_repository.search(embedding)
            for metric_info in metric_infos:
                metric_id = metric_info.id
                if metric_id not in retrieved_metrics_dict:
                    retrieved_metrics_dict[metric_id] = metric_info

        write({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info(f"召回指标信息成功：{list(retrieved_metrics_dict.keys())}")
        return {"retrieved_metrics": list(retrieved_metrics_dict.values())}
    except Exception as e:
        logger.error(f"召回指标发生异常：{e}")
        write({"type": "progress", "step": "召回指标", "status": "error"})
        raise
