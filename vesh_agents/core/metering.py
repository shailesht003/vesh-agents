"""API key management and cloud metering client.

Handles authentication with Vesh AI cloud for premium features
(benchmarks, historical tracking, managed pipelines).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

VESH_CLOUD_URL = os.environ.get("VESH_CLOUD_URL", "https://cloud.veshai.com")
CONFIG_DIR = Path.home() / ".vesh"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_api_key() -> str | None:
    return load_config().get("api_key")


def set_api_key(key: str) -> None:
    config = load_config()
    config["api_key"] = key
    save_config(config)


def get_cloud_url() -> str:
    return load_config().get("cloud_url", VESH_CLOUD_URL)


async def send_trace(trace_data: dict[str, Any]) -> dict | None:
    """Send a trace to Vesh cloud (optional, only if API key is set)."""
    api_key = get_api_key()
    if not api_key:
        return None

    url = f"{get_cloud_url()}/api/v1/cloud/trace"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=trace_data, headers={"X-API-Key": api_key})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return None
