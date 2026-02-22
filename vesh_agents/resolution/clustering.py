"""Entity clustering — groups scored pairs into entity clusters using Union-Find."""

import logging
from dataclasses import dataclass, field

from vesh_agents.resolution.scoring import PairScore

logger = logging.getLogger(__name__)


@dataclass
class EntityCluster:
    """A cluster of source records that represent the same real-world entity."""

    cluster_id: str
    members: list[tuple[str, str]]
    max_confidence: float
    avg_confidence: float
    pair_scores: list[PairScore] = field(default_factory=list)


class UnionFind:
    """Weighted Union-Find with path compression for entity clustering."""

    def __init__(self):
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        root_x, root_y = self.find(x), self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1


class ClusteringEngine:
    """Cluster scored pairs into entity groups using Union-Find."""

    def __init__(self, high_confidence_threshold: float = 0.50, auto_merge_threshold: float = 0.70):
        self.high_threshold = high_confidence_threshold
        self.auto_merge_threshold = auto_merge_threshold

    def cluster(self, scored_pairs: list[PairScore]) -> list[EntityCluster]:
        uf = UnionFind()
        pair_map: dict[str, list[PairScore]] = {}

        for pair in scored_pairs:
            if pair.total_score < self.high_threshold:
                continue
            key_a = f"{pair.record_a_source}:{pair.record_a_id}"
            key_b = f"{pair.record_b_source}:{pair.record_b_id}"
            uf.union(key_a, key_b)
            root = uf.find(key_a)
            pair_map.setdefault(root, []).append(pair)

        components: dict[str, set[str]] = {}
        for key in uf.parent:
            root = uf.find(key)
            components.setdefault(root, set()).add(key)

        clusters: list[EntityCluster] = []
        for root, members_set in components.items():
            members = []
            for m in members_set:
                parts = m.split(":", 1)
                if len(parts) == 2:
                    members.append((parts[0], parts[1]))
            if len(members) < 2:
                continue
            pairs = pair_map.get(root, [])
            scores = [p.total_score for p in pairs]
            clusters.append(
                EntityCluster(
                    cluster_id=root, members=members,
                    max_confidence=max(scores) if scores else 0.0,
                    avg_confidence=sum(scores) / len(scores) if scores else 0.0,
                    pair_scores=pairs,
                )
            )
        logger.info("Clustered into %d entities from %d scored pairs", len(clusters), len(scored_pairs))
        return clusters

    def get_review_candidates(self, scored_pairs: list[PairScore]) -> list[PairScore]:
        return [p for p in scored_pairs if self.high_threshold <= p.total_score < self.auto_merge_threshold]
