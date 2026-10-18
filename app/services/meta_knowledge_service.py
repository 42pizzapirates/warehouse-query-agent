import uuid
from pathlib import Path

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.models.column_info_mysql import ColumnInfoMySQL
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    """元数据知识库构建服务。"""

    def __init__(self, meta_mysql_repository: MetaMySQLRepository, dw_mysql_repository: DWMySQLRepository,
                 column_qdrant_repository: ColumnQdrantRepository, embedding_client: HuggingFaceEndpointEmbeddings,
                 value_es_repository: ValueESRepository, metric_qdrant_repository: MetricQdrantRepository):
        """注入各存储的持久层与嵌入客户端。"""

        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    async def build(self, meta_config_path: Path):
        """读取元数据配置并同步到 MySQL、Qdrant 与 Elasticsearch。"""

        logger.info(f"构建元数据库脚本,{meta_config_path}")

        context = OmegaConf.load(meta_config_path)
        structured = OmegaConf.structured(MetaConfig)
        # 合并结构化 schema，确保配置字段完整且类型正确。
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(structured, context))

        if meta_config.tables:
            column_infos: list[ColumnInfo] = await self._save_table_info_to_meta_db(meta_config)
            logger.info(f"批量保存表信息成功")

            await self._save_column_info_to_qdrant(column_infos)
            logger.info(f"为字段信息建立向量索引成功")

            await self._save_value_info_to_es(meta_config, column_infos)
            logger.info(f"为字段取值建立全文索引成功 ")

        if meta_config.metrics:
            metric_infos: list[MetricInfo] = await self._save_metric_info_to_meta_db(meta_config)
            logger.info("指标信息存入到meta元数据库成功")

            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("为指标信息建立向量索引成功")

    async def _save_table_info_to_meta_db(self, meta_config: MetaConfig) -> list[ColumnInfo]:
        """构建表和字段实体，并批量写入元数据库。"""

        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []
        if meta_config.tables:
            for table in meta_config.tables:
                table_info = TableInfo(
                    id=table.name,
                    name=table.name,
                    description=table.description,
                    role=table.role
                )
                table_infos.append(table_info)
                column_type: dict[str, str] = await self.dw_mysql_repository.get_column_type_by_table_id(table_info.id)
                for column in table.columns:
                    examples: list[str] = await self.dw_mysql_repository.get_column_values_by_table_id(table_info.id,
                                                                                                       column.name)
                    # 字段 ID 统一采用 "表 ID.字段名" 的约定。
                    column_info = ColumnInfo(
                        id=f"{table_info.id}.{column.name}",
                        name=column.name,
                        role=column.role,
                        description=column.description,
                        alias=column.alias,
                        table_id=table_info.id,
                        type=column_type[column.name],
                        examples=examples
                    )
                    column_infos.append(column_info)
        # 表与字段在同一事务中写入，避免元数据只落一部分。
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_table_infos(table_infos)
            await self.meta_mysql_repository.save_column_infos(column_infos)
        return column_infos

    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
        """为字段名称、描述和别名建立向量索引。"""

        await self.column_qdrant_repository.ensure_collection()

        points = []
        # 名称、描述、别名分别建点，提高不同表述下的召回覆盖率。
        for column_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": column_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info
            })
            for alias in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": column_info
                })
        embeddings = []
        batch_size = 10
        embedding_texts = [point["embedding_text"] for point in points]
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding = embedding_texts[i: i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)

    async def _save_value_info_to_es(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
        """将配置开启 sync 的字段取值写入全文索引。"""

        await self.value_es_repository.ensure_index()
        value_infos: list[ValueInfo] = []

        # 仅同步配置中显式开启 sync 的字段取值。
        colum2es = [column.name for table in meta_config.tables for column in table.columns if column.sync == True]

        for column_info in column_infos:
            if column_info.name in colum2es:
                values = await self.dw_mysql_repository.get_column_values_by_table_id(column_info.table_id,
                                                                                      column_info.name, limit=100000)
                for value in values:
                    value_info = ValueInfo(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        column_id=column_info.id
                    )
                    value_infos.append(value_info)
        await self.value_es_repository.upsert(value_infos)

    async def _save_metric_info_to_meta_db(self, meta_config: MetaConfig) -> list[MetricInfo]:
        """构建指标及其字段关联关系，并批量写入元数据库。"""

        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []

        for metric in meta_config.metrics:
            metric_info = MetricInfo(
                id = metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            )
            metric_infos.append(metric_info)
            for relevant_column in metric.relevant_columns:
                column_metric = ColumnMetric(
                    metric_id=metric_info.id,
                    column_id=relevant_column
                )
                column_metrics.append(column_metric)
        # 指标与字段关联在同一事务中写入。
        async with self.meta_mysql_repository.session.begin():
            await self.meta_mysql_repository.save_metric_info_to_meta_db(metric_infos)
            await self.meta_mysql_repository.save_column_metric_info_to_meta_db(column_metrics)
        return metric_infos

    async def _save_metric_info_to_qdrant(self, metric_infos:list[MetricInfo]):
        """为指标名称、描述和别名建立向量索引。"""

        await self.metric_qdrant_repository.ensure_collection()

        points = []
        # 名称、描述、别名分别建点，提高不同表述下的召回覆盖率。
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": metric_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": metric_info
            })
            for alias in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alias,
                    "payload": metric_info
                })
        embeddings = []
        batch_size = 10
        embedding_texts = [point["embedding_text"] for point in points]
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding = embedding_texts[i: i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch_embedding)
            embeddings.extend(batch_embeddings)
        ids = [point["id"] for point in points]
        payloads = [point["payload"] for point in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)
