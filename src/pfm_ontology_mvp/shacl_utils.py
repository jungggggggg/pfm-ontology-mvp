from __future__ import annotations

from pathlib import Path
import yaml
from rdflib import Graph, Namespace, RDF, URIRef, Literal
from pyshacl import validate

from .settings import ONTOLOGY_DIR, STORE_DIR
from .utils import slugify


EX = Namespace("http://example.org/pfm/")
SH = Namespace("http://www.w3.org/ns/shacl#")


class SHACLBuilder:
    def __init__(self) -> None:
        self.seed = yaml.safe_load((ONTOLOGY_DIR / "seed_schema.yaml").read_text(encoding="utf-8"))

    def build_shapes(self, out_path: Path | None = None) -> Path:
        out_path = out_path or (STORE_DIR / "shapes.ttl")
        g = Graph()
        g.bind("sh", SH)
        g.bind("ex", EX)

        for cls in self.seed.get("classes", []):
            class_uri = EX[slugify(cls["label"])]
            shape_uri = EX[slugify(cls["label"] + "Shape")]
            g.add((shape_uri, RDF.type, SH.NodeShape))
            g.add((shape_uri, SH.targetClass, class_uri))

        for rel in self.seed.get("relations", []):
            domain_shape = EX[slugify(rel["domain"] + "Shape")]
            prop_shape = URIRef(str(domain_shape) + "/" + slugify(rel["label"]))
            g.add((domain_shape, SH.property, prop_shape))
            g.add((prop_shape, SH.path, EX[slugify(rel["label"])]))
            g.add((prop_shape, SH["class"], EX[slugify(rel["range"])]))
            g.add((prop_shape, SH.message, Literal(f"{rel['label']} must point to {rel['range']}")))

        g.serialize(destination=str(out_path), format="turtle")
        return out_path


class SHACLValidator:
    def validate(self, data_graph_path: Path, shapes_graph_path: Path) -> tuple[bool, str, Path]:
        data_graph = Graph().parse(str(data_graph_path), format="turtle")
        shapes_graph = Graph().parse(str(shapes_graph_path), format="turtle")
        conforms, _, report_text = validate(data_graph, shacl_graph=shapes_graph, inference="rdfs")
        report_path = STORE_DIR / "shacl_report.txt"
        report_path.write_text(str(report_text), encoding="utf-8")
        return bool(conforms), str(report_text), report_path
