import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    """Elasticsearch异步客户端管理器：封装ES客户端的初始化、连接、关闭逻辑"""

    def __init__(self, es_config: ESConfig):
        """
        初始化ES客户端管理器
        :param es_config: ES配置对象，包含host（主机地址）、port（端口号）等核心连接参数
        """
        # 保存ES服务的连接配置信息
        self.es_config = es_config
        # 定义异步ES客户端对象，初始值为None（通过init方法初始化）
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        """
        拼接ES服务的连接URL
        :return: 符合ES客户端要求的http格式连接地址（如：http://127.0.0.1:9200）
        """
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        """初始化异步Elasticsearch客户端实例（创建连接）"""
        # 创建异步ES客户端，hosts参数接收列表形式的连接地址
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        """异步关闭ES客户端连接，释放资源（需在程序退出前调用）"""
        await self.client.close()

# 实例化ES客户端管理器，传入全局配置中的ES连接配置
es_client_manager = ESClientManager(app_config.es)



if __name__ == '__main__':
    es_client_manager.init()

    async def test():
        client = es_client_manager.client

        # 创建索引
        #参考：https://www.elastic.co/guide/en/elasticsearch/reference/8.19/getting-started.html#getting-started-explicit-mapping
        await client.indices.create(
            index="my-books",
            mappings={
                "dynamic": False,
                "properties": {
                    "name": {
                        "type": "text"
                    },
                    "author": {
                        "type": "text"
                    },
                    "release_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "page_count": {
                        "type": "integer"
                    }
                }
            },
        )

        # 插入数据
        #参考：https://www.elastic.co/guide/en/elasticsearch/reference/8.19/getting-started.html#getting-started-add-multiple-documents
        await client.bulk(
            operations=[
                {
                    "index": {
                        "_index": "my-books"
                    }
                },
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585
                },
                {
                    "index": {
                        "_index": "my-books"
                    }
                },
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328
                },
                {
                    "index": {
                        "_index": "my-books"
                    }
                },
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227
                },
                {
                    "index": {
                        "_index": "my-books"
                    }
                },
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268
                },
                {
                    "index": {
                        "_index": "my-books"
                    }
                },
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311
                }
            ],
        )

        # 搜索
        # 参考：https://www.elastic.co/guide/en/elasticsearch/reference/8.19/getting-started.html#getting-started-match-query
        resp = await client.search(
            index="my-books",
            query={
                "match": {
                    "name": "brave"
                }
            },
        )
        print(resp)
        await es_client_manager.close()


    asyncio.run(test())