from __future__ import annotations

from pathlib import Path
import yaml

from .schema import CandidateBundle, SeedSchema, StoreNode, StoreEdge
from .utils import append_jsonl, read_jsonl
from .settings import ONTOLOGY_DIR, STORE_DIR, PROPOSALS_DIR, AUTO_ACCEPT_CONFIDENCE


class OntologyStore:
    def __init__(self) -> None:
        self.nodes_path = STORE_DIR / "nodes.jsonl"
        self.edges_path = STORE_DIR / "edges.jsonl"
        self.proposed_nodes_path = PROPOSALS_DIR / "proposed_nodes.jsonl"
        self.proposed_edges_path = PROPOSALS_DIR / "proposed_edges.jsonl"
        self.seed_schema = self._load_seed_schema()
        self.allowed_classes = {item.label for item in self.seed_schema.classes}
        self.allowed_relations = {item.label: item for item in self.seed_schema.relations}

    def _load_seed_schema(self) -> SeedSchema:
        path = ONTOLOGY_DIR / "seed_schema.yaml"
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return SeedSchema.model_validate(raw)

    def existing_nodes(self) -> list[dict]:
        return read_jsonl(self.nodes_path)

    def ingest(self, bundle: CandidateBundle) -> tuple[list[StoreNode], list[StoreEdge], list[dict], list[dict]]:
        accepted_nodes: list[StoreNode] = []
        accepted_edges: list[StoreEdge] = []
        proposed_nodes: list[dict] = []
        proposed_edges: list[dict] = []

        existing_node_rows = self.existing_nodes()
        existing_labels = {row["label"] for row in existing_node_rows}
        node_type_index = {row["label"]: row["type"] for row in existing_node_rows}

        local_types = {}
        for node in bundle.nodes:
            canonical = node.canonical_label or node.label
            local_types[canonical] = node.type
            if node.type not in self.allowed_classes:
                proposed_nodes.append({**node.model_dump(), "reason": "unknown_class"})
                continue
            if node.confidence >= AUTO_ACCEPT_CONFIDENCE or canonical in existing_labels:
                accepted_nodes.append(
                    StoreNode(
                        label=canonical,
                        type=node.type,
                        source_paper=node.paper_id,
                        evidence=node.evidence,
                        aliases=[node.label] if node.label != canonical else [],
                    )
                )
            else:
                proposed_nodes.append({**node.model_dump(), "reason": "low_confidence_or_new_node"})

        accepted_node_labels = {node.label for node in accepted_nodes} | existing_labels

        for edge in bundle.edges:
            relation = self.allowed_relations.get(edge.relation)
            if not relation:
                proposed_edges.append({**edge.model_dump(), "reason": "unknown_relation"})
                continue

            source = edge.canonical_source or edge.source
            target = edge.canonical_target or edge.target

            source_type = local_types.get(source) or node_type_index.get(source)
            target_type = local_types.get(target) or node_type_index.get(target)

            if source not in accepted_node_labels or target not in accepted_node_labels:
                proposed_edges.append({**edge.model_dump(), "reason": "source_or_target_not_accepted"})
                continue
            if source_type != relation.domain or target_type != relation.range:
                proposed_edges.append({**edge.model_dump(), "reason": f"domain_range_mismatch:{source_type}->{target_type}"})
                continue
            if edge.confidence >= AUTO_ACCEPT_CONFIDENCE:
                accepted_edges.append(
                    StoreEdge(
                        source=source,
                        relation=edge.relation,
                        target=target,
                        source_paper=edge.paper_id,
                        evidence=edge.evidence,
                    )
                )
            else:
                proposed_edges.append({**edge.model_dump(), "reason": "low_confidence"})

        self._write_unique_nodes(accepted_nodes)
        self._write_unique_edges(accepted_edges)
        append_jsonl(self.proposed_nodes_path, proposed_nodes)
        append_jsonl(self.proposed_edges_path, proposed_edges)
        return accepted_nodes, accepted_edges, proposed_nodes, proposed_edges

    def _write_unique_nodes(self, nodes: list[StoreNode]) -> None:
        existing = {(row["label"], row["type"]) for row in read_jsonl(self.nodes_path)}
        new_rows = []
        for node in nodes:
            key = (node.label, node.type)
            if key not in existing:
                new_rows.append(node.model_dump())
                existing.add(key)
        append_jsonl(self.nodes_path, new_rows)

    def _write_unique_edges(self, edges: list[StoreEdge]) -> None:
        existing = {(row["source"], row["relation"], row["target"]) for row in read_jsonl(self.edges_path)}
        new_rows = []
        for edge in edges:
            key = (edge.source, edge.relation, edge.target)
            if key not in existing:
                new_rows.append(edge.model_dump())
                existing.add(key)
        append_jsonl(self.edges_path, new_rows)
