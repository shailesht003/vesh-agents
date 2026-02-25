"""CSV connector — import revenue data from CSV files for quick analysis.

Supports common SaaS data exports (Stripe, ChartMogul, Baremetrics, etc.)
and generic CSV files with auto-detected column types.
"""

import csv
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vesh_agents.connectors.base import (
    BaseConnector,
    ChangeType,
    ColumnSchema,
    ConnectorCapabilities,
    DiscoveredSchema,
    NormalizedRecord,
    TableSchema,
)

logger = logging.getLogger(__name__)

REVENUE_FIELD_ALIASES = {
    "mrr": ["mrr", "monthly_recurring_revenue", "mrr_amount", "revenue"],
    "email": ["email", "email_address", "customer_email", "contact_email"],
    "name": ["name", "company_name", "company", "customer_name", "account_name"],
    "plan": ["plan", "plan_name", "subscription_plan", "tier", "pricing_plan"],
    "status": ["status", "subscription_status", "state", "account_status"],
    "created_at": ["created_at", "created", "signup_date", "created_date", "start_date"],
    "customer_id": ["customer_id", "id", "account_id", "stripe_customer_id", "external_id"],
}


def _detect_column_type(values: list[str]) -> str:
    """Heuristic type detection from sample values."""
    numeric_count = 0
    date_count = 0
    for v in values[:20]:
        if not v:
            continue
        try:
            float(v.replace(",", "").replace("$", "").replace("£", "").replace("€", ""))
            numeric_count += 1
        except ValueError:
            pass
        if any(sep in v for sep in ["-", "/", "T"]) and len(v) >= 8:
            date_count += 1

    total = len([v for v in values[:20] if v])
    if total == 0:
        return "string"
    if numeric_count / max(total, 1) > 0.8:
        return "numeric"
    if date_count / max(total, 1) > 0.5:
        return "timestamp"
    return "string"


def _resolve_field(headers: list[str], aliases: list[str]) -> str | None:
    """Find a column header that matches one of the known aliases."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for alias in aliases:
        if alias in lower_headers:
            return lower_headers[alias]
    return None


class CsvConnector(BaseConnector):
    """Import SaaS data from CSV files."""

    def __init__(self, connection_id: str, config: dict, credentials: dict | None = None):
        super().__init__(connection_id, config, credentials or {})
        self.file_path = Path(config.get("file_path", ""))
        self._rows: list[dict[str, str]] | None = None
        self._headers: list[str] = []

    def _load(self) -> list[dict[str, str]]:
        if self._rows is not None:
            return self._rows
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        with open(self.file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self._headers = reader.fieldnames or []
            self._rows = list(reader)
        logger.info("Loaded %d rows from %s", len(self._rows), self.file_path.name)
        return self._rows

    def get_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_cdc=False, supports_incremental=False, supports_schema_introspection=True, read_only=True
        )

    async def test_connection(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False

    async def discover(self) -> DiscoveredSchema:
        rows = self._load()
        columns: list[ColumnSchema] = []
        for header in self._headers:
            values = [r.get(header, "") for r in rows[:50]]
            col_type = _detect_column_type(values)
            semantic = None
            for semantic_name, aliases in REVENUE_FIELD_ALIASES.items():
                if header.lower().strip() in aliases:
                    semantic = semantic_name
                    break
            columns.append(
                ColumnSchema(
                    column_name=header,
                    data_type=col_type,
                    semantic_type=semantic,
                    sample_values=values[:5],
                )
            )
        table_name = self.file_path.stem if self.file_path else "data"
        return DiscoveredSchema(
            source_type="csv",
            tables=[TableSchema(table_name=table_name, columns=columns, row_count_estimate=len(rows))],
        )

    async def extract_full(
        self, object_types: list[str] | None = None, progress_callback: Callable[[int, int | None], None] | None = None
    ) -> list[NormalizedRecord]:
        rows = self._load()
        now = datetime.now(UTC)
        records: list[NormalizedRecord] = []
        table_name = self.file_path.stem if self.file_path else "data"
        total_rows = len(rows)

        id_col = _resolve_field(self._headers, REVENUE_FIELD_ALIASES["customer_id"])
        for idx, row in enumerate(rows):
            data: dict[str, Any] = {}
            for k, v in row.items():
                if v == "":
                    data[k] = None
                else:
                    try:
                        data[k] = float(v.replace(",", "").replace("$", "").replace("£", "").replace("€", ""))
                    except (ValueError, AttributeError):
                        data[k] = v

            record_id = str(data.get(id_col, idx)) if id_col else str(idx)
            records.append(
                NormalizedRecord(
                    source_type="csv",
                    source_id=self.connection_id,
                    object_type=table_name,
                    record_id=record_id,
                    data=data,
                    extracted_at=now,
                    change_type=ChangeType.CREATE,
                    record_hash=self._compute_record_hash(data),
                )
            )
            if progress_callback and (idx + 1) % 1000 == 0:
                progress_callback(idx + 1, total_rows)

        if progress_callback:
            progress_callback(total_rows, total_rows)

        return records

    async def extract_incremental(
        self,
        since: datetime,
        object_types: list[str] | None = None,
        progress_callback: Callable[[int, int | None], None] | None = None,
    ) -> list[NormalizedRecord]:
        return await self.extract_full(object_types, progress_callback)
