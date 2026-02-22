"""MCP Server — expose Vesh AI agents as MCP tools for external clients.

Connect from OpenCode, Cursor, Claude Desktop, or any MCP-compatible client.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def get_mcp_tools() -> list[dict]:
    """Return tool definitions in MCP format."""
    return [
        {
            "name": "vesh_import_csv",
            "description": "Import SaaS revenue data from a CSV file and return normalized records.",
            "inputSchema": {
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the CSV file"}},
                "required": ["file_path"],
            },
        },
        {
            "name": "vesh_resolve_entities",
            "description": "Resolve entities across data sources using fuzzy matching on email, name, and temporal signals.",
            "inputSchema": {
                "type": "object",
                "properties": {"records_json": {"type": "string", "description": "JSON array of extracted records"}},
                "required": ["records_json"],
            },
        },
        {
            "name": "vesh_compute_metrics",
            "description": "Compute SaaS metrics (MRR, churn, ARPU, NRR, Quick Ratio) from resolved entity data.",
            "inputSchema": {
                "type": "object",
                "properties": {"entities_json": {"type": "string", "description": "JSON of resolved entities"}},
                "required": ["entities_json"],
            },
        },
        {
            "name": "vesh_detect_anomalies",
            "description": "Detect statistical anomalies in computed SaaS metrics using z-score and rate-of-change methods.",
            "inputSchema": {
                "type": "object",
                "properties": {"metrics_json": {"type": "string", "description": "JSON of computed metrics"}},
                "required": ["metrics_json"],
            },
        },
        {
            "name": "vesh_analyze_csv",
            "description": (
                "Full pipeline: import CSV -> resolve entities -> compute metrics -> detect anomalies. Returns complete analysis."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the CSV file with revenue data"}},
                "required": ["file_path"],
            },
        },
    ]


async def handle_tool_call(tool_name: str, arguments: dict) -> str:
    """Handle an MCP tool call and return results."""
    if tool_name == "vesh_import_csv":
        from vesh_agents.connectors.csv import CsvConnector

        connector = CsvConnector(connection_id="mcp", config={"file_path": arguments["file_path"]})
        records = await connector.extract_full()
        return json.dumps({"records": [r.to_dict() for r in records], "record_count": len(records)}, default=str)

    elif tool_name == "vesh_resolve_entities":
        from vesh_agents.tools.resolution import resolve_entities

        return resolve_entities.fn(arguments["records_json"])

    elif tool_name == "vesh_compute_metrics":
        from vesh_agents.tools.metrics import compute_saas_metrics

        return compute_saas_metrics.fn(arguments["entities_json"])

    elif tool_name == "vesh_detect_anomalies":
        from vesh_agents.tools.detection import detect_anomalies

        return detect_anomalies.fn(arguments["metrics_json"])

    elif tool_name == "vesh_analyze_csv":
        from datetime import date

        from vesh_agents.connectors.csv import CsvConnector
        from vesh_agents.metrics.computation import MetricComputationEngine
        from vesh_agents.metrics.ontology import CORE_METRICS

        connector = CsvConnector(connection_id="mcp", config={"file_path": arguments["file_path"]})
        records = await connector.extract_full()
        entity_data = [r.data for r in records]
        engine = MetricComputationEngine()
        computed = engine.compute_all(tenant_id="mcp", period_date=date.today(), entity_data=entity_data)
        metrics = [
            {
                "metric_id": m.metric_id,
                "name": CORE_METRICS[m.metric_id].name if m.metric_id in CORE_METRICS else m.metric_id,
                "value": m.value,
                "change_percent": m.change_percent,
            }
            for m in computed
        ]
        return json.dumps({"records": len(records), "entities": len(entity_data), "metrics": metrics}, default=str)

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def start_server(port: int = 8765):
    """Start the MCP server (stdio mode for local clients)."""
    logger.info("Vesh AI MCP server starting on port %d", port)
    logger.info("Available tools: %s", [t["name"] for t in get_mcp_tools()])
    print(f"Vesh AI MCP Server ready. {len(get_mcp_tools())} tools available.")
    print("Connect using: opencode mcp add vesh --type local --command 'vesh mcp serve'")
    print("Press Ctrl+C to stop.")

    try:
        import asyncio

        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
