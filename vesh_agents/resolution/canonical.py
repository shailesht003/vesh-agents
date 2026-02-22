"""Canonical (golden) record computation — builds the best-known representation of each entity."""

import logging
from typing import Any

from vesh_agents.resolution.clustering import EntityCluster

logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {
    "stripe": 3,
    "postgres": 2,
    "mysql": 2,
    "hubspot": 1,
    "salesforce": 1,
    "csv": 1,
}

FIELD_SOURCE_PRIORITY = {
    "email": ["stripe", "hubspot", "postgres"],
    "company_name": ["hubspot", "salesforce", "postgres", "stripe"],
    "mrr": ["stripe"],
    "plan": ["stripe"],
    "seats": ["postgres"],
    "created_at": ["stripe", "postgres"],
}


def compute_canonical_record(cluster: EntityCluster, records_by_key: dict[str, dict]) -> dict[str, Any]:
    """Compute the golden record for an entity cluster.

    For each field, prefer the value from the highest-priority source,
    then fall back to the most recently updated value.
    """
    canonical: dict[str, Any] = {}
    field_sources: dict[str, list[tuple[int, str, Any]]] = {}

    for source_type, record_id in cluster.members:
        key = f"{source_type}:{record_id}"
        record = records_by_key.get(key)
        if not record:
            continue
        data = record.get("data", record)
        priority = SOURCE_PRIORITY.get(source_type, 0)
        for field_name, value in data.items():
            if value is None or field_name.startswith("_"):
                continue
            field_sources.setdefault(field_name, []).append((priority, source_type, value))

    for field_name, sources in field_sources.items():
        priority_order = FIELD_SOURCE_PRIORITY.get(field_name)
        if priority_order:
            for preferred_source in priority_order:
                for _priority, source, value in sources:
                    if source == preferred_source:
                        canonical[field_name] = value
                        break
                if field_name in canonical:
                    break

        if field_name not in canonical:
            sources.sort(key=lambda x: x[0], reverse=True)
            canonical[field_name] = sources[0][2]

    canonical["_sources"] = [{"source_type": s, "record_id": r} for s, r in cluster.members]
    canonical["_source_count"] = len(cluster.members)
    canonical["_confidence"] = cluster.avg_confidence
    return canonical
