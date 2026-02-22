"""Tests for CSV connector and base classes."""

import asyncio
import os
import tempfile

from vesh_agents.connectors.csv import CsvConnector


def test_csv_connector_load():
    """Test CSV connector can load and extract records."""
    csv_content = (
        "customer_id,email,company_name,plan,status,mrr_amount\n"
        "c1,alice@acme.com,Acme Corp,growth,active,1200\n"
        "c2,bob@beta.io,Beta Inc,starter,active,299\n"
        "c3,carol@gamma.co,Gamma LLC,enterprise,canceled,5000\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        path = f.name

    try:
        connector = CsvConnector(connection_id="test", config={"file_path": path})
        records = asyncio.get_event_loop().run_until_complete(connector.extract_full())
        assert len(records) == 3
        assert records[0].source_type == "csv"
        assert records[0].data["email"] == "alice@acme.com"
        assert records[0].data["mrr_amount"] == 1200.0
    finally:
        os.unlink(path)


def test_csv_connector_discover():
    """Test CSV connector discovers schema with semantic types."""
    csv_content = (
        "customer_id,email,mrr,plan\n"
        "c1,alice@acme.com,1200,growth\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        path = f.name

    try:
        connector = CsvConnector(connection_id="test", config={"file_path": path})
        schema = asyncio.get_event_loop().run_until_complete(connector.discover())
        assert schema.source_type == "csv"
        assert len(schema.tables) == 1
        col_names = [c.column_name for c in schema.tables[0].columns]
        assert "email" in col_names
        assert "mrr" in col_names
    finally:
        os.unlink(path)
