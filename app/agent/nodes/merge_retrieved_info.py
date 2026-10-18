from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, MetricInfoState, TableInfoState, ColumnInfoState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """补齐已召回信息，形成 SQL 生成所需的表、字段与指标上下文。"""

    write = runtime.stream_writer
    write({"type": "progress", "step": "合并召回信息", "status": "running"})
    try:
        retrieved_columns: list[ColumnInfo] = state["retrieved_columns"]
        retrieved_metrics: list[MetricInfo] = state["retrieved_metrics"]
        retrieved_values: list[ValueInfo] = state["retrieved_values"]
        meta_mysql_repository = runtime.context["meta_mysql_repository"]

        column_id_column_info_dict = {column_info.id: column_info for column_info in retrieved_columns}
        # 指标关联字段可能未被向量召回，按字段 ID 从元数据库补齐。
        for retrieved_metric in retrieved_metrics:
            for column_id in retrieved_metric.relevant_columns:
                if column_id not in column_id_column_info_dict:
                    column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                    column_id_column_info_dict[column_id] = column_info

        # 将召回的真实取值补充到字段样例，约束 WHERE 条件生成。
        for value_info in retrieved_values:
            column_id = value_info.column_id
            if column_id not in column_id_column_info_dict:
                column_info: ColumnInfo = await meta_mysql_repository.get_column_info_by_id(column_id)
                column_id_column_info_dict[column_id] = column_info
            value = value_info.value
            if value not in column_id_column_info_dict[column_id].examples:
                column_id_column_info_dict[column_id].examples.append(value)

        table_id_columns_dict: dict[str, list[ColumnInfo]] = {}
        for column_info in column_id_column_info_dict.values():
            table_id = column_info.table_id
            if table_id not in table_id_columns_dict:
                table_id_columns_dict[table_id] = []
            table_id_columns_dict[table_id].append(column_info)

        # 补齐主外键，保留表之间的关联路径。
        for table_id in table_id_columns_dict.keys():
            column_ids = [column.id for column in table_id_columns_dict[table_id]]
            key_columns: list[ColumnInfo] = await meta_mysql_repository.get_key_column_by_table_id(table_id)
            for key_column in key_columns:
                if key_column.id not in column_ids:
                    table_id_columns_dict[table_id].append(key_column)

        table_infos: list[TableInfoState] = []
        for table_id, column_infos in table_id_columns_dict.items():
            table_info: TableInfo = await meta_mysql_repository.get_table_info_by_id(table_id)
            table_info_state = TableInfoState(
                name=table_info.name,
                role=table_info.role,
                description=table_info.description,
                columns=[ColumnInfoState(
                    name=column_info.name,
                    type=column_info.type,
                    role=column_info.role,
                    examples=column_info.examples,
                    description=column_info.description,
                    alias=column_info.alias
                ) for column_info in column_infos]
            )
            table_infos.append(table_info_state)
        metric_infos: list[MetricInfoState] = []
        if retrieved_metrics:
            for metric_info in retrieved_metrics:
                metric_info_state = MetricInfoState(
                    name=metric_info.name,
                    description=metric_info.description,
                    relevant_columns=metric_info.relevant_columns,
                    alias=metric_info.alias
                )
                metric_infos.append(metric_info_state)
        write({"type": "progress", "step": "合并召回信息", "status": "success"})
        logger.info(f"合并召回信息成功，表：{table_id_columns_dict.keys()}")
        logger.info(f"合并召回信息成功，字段：{[column['name'] for ti in table_infos for column in ti['columns']]}")
        logger.info(f"合并召回信息成功，指标：{[metric_info["name"] for metric_info in metric_infos]}")
        return {"table_infos": table_infos, "metric_infos": metric_infos}
    except Exception as e:
        logger.error(f"合并召回信息发生异常：{e}")
        write({"type": "progress", "step": "合并召回信息", "status": "error"})
        raise
