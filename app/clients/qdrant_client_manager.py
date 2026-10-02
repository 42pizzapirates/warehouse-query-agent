import asyncio
import random
from typing import Optional
from qdrant_client import AsyncQdrantClient, models
from app.conf.app_config import QdrantConfig, app_config

class QdrantClientManager:
    """Qdrant向量数据库异步客户端管理器：封装客户端的初始化、关闭逻辑"""

    def __init__(self, qdrant_config: QdrantConfig):
        """
        初始化Qdrant客户端管理器
        :param qdrant_config: Qdrant配置对象，包含host/port等连接信息
        """
        # 保存Qdrant连接配置
        self.qdrant_config = qdrant_config
        # 定义异步Qdrant客户端对象，初始为None（init方法中初始化）
        self.client: Optional[AsyncQdrantClient] = None

    def _get_url(self):
        """
        拼接Qdrant服务的连接URL
        :return: 符合Qdrant客户端要求的http连接地址
        """
        return f"http://{self.qdrant_config.host}:{self.qdrant_config.port}"

    def init(self):
        """初始化异步Qdrant客户端（创建客户端实例）"""
        self.client = AsyncQdrantClient(self._get_url())

    async def close(self):
        """异步关闭Qdrant客户端，释放连接资源"""
        await self.client.close()


# 实例化Qdrant客户端管理器（传入全局配置中的Qdrant配置）
qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == '__main__':
    # 初始化Qdrant异步客户端
    qdrant_client_manager.init()

    async def test():
        """测试Qdrant异步客户端核心功能：创建集合、插入向量、相似度检索"""
        # 获取初始化后的Qdrant异步客户端实例
        client = qdrant_client_manager.client
        # 1. 检查集合是否存在，不存在则创建
        if not await client.collection_exists("my_collection"):
            await client.create_collection(
                collection_name="my_collection",  # 集合名称（类似数据库表名）
                # 向量字段配置：10维向量，使用余弦相似度计算
                vectors_config=models.VectorParams(size=10, distance=models.Distance.COSINE),
            )

        # 2. 批量插入100个10维随机向量到集合中
        await client.upsert(
            collection_name="my_collection",
            # 列表推导式生成100个PointStruct对象（包含ID和随机向量）
            points=[
                models.PointStruct(
                    id=i,  # 向量唯一标识ID
                    vector=[random.random() for _ in range(10)]  # 生成10维随机向量
                )
                for i in range(100)
            ],
        )

        # 3. 向量相似度检索：查找最相似的10个向量
        res = await client.query_points(
            collection_name="my_collection",  # 检索的集合名称
            query=[random.random() for _ in range(10)],  # 10维随机查询向量（type: ignore忽略类型提示）
            limit=10,  # 返回最相似的前10个向量
            score_threshold=0.5  # 相似度得分阈值：只返回得分≥0.5的结果
        )
        # 打印检索结果中的向量点信息（包含ID、向量、得分等）
        print(res.points)

    # 运行异步测试函数（asyncio.run是执行异步函数的标准方式）
    asyncio.run(test())