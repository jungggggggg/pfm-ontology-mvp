from __future__ import annotations

from .settings import (
    RAW_DIR,
    PARSED_DIR,
    CHUNKS_DIR,
    CANDIDATES_DIR,
    NORMALIZED_DIR,
    EXTRACTOR,
    OPENAI_API_KEY,
    LOCAL_LLM_MODEL_PATH,
    MAX_CHUNKS_PER_DOC,
)
from .pdf_parser import PDFParser
from .chunker import SimpleChunker
from .extractors.rule_based import RuleBasedExtractor
from .extractors.llm_openai import OpenAICompatibleExtractor
from .extractors.llm_local import LocalHFExtractor
from .normalize import Normalizer
from .ontology_store import OntologyStore
from .rdf_export import RDFExporter
from .shacl_utils import SHACLBuilder, SHACLValidator
from .utils import write_json


class Pipeline:
    def __init__(self) -> None:
        self.parser = PDFParser()
        self.chunker = SimpleChunker()
        self.normalizer = Normalizer()
        self.store = OntologyStore()
        self.extractor = self._choose_extractor()

    def _choose_extractor(self):
        if EXTRACTOR == "local_llm":
            return LocalHFExtractor()
        if EXTRACTOR == "llm":
            return OpenAICompatibleExtractor()
        if EXTRACTOR == "rule":
            return RuleBasedExtractor()
        if LOCAL_LLM_MODEL_PATH:
            return LocalHFExtractor()
        if OPENAI_API_KEY:
            return OpenAICompatibleExtractor()
        return RuleBasedExtractor()

    def run(self) -> None:
        pdfs = sorted(RAW_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"No PDF files found in {RAW_DIR}")
            return

        for pdf_path in pdfs:
            print(f"[1/8] Parsing PDF: {pdf_path.name}")
            parsed = self.parser.parse(pdf_path)
            write_json(PARSED_DIR / f"{parsed.paper_id}.json", parsed.model_dump())

            print(f"[2/8] Chunking: {parsed.paper_id}")
            chunks = self.chunker.chunk(parsed)
            if MAX_CHUNKS_PER_DOC:
                chunks = chunks[:MAX_CHUNKS_PER_DOC]
            write_json(CHUNKS_DIR / f"{parsed.paper_id}.json", [c.model_dump() for c in chunks])

            all_nodes = []
            all_edges = []
            print(f"[3/8] Extracting candidates with {self.extractor.__class__.__name__}")
            for chunk in chunks:
                bundle = self.extractor.extract(chunk)
                all_nodes.extend(bundle.nodes)
                all_edges.extend(bundle.edges)

            candidate_bundle = {
                "paper_id": parsed.paper_id,
                "nodes": [n.model_dump() for n in all_nodes],
                "edges": [e.model_dump() for e in all_edges],
            }
            write_json(CANDIDATES_DIR / f"{parsed.paper_id}.json", candidate_bundle)

            print(f"[4/8] Normalizing and matching existing ontology")
            from .schema import CandidateBundle
            bundle_obj = CandidateBundle.model_validate(candidate_bundle)
            normalized = self.normalizer.normalize_bundle(bundle_obj, self.store.existing_nodes())
            write_json(NORMALIZED_DIR / f"{parsed.paper_id}.json", normalized.model_dump())

            print(f"[5/8] Ingesting into accepted ontology / proposals")
            accepted_nodes, accepted_edges, proposed_nodes, proposed_edges = self.store.ingest(normalized)
            print(
                f"Accepted nodes={len(accepted_nodes)}, accepted edges={len(accepted_edges)}, "
                f"proposed nodes={len(proposed_nodes)}, proposed edges={len(proposed_edges)}"
            )

        print("[6/8] Exporting accepted ontology to RDF/Turtle")
        ontology_path = RDFExporter().export()
        print(f"Wrote: {ontology_path}")

        print("[7/8] Building SHACL shapes")
        shapes_path = SHACLBuilder().build_shapes()
        print(f"Wrote: {shapes_path}")

        print("[8/8] Validating ontology")
        conforms, _, report_path = SHACLValidator().validate(ontology_path, shapes_path)
        print(f"SHACL conforms={conforms}, report={report_path}")