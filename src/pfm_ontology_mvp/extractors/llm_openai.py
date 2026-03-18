from __future__ import annotations

import json
import requests

from .base import BaseExtractor
from ..schema import Chunk, CandidateBundle
from ..settings import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


class OpenAICompatibleExtractor(BaseExtractor):
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

    def extract(self, chunk: Chunk) -> CandidateBundle:
        prompt = self._make_prompt(chunk)
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract ontology candidates from phase-field modeling documents. Return JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["paper_id"] = chunk.paper_id
        for node in parsed.get("nodes", []):
            node.setdefault("source_chunk_id", chunk.chunk_id)
            node.setdefault("paper_id", chunk.paper_id)
            node.setdefault("confidence", 0.75)
        for edge in parsed.get("edges", []):
            edge.setdefault("source_chunk_id", chunk.chunk_id)
            edge.setdefault("paper_id", chunk.paper_id)
            edge.setdefault("confidence", 0.75)
        return CandidateBundle.model_validate(parsed)

    @staticmethod
    def _make_prompt(chunk: Chunk) -> str:
        return f"""
Extract ontology candidates from this phase-field modeling chunk.

Allowed node types:
Paper, SimulationType, MaterialSystem, GoverningEquation, PhaseFieldVariable,
FreeEnergyTerm, Parameter, BoundaryCondition, InitialCondition,
NumericalMethod, PhysicalPhenomenon, OutputMetric

Allowed relations:
describes, appliedToMaterial, usesEquation, hasVariable, hasFreeEnergyTerm,
hasParameter, hasBoundaryCondition, hasInitialCondition, usesNumericalMethod,
modelsPhenomenon, predictsOutput

Rules:
1. Extract only concepts explicitly supported by the text.
2. Do not invent node types or relations.
3. Every node and edge must include an evidence sentence copied or tightly quoted from the text.
4. Use concise canonical labels when possible.
5. Return JSON object with keys: paper_id, nodes, edges.
6. nodes items must have: label, type, evidence, confidence.
7. edges items must have: source, relation, target, evidence, confidence.

Chunk ID: {chunk.chunk_id}
Text:
{chunk.text}
""".strip()
