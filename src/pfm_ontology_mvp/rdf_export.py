from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

from .settings import STORE_DIR
from .utils import read_jsonl, slugify


EX = Namespace("http://example.org/pfm/")


class RDFExporter:
    def __init__(self) -> None:
        self.graph = Graph()
        self.graph.bind("ex", EX)
        self.graph.bind("rdfs", RDFS)

    def export(self, out_path: Path | None = None) -> Path:
        out_path = out_path or (STORE_DIR / "ontology.ttl")
        self._load_schema()
        self._load_nodes()
        self._load_edges()
        self.graph.serialize(destination=str(out_path), format="turtle")
        return out_path

    def _class_uri(self, class_name: str) -> URIRef:
        return EX[slugify(class_name)]

    def _node_uri(self, label: str) -> URIRef:
        return EX["node/" + slugify(label)]

    def _relation_uri(self, label: str) -> URIRef:
        return EX[slugify(label)]

    def _load_schema(self) -> None:
        import yaml
        from .settings import ONTOLOGY_DIR

        seed = yaml.safe_load((ONTOLOGY_DIR / "seed_schema.yaml").read_text(encoding="utf-8"))
        for item in seed.get("classes", []):
            class_uri = self._class_uri(item["label"])
            self.graph.add((class_uri, RDF.type, RDFS.Class))
            self.graph.add((class_uri, RDFS.label, Literal(item["label"])))
        for item in seed.get("relations", []):
            rel_uri = self._relation_uri(item["label"])
            self.graph.add((rel_uri, RDF.type, RDF.Property))
            self.graph.add((rel_uri, RDFS.label, Literal(item["label"])))
            self.graph.add((rel_uri, RDFS.domain, self._class_uri(item["domain"])))
            self.graph.add((rel_uri, RDFS.range, self._class_uri(item["range"])))

    def _load_nodes(self) -> None:
        for row in read_jsonl(STORE_DIR / "nodes.jsonl"):
            node_uri = self._node_uri(row["label"])
            class_uri = self._class_uri(row["type"])
            self.graph.add((node_uri, RDF.type, class_uri))
            self.graph.add((node_uri, RDFS.label, Literal(row["label"])))
            self.graph.add((node_uri, EX.sourcePaper, Literal(row.get("source_paper", ""))))
            self.graph.add((node_uri, EX.evidence, Literal(row.get("evidence", ""))))
            for alias in row.get("aliases", []):
                self.graph.add((node_uri, EX.alias, Literal(alias)))

    def _load_edges(self) -> None:
        for row in read_jsonl(STORE_DIR / "edges.jsonl"):
            s = self._node_uri(row["source"])
            p = self._relation_uri(row["relation"])
            o = self._node_uri(row["target"])
            self.graph.add((s, p, o))
