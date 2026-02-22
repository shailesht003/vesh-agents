"""Custom trace processor for Vesh AI agent runs.

Captures agent execution data (timing, tool calls, handoffs) and either
writes to a local JSON file or sends to the Vesh cloud API.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentSpan:
    """A single span in an agent execution trace."""

    agent_name: str
    tool_name: str | None = None
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "running"
    input_summary: str = ""
    output_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


@dataclass
class AgentTrace:
    """Complete trace of a pipeline run."""

    run_id: str
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    status: str = "running"
    spans: list[AgentSpan] = field(default_factory=list)
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def add_span(self, span: AgentSpan) -> None:
        self.spans.append(span)

    def complete(self, status: str = "success") -> None:
        self.completed_at = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        end = self.completed_at or time.time()
        return (end - self.started_at) * 1000

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_local(self, path: str | Path = ".vesh/traces") -> Path:
        """Save trace to a local JSON file."""
        out_dir = Path(path)
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / f"{self.run_id}.json"
        filepath.write_text(json.dumps(self.to_dict(), indent=2, default=str))
        return filepath
