"""PostgreSQL connector — standalone, uses psycopg3 directly (no SQLAlchemy)."""

import logging
from datetime import UTC, datetime
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

PAGE_SIZE = 5000
SAMPLE_SIZE = 50


class PostgresConnector(BaseConnector):
    """Connector for PostgreSQL databases — schema discovery + extraction."""

    def __init__(self, connection_id: str, config: dict, credentials: dict):
        super().__init__(connection_id, config, credentials)
        self._conn = None

    def _get_dsn(self) -> str:
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        database = self.config.get("database", "")
        user = self.credentials.get("user", "")
        password = self.credentials.get("password", "")
        return f"host={host} port={port} dbname={database} user={user} password={password}"

    def _get_conn(self):
        if self._conn is None:
            try:
                import psycopg
            except ImportError:
                raise ImportError(
                    "Postgres connector requires 'psycopg' package. Install with: pip install vesh-agents[postgres]"
                )
            self._conn = psycopg.connect(self._get_dsn(), autocommit=True)
        return self._conn

    def get_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_cdc=False, supports_incremental=True, supports_schema_introspection=True, read_only=True
        )

    async def test_connection(self) -> bool:
        try:
            conn = self._get_conn()
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def discover(self) -> DiscoveredSchema:
        conn = self._get_conn()
        schema_name = self.config.get("schema", "public")
        tables: list[TableSchema] = []

        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (schema_name,),
            )
            table_names = [row[0] for row in cur.fetchall()]

        for table_name in table_names:
            columns: list[ColumnSchema] = []
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                    (schema_name, table_name),
                )
                for col_name, data_type, nullable in cur.fetchall():
                    columns.append(ColumnSchema(column_name=col_name, data_type=data_type, nullable=(nullable == "YES")))
            tables.append(TableSchema(table_name=table_name, columns=columns))

        return DiscoveredSchema(source_type="postgres", tables=tables)

    async def extract_full(self, object_types: list[str] | None = None) -> list[NormalizedRecord]:
        conn = self._get_conn()
        schema_name = self.config.get("schema", "public")
        records: list[NormalizedRecord] = []
        now = datetime.now(UTC)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (schema_name,),
            )
            all_tables = [row[0] for row in cur.fetchall()]

        targets = object_types or all_tables
        for table_name in targets:
            if table_name not in all_tables:
                continue
            offset = 0
            while True:
                with conn.cursor() as cur:
                    cur.execute(
                        f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT %s OFFSET %s',  # noqa: S608
                        (PAGE_SIZE, offset),
                    )
                    cols = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()

                if not rows:
                    break
                for row in rows:
                    row_dict = dict(zip(cols, row))
                    record_id = str(row_dict.get("id", offset))
                    records.append(
                        NormalizedRecord(
                            source_type="postgres",
                            source_id=self.connection_id,
                            object_type=table_name,
                            record_id=record_id,
                            data=row_dict,
                            extracted_at=now,
                            change_type=ChangeType.CREATE,
                            record_hash=self._compute_record_hash(row_dict),
                        )
                    )
                offset += PAGE_SIZE
        return records

    async def extract_incremental(self, since: datetime, object_types: list[str] | None = None) -> list[NormalizedRecord]:
        conn = self._get_conn()
        schema_name = self.config.get("schema", "public")
        records: list[NormalizedRecord] = []
        now = datetime.now(UTC)
        timestamp_candidates = ["updated_at", "modified_at", "updated_date", "last_modified"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (schema_name,),
            )
            all_tables = [row[0] for row in cur.fetchall()]

        targets = object_types or all_tables
        for table_name in targets:
            if table_name not in all_tables:
                continue

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s",
                    (schema_name, table_name),
                )
                col_names = [row[0] for row in cur.fetchall()]

            ts_col = next((c for c in timestamp_candidates if c in col_names), None)
            if not ts_col:
                continue

            with conn.cursor() as cur:
                cur.execute(
                    f'SELECT * FROM "{schema_name}"."{table_name}" WHERE "{ts_col}" > %s ORDER BY "{ts_col}" ASC',  # noqa: S608
                    (since,),
                )
                cols = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    record_id = str(row_dict.get("id", ""))
                    records.append(
                        NormalizedRecord(
                            source_type="postgres",
                            source_id=self.connection_id,
                            object_type=table_name,
                            record_id=record_id,
                            data=row_dict,
                            extracted_at=now,
                            change_type=ChangeType.UPDATE,
                            record_hash=self._compute_record_hash(row_dict),
                        )
                    )
        return records
