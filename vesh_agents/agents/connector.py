"""DataConnectorAgent — extracts and normalizes data from connected sources."""

from agents import Agent

from vesh_agents.tools.connectors import extract_postgres, extract_stripe, import_csv

INSTRUCTIONS = """You are the Data Connector Agent for Vesh AI.

Your role is to extract data from connected sources (CSV files, Stripe, PostgreSQL).
When the user provides a data source, use the appropriate tool to extract records.

Guidelines:
- For CSV files, use the import_csv tool with the file path.
- For Stripe, use extract_stripe with the API key.
- For PostgreSQL, use extract_postgres with connection details.
- Always confirm the number of records extracted and the source type.
- If extraction fails, explain the error clearly.

After extraction, pass the data to the Entity Resolver Agent for matching."""

data_connector_agent = Agent(
    name="DataConnector",
    instructions=INSTRUCTIONS,
    tools=[import_csv, extract_stripe, extract_postgres],
)
