"""Elasticsearch 字段取值文档。"""

from dataclasses import dataclass

@dataclass
class ValueInfo:
  id: str
  value: str
  column_id: str
