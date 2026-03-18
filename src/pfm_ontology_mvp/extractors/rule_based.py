from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from .base import BaseExtractor
from ..schema import Chunk, CandidateBundle, NodeCandidate, EdgeCandidate
from ..utils import split_sentences


class RuleBasedExtractor(BaseExtractor):
    TERM_PATTERNS: Dict[str, Tuple[str, List[str]]] = {
        "PFM": ("SimulationType", ["phase-field model", "phase field model", "phase-field method", "phase field method", "pfm"]),
        "Multi-Phase-Field Model": ("SimulationType", ["multi-phase-field model", "multiphase-field model", "multi phase field"]),
        "Allen-Cahn": ("GoverningEquation", ["allen-cahn", "allen cahn"]),
        "Cahn-Hilliard": ("GoverningEquation", ["cahn-hilliard", "cahn hilliard"]),
        "Order Parameter": ("PhaseFieldVariable", ["order parameter"]),
        "Phase Fraction": ("PhaseFieldVariable", ["phase fraction"]),
        "Free Energy": ("FreeEnergyTerm", ["free energy"]),
        "Bulk Free Energy": ("FreeEnergyTerm", ["bulk free energy"]),
        "Gradient Energy": ("FreeEnergyTerm", ["gradient energy"]),
        "Chemical Free Energy": ("FreeEnergyTerm", ["chemical free energy"]),
        "Mobility": ("Parameter", ["mobility coefficient", "mobility"]),
        "Diffusion Coefficient": ("Parameter", ["diffusion coefficient"]),
        "Interface Width": ("Parameter", ["interface width"]),
        "Interfacial Energy": ("Parameter", ["interfacial energy", "interface energy"]),
        "Anisotropy Coefficient": ("Parameter", ["anisotropy coefficient", "anisotropy"]),
        "Boundary Condition": ("BoundaryCondition", ["boundary condition", "dirichlet", "neumann", "periodic boundary"]),
        "Initial Condition": ("InitialCondition", ["initial condition", "initialized with", "initially"]),
        "Finite Difference Method": ("NumericalMethod", ["finite difference method", "fdm"]),
        "Finite Element Method": ("NumericalMethod", ["finite element method", "fem"]),
        "Spectral Method": ("NumericalMethod", ["spectral method", "fourier spectral"]),
        "Dendritic Growth": ("PhysicalPhenomenon", ["dendritic growth", "dendrite"]),
        "Grain Growth": ("PhysicalPhenomenon", ["grain growth"]),
        "Spinodal Decomposition": ("PhysicalPhenomenon", ["spinodal decomposition"]),
        "Coarsening": ("PhysicalPhenomenon", ["coarsening"]),
        "Solidification": ("PhysicalPhenomenon", ["solidification"]),
        "Grain Size": ("OutputMetric", ["grain size"]),
        "Interface Velocity": ("OutputMetric", ["interface velocity"]),
        "Al-Cu": ("MaterialSystem", ["al-cu", "al cu", "aluminum-copper"]),
        "Ni-based Superalloy": ("MaterialSystem", ["ni-based superalloy", "nickel-based superalloy"]),
        "Fe-C": ("MaterialSystem", ["fe-c", "fe c", "iron-carbon"]),
    }

    def extract(self, chunk: Chunk) -> CandidateBundle:
        bundle = CandidateBundle(paper_id=chunk.paper_id)
        sentences = split_sentences(chunk.text)
        found_terms: Dict[str, NodeCandidate] = {}

        for sentence in sentences:
            lower = sentence.lower()
            for canonical, (node_type, patterns) in self.TERM_PATTERNS.items():
                if any(p in lower for p in patterns):
                    if canonical not in found_terms:
                        found_terms[canonical] = NodeCandidate(
                            label=canonical,
                            type=node_type,
                            evidence=sentence,
                            source_chunk_id=chunk.chunk_id,
                            paper_id=chunk.paper_id,
                            confidence=0.78,
                        )

        bundle.nodes = list(found_terms.values())

        present_by_type: Dict[str, List[str]] = defaultdict(list)
        for node in bundle.nodes:
            present_by_type[node.type].append(node.label)

        def add_edge(source: str, relation: str, target: str, evidence: str, confidence: float = 0.80) -> None:
            if source == target:
                return
            bundle.edges.append(
                EdgeCandidate(
                    source=source,
                    relation=relation,
                    target=target,
                    evidence=evidence,
                    source_chunk_id=chunk.chunk_id,
                    paper_id=chunk.paper_id,
                    confidence=confidence,
                )
            )

        joined_text = " ".join(sentences).lower()

        simulation_candidates = present_by_type.get("SimulationType", [])
        equation_candidates = present_by_type.get("GoverningEquation", [])
        variable_candidates = present_by_type.get("PhaseFieldVariable", [])
        energy_candidates = present_by_type.get("FreeEnergyTerm", [])
        parameter_candidates = present_by_type.get("Parameter", [])
        bc_candidates = present_by_type.get("BoundaryCondition", [])
        ic_candidates = present_by_type.get("InitialCondition", [])
        method_candidates = present_by_type.get("NumericalMethod", [])
        phenomenon_candidates = present_by_type.get("PhysicalPhenomenon", [])
        output_candidates = present_by_type.get("OutputMetric", [])
        material_candidates = present_by_type.get("MaterialSystem", [])

        for sim in simulation_candidates:
            for eq in equation_candidates:
                add_edge(sim, "usesEquation", eq, f"{sim} appears with {eq} in the same chunk.")
            for mat in material_candidates:
                add_edge(sim, "appliedToMaterial", mat, f"{sim} appears with {mat} in the same chunk.")
            for bc in bc_candidates:
                add_edge(sim, "hasBoundaryCondition", bc, f"{sim} appears with {bc} in the same chunk.")
            for ic in ic_candidates:
                add_edge(sim, "hasInitialCondition", ic, f"{sim} appears with {ic} in the same chunk.")
            for method in method_candidates:
                add_edge(sim, "usesNumericalMethod", method, f"{sim} appears with {method} in the same chunk.")
            for phenomenon in phenomenon_candidates:
                add_edge(sim, "modelsPhenomenon", phenomenon, f"{sim} appears with {phenomenon} in the same chunk.")
            for output in output_candidates:
                add_edge(sim, "predictsOutput", output, f"{sim} appears with {output} in the same chunk.")

        for eq in equation_candidates:
            for var in variable_candidates:
                add_edge(eq, "hasVariable", var, f"{eq} appears with {var} in the same chunk.")
            for energy in energy_candidates:
                add_edge(eq, "hasFreeEnergyTerm", energy, f"{eq} appears with {energy} in the same chunk.")
            for param in parameter_candidates:
                add_edge(eq, "hasParameter", param, f"{eq} appears with {param} in the same chunk.")

        if simulation_candidates:
            for keyword, phenomenon in [
                ("solidification", "Solidification"),
                ("dendritic", "Dendritic Growth"),
                ("grain growth", "Grain Growth"),
                ("coarsening", "Coarsening"),
            ]:
                if keyword in joined_text and phenomenon in found_terms:
                    for sim in simulation_candidates:
                        add_edge(sim, "modelsPhenomenon", phenomenon, f"Keyword '{keyword}' found in chunk.", 0.86)

        # Dedupe edges
        unique = {}
        for edge in bundle.edges:
            key = (edge.source, edge.relation, edge.target)
            if key not in unique or edge.confidence > unique[key].confidence:
                unique[key] = edge
        bundle.edges = list(unique.values())
        return bundle
