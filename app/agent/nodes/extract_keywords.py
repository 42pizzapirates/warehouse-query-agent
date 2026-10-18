import jieba.analyse
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """Graph 入口节点，从用户问题中抽取检索关键词。"""
    query = state["query"]
    writer = get_stream_writer()
    writer({"type": "progress", "step": "抽取关键字", "status": "running"})
    try:
        # 保留名词、专有名词、动词等对元数据召回有意义的词性。
        allow_pos = (
            "n",
            "nr",
            "ns",
            "nt",
            "nz",
            "v",
            "vn",
            "a",
            "an",
            "eng",
            "i",
            "l",
        )
        keywords = jieba.analyse.extract_tags(query, topK=10, allowPOS=allow_pos)
        # 原始问题一并保留，避免分词丢失完整语义。
        keywords = list(set(keywords + [query]))
        writer({"type": "progress", "step": "抽取关键字", "status": "success"})
        logger.info(f"抽取关键字成功:{keywords}")
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"抽取关键字节点执行异常:{e}")
        writer({"type": "progress", "step": "抽取关键字", "status": "error"})
        raise
