"""Tests for data connectors."""

import asyncio
import os
from pathlib import Path

import pytest

from vesh_agents.connectors.base import BaseConnector, ChangeType, ConnectorCapabilities, NormalizedRecord
from vesh_agents.connectors.csv import CsvConnector, _detect_column_type, _resolve_field

SAMPLE_CSV = Path(__file__).parent.parent / "examples" / "sample_data.csv"


class TestColumnTypeDetection:
    def test_numeric_values(self):
        assert _detect_column_type(["100", "200.5", "300"]) == "numeric"

    def test_currency_values(self):
        assert _detect_column_type(["$100", "$200.50", "$300"]) == "numeric"

    def test_string_values(self):
        assert _detect_column_type(["hello", "world", "foo"]) == "string"

    def test_timestamp_values(self):
        assert _detect_column_type(["2024-01-15", "2024-02-20", "2024-03-25"]) == "timestamp"

    def test_empty_values(self):
        assert _detect_column_type(["", "", ""]) == "string"

    def test_mixed_values_majority_numeric(self):
        values = ["100", "200", "300", "400", "500", "600", "700", "800", "900", "foo"]
        assert _detect_column_type(values) == "numeric"


class TestFieldResolution:
    def test_resolves_exact_match(self):
        assert _resolve_field(["email", "name"], ["email"]) == "email"

    def test_resolves_case_insensitive(self):
        assert _resolve_field(["Email", "Name"], ["email"]) == "Email"

    def test_returns_none_when_no_match(self):
        assert _resolve_field(["foo", "bar"], ["email"]) is None

    def test_resolves_first_alias(self):
        headers = ["contact_email", "name"]
        aliases = ["email", "email_address", "contact_email"]
        assert _resolve_field(headers, aliases) == "contact_email"


class TestCsvConnector:
    def test_capabilities(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        caps = connector.get_capabilities()
        assert isinstance(caps, ConnectorCapabilities)
        assert caps.read_only is True
        assert caps.supports_cdc is False

    @pytest.mark.asyncio
    async def test_connection_success(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        assert await connector.test_connection() is True

    @pytest.mark.asyncio
    async def test_connection_failure_missing_file(self):
        connector = CsvConnector("test", {"file_path": "/nonexistent/file.csv"})
        assert await connector.test_connection() is False

    @pytest.mark.asyncio
    async def test_extract_full(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        records = await connector.extract_full()
        assert len(records) == 40
        assert all(isinstance(r, NormalizedRecord) for r in records)
        assert all(r.source_type == "csv" for r in records)
        assert all(r.change_type == ChangeType.CREATE for r in records)

    @pytest.mark.asyncio
    async def test_extract_has_data(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        records = await connector.extract_full()
        first = records[0]
        assert "email" in first.data or "company_name" in first.data
        assert first.record_id is not None
        assert first.record_hash is not None

    @pytest.mark.asyncio
    async def test_discover_schema(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        schema = await connector.discover()
        assert schema.source_type == "csv"
        assert len(schema.tables) == 1
        table = schema.tables[0]
        column_names = [c.column_name for c in table.columns]
        assert "email" in column_names
        assert "mrr_amount" in column_names
        assert table.row_count_estimate == 40

    @pytest.mark.asyncio
    async def test_discover_detects_semantic_types(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        schema = await connector.discover()
        columns = {c.column_name: c for c in schema.tables[0].columns}
        assert columns["email"].semantic_type == "email"
        assert columns["status"].semantic_type == "status"

    @pytest.mark.asyncio
    async def test_numeric_values_parsed(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        records = await connector.extract_full()
        mrr_values = [r.data.get("mrr_amount") for r in records if r.data.get("mrr_amount") is not None]
        assert all(isinstance(v, float) for v in mrr_values)

    @pytest.mark.asyncio
    async def test_record_hashes_unique(self):
        connector = CsvConnector("test", {"file_path": str(SAMPLE_CSV)})
        records = await connector.extract_full()
        hashes = [r.record_hash for r in records]
        assert len(hashes) == len(set(hashes))
