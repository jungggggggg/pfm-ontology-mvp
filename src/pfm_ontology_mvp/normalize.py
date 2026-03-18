from __future__ import annotations

import yaml
import numpy as np
from pathlib import Path
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer

from .schema import CandidateBundle, NodeCandidate
from .settings import ONTOLOGY_DIR, EMBEDDING_MODEL, FUZZY_MATCH_THRESHOLD, SEMANTIC_MATCH_THRESHOLD
from .utils import read_jsonl


class Normalizer:
    def __init__(self, aliases_path: Path | None = None) -> None:
        self.aliases_path = aliases_path or (ONTOLOGY_DIR / "aliases.yaml")
        raw = yaml.safe_load(self.aliases_path.read_text(encoding="utf-8")) or {}
        self.aliases = {k.lower().strip(): v.strip() for k, v in raw.get("aliases", {}).items()}
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

    def normalize_bundle(self, bundle: CandidateBundle, existing_nodes: list[dict]) -> CandidateBundle:
        if existing_nodes:
            existing_labels = [node["label"] for node in existing_nodes]
            existing_embeddings = self.embedder.encode(existing_labels, normalize_embeddings=True)
        else:
            existing_labels = []
            existing_embeddings = np.empty((0, 384), dtype=float)

        for node in bundle.nodes:
            node.canonical_label = self._canonicalize(node.label)
            matched = self._match_existing(node, existing_labels, existing_embeddings)
            if matched:
                node.matched_existing = matched
                node.canonical_label = matched
                node.confidence = max(node.confidence, 0.88)

        label_to_canonical = {node.label: node.canonical_label or node.label for node in bundle.nodes}
        for edge in bundle.edges:
            edge.canonical_source = self._canonicalize(label_to_canonical.get(edge.source, edge.source))
            edge.canonical_target = self._canonicalize(label_to_canonical.get(edge.target, edge.target))
            if edge.canonical_source == edge.canonical_target:
                edge.confidence = min(edge.confidence, 0.2)

        return bundle

    def _canonicalize(self, label: str) -> str:
        text = label.strip()
        return self.aliases.get(text.lower(), text)

    def _match_existing(self, node: NodeCandidate, existing_labels: list[str], existing_embeddings) -> str | None:
        candidate = node.canonical_label or node.label
        if candidate in existing_labels:
            return candidate

        best_fuzzy_label = None
        best_fuzzy_score = -1
        for existing in existing_labels:
            score = fuzz.ratio(candidate.lower(), existing.lower())
            if score > best_fuzzy_score:
                best_fuzzy_score = score
                best_fuzzy_label = existing
        if best_fuzzy_label and best_fuzzy_score >= FUZZY_MATCH_THRESHOLD:
            return best_fuzzy_label

        if existing_labels:
            vec = self.embedder.encode([candidate], normalize_embeddings=True)
            sims = np.dot(existing_embeddings, vec[0])
            idx = int(np.argmax(sims))
            if float(sims[idx]) >= SEMANTIC_MATCH_THRESHOLD:
                return existing_labels[idx]
        return None


def load_existing_nodes(store_dir: Path) -> list[dict]:
    return read_jsonl(store_dir / "nodes.jsonl")
