from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    """字段信息在 Graph 状态中的表示。"""

    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    """表信息在 Graph 状态中的表示。"""

    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    """指标信息在 Graph 状态中的表示。"""

    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    """生成 SQL 时使用的日期上下文。"""

    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    """数仓版本与方言信息。"""

    version: str
    dialect: str


class DataAgentState(TypedDict):
    """Graph 各节点共享的运行时状态。"""

    query: str
    keywords: list[str]
    retrieved_columns: list[ColumnInfo]
    retrieved_metrics: list[MetricInfo]
    retrieved_values: list[ValueInfo]
    table_infos: list[TableInfoState]
    metric_infos: list[MetricInfoState]

    date_info: DateInfoState
    db_info: DBInfoState

    sql: str
    error: str
