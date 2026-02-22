"""Entity resolution tools — @function_tool wrappers for the resolution pipeline."""

from __future__ import annotations

import json

from agents import function_tool

from vesh_agents.resolution.blocking import BlockingEngine
from vesh_agents.resolution.canonical import compute_canonical_record
from vesh_agents.resolution.clustering import ClusteringEngine
from vesh_agents.resolution.scoring import ScoringEngine


@function_tool
def resolve_entities(records_json: str) -> str:
    """Resolve entities across data sources by matching and clustering records.

    Takes extracted records from multiple sources and identifies which records
    refer to the same real-world entity using email, name, and temporal matching.

    Args:
        records_json: JSON string of extracted records (from connector tools).
    """
    data = json.loads(records_json)
    records = data if isinstance(data, list) else data.get("records", [])

    if not records:
        return json.dumps({"entities": [], "entity_count": 0, "message": "No records to resolve"})

    sources: dict[str, list[dict]] = {}
    records_by_id: dict[str, dict] = {}
    for rec in records:
        source = rec.get("source_type", "unknown")
        sources.setdefault(source, []).append(rec)
        key = f"{source}:{rec.get('record_id', '')}"
        records_by_id[key] = rec

    source_list = list(sources.keys())

    if len(source_list) < 2:
        entities = []
        for rec in records:
            entity = rec.get("data", rec)
            entity["_sources"] = [{"source_type": rec.get("source_type"), "record_id": rec.get("record_id")}]
            entity["_source_count"] = 1
            entity["_confidence"] = 1.0
            entities.append(entity)
        return json.dumps({"entities": entities, "entity_count": len(entities), "source_count": 1}, default=str)

    blocking = BlockingEngine()
    scoring = ScoringEngine()
    clustering = ClusteringEngine()

    all_candidates = []
    for i in range(len(source_list)):
        for j in range(i + 1, len(source_list)):
            candidates = blocking.generate_candidates(
                sources[source_list[i]], source_list[i],
                sources[source_list[j]], source_list[j],
            )
            all_candidates.extend(candidates)

    scored = scoring.score_candidates(all_candidates, records_by_id)
    clusters = clustering.cluster(scored)

    entities = []
    matched_keys: set[str] = set()
    for cluster in clusters:
        canonical = compute_canonical_record(cluster, records_by_id)
        entities.append(canonical)
        for src, rid in cluster.members:
            matched_keys.add(f"{src}:{rid}")

    for key, rec in records_by_id.items():
        if key not in matched_keys:
            entity = rec.get("data", rec)
            entity["_sources"] = [{"source_type": rec.get("source_type"), "record_id": rec.get("record_id")}]
            entity["_source_count"] = 1
            entity["_confidence"] = 1.0
            entities.append(entity)

    return json.dumps({
        "entities": entities,
        "entity_count": len(entities),
        "clusters_found": len(clusters),
        "source_count": len(source_list),
    }, default=str)
