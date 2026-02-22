"""JSON output formatter for pipeline results."""

from __future__ import annotations

import json
import sys
from typing import Any


def write_json(data: dict[str, Any], filepath: str | None = None, indent: int = 2) -> None:
    """Write pipeline results as JSON to a file or stdout."""
    output = json.dumps(data, indent=indent, default=str)
    if filepath:
        with open(filepath, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)
        sys.stdout.write("\n")
