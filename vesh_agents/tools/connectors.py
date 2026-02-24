"""Connector tools — @function_tool wrappers for data extraction."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agents import function_tool

from vesh_agents.connectors.csv import CsvConnector


@function_tool
def import_csv(file_path: str) -> str:
    """Import revenue data from a CSV file and return normalized records as JSON.

    Args:
        file_path: Path to the CSV file containing revenue/subscription data.
    """
    connector = CsvConnector(connection_id="csv-local", config={"file_path": file_path})
    records = asyncio.get_event_loop().run_until_complete(connector.extract_full())
    result = {
        "source": "csv",
        "file": file_path,
        "record_count": len(records),
        "records": [r.to_dict() for r in records[:500]],
    }
    return json.dumps(result, default=str)


@function_tool
def extract_stripe(object_types: str = "customer,subscription,invoice") -> str:
    """Extract data from Stripe using the STRIPE_API_KEY environment variable.

    Args:
        object_types: Comma-separated list of Stripe object types to extract.
    """
    import os

    from vesh_agents.connectors.stripe import StripeConnector

    api_key = os.environ.get("STRIPE_API_KEY", "")
    if not api_key:
        return json.dumps({"error": "STRIPE_API_KEY environment variable is not set"})
    types = [t.strip() for t in object_types.split(",")]
    connector = StripeConnector(connection_id="stripe-cli", config={}, credentials={"api_key": api_key})
    records = asyncio.get_event_loop().run_until_complete(connector.extract_full(types))
    result = {
        "source": "stripe",
        "record_count": len(records),
        "object_types": types,
        "records": [r.to_dict() for r in records[:500]],
    }
    return json.dumps(result, default=str)


@function_tool
def extract_postgres(host: str, port: int, database: str, schema: str = "public") -> str:
    """Extract data from a PostgreSQL database.

    Credentials are read from PGUSER and PGPASSWORD environment variables.

    Args:
        host: Database hostname.
        port: Database port.
        database: Database name.
        schema: Schema to extract from (default: public).
    """
    import os

    from vesh_agents.connectors.postgres import PostgresConnector

    user = os.environ.get("PGUSER", "")
    password = os.environ.get("PGPASSWORD", "")
    if not user:
        return json.dumps({"error": "PGUSER environment variable is not set"})
    connector = PostgresConnector(
        connection_id="pg-cli",
        config={"host": host, "port": port, "database": database, "schema": schema},
        credentials={"user": user, "password": password},
    )
    records = asyncio.get_event_loop().run_until_complete(connector.extract_full())
    result = {
        "source": "postgres",
        "record_count": len(records),
        "records": [r.to_dict() for r in records[:500]],
    }
    return json.dumps(result, default=str)


def _parse_records(raw_json: str) -> list[dict[str, Any]]:
    """Parse records from JSON tool output."""
    data = json.loads(raw_json)
    return data.get("records", [])
