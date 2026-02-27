FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY vesh_agents/ vesh_agents/

RUN pip install --no-cache-dir .

ENTRYPOINT ["vesh", "mcp", "serve"]
