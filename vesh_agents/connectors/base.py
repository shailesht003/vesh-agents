"""Abstract connector interface — every data source connector implements this contract."""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


import logging
from typing import Any

logger = logging.getLogger(__name__)


class ChangeType(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ConnectorCapabilities:
    """What a connector supports."""

    supports_cdc: bool = False
    supports_incremental: bool = False
    supports_schema_introspection: bool = True
    read_only: bool = True


@dataclass
class ColumnSchema:
    """Schema for a single column."""

    column_name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    semantic_type: str | None = None
    semantic_confidence: float | None = None
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class TableSchema:
    """Schema for a single table/object type."""

    table_name: str
    columns: list[ColumnSchema]
    row_count_estimate: int | None = None


@dataclass
class DiscoveredSchema:
    """Full schema discovered from a data source."""

    source_type: str
    tables: list[TableSchema]
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class NormalizedRecord:
    """Common record format emitted by all connectors."""

    source_type: str
    source_id: str
    object_type: str
    record_id: str
    data: dict[str, Any]
    extracted_at: datetime
    change_type: ChangeType
    record_hash: str
    schema_annotations: dict[str, dict] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "object_type": self.object_type,
            "record_id": self.record_id,
            "data": self.data,
            "extracted_at": self.extracted_at.isoformat(),
            "change_type": self.change_type.value,
            "record_hash": self.record_hash,
        }


class BaseConnector(ABC):
    """Abstract base class for all data source connectors."""

    def __init__(self, connection_id: str, config: dict, credentials: dict):
        self.connection_id = connection_id
        self.config = config
        self.credentials = credentials

    @abstractmethod
    async def test_connection(self) -> bool: ...

    @abstractmethod
    async def discover(self) -> DiscoveredSchema: ...

    @abstractmethod
    async def extract_full(self, object_types: list[str] | None = None) -> list[NormalizedRecord]: ...

    @abstractmethod
    async def extract_incremental(self, since: datetime, object_types: list[str] | None = None) -> list[NormalizedRecord]: ...

    @abstractmethod
    def get_capabilities(self) -> ConnectorCapabilities: ...

    def _compute_record_hash(self, data: dict) -> str:
        import hashlib
        import json

        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()
