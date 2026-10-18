import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """用大模型筛除与问题无关的指标。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "过滤指标", "status": "running"})

    try:
        metric_infos: list[MetricInfoState] = state["metric_infos"]
        query = state["query"]
        prompt = PromptTemplate(template=load_prompt("filter_metric_info"), input_variables=["query", "metric_infos"])
        out_put = JsonOutputParser()
        # 模型返回所需指标名称列表。
        chain = prompt | llm | out_put
        result = await chain.ainvoke(
            {"query": query, "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)})
        logger.info(f"调用llm获取所需指标：{result}")

        # 遍历副本，避免边遍历边删除导致漏删。
        for metric_info in metric_infos[:]:
            metric_name = metric_info["name"]
            if metric_name not in result:
                metric_infos.remove(metric_info)
        write({"type": "progress", "step": "过滤指标", "status": "success"})
        logger.info(f"过滤指标成功，指标：{[metric_info["name"] for metric_info in metric_infos]}")
        return {"metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"过滤指标发生异常：{e}")
        write({"type": "progress", "step": "过滤指标", "status": "error"})
        raise
