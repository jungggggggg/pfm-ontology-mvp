from __future__ import annotations

import json
from typing import Any, Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .base import BaseExtractor
from ..schema import Chunk, CandidateBundle
from ..settings import (
    LOCAL_LLM_MODEL_PATH,
    LOCAL_LLM_TORCH_DTYPE,
    LOCAL_LLM_MAX_NEW_TOKENS,
    LOCAL_LLM_TEMPERATURE,
    LOCAL_LLM_TOP_P,
)


class LocalHFExtractor(BaseExtractor):
    def __init__(self) -> None:
        if not LOCAL_LLM_MODEL_PATH:
            raise ValueError("LOCAL_LLM_MODEL_PATH is not set.")

        dtype = self._resolve_dtype(LOCAL_LLM_TORCH_DTYPE)

        self.tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_LLM_MODEL_PATH,
            local_files_only=True,
            use_fast=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            LOCAL_LLM_MODEL_PATH,
            local_files_only=True,
            torch_dtype=dtype,
            device_map="auto",
        )
        self.model.eval()

        if self.tokenizer.pad_token is None and self.tokenizer.eos_token is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def extract(self, chunk: Chunk) -> CandidateBundle:
        prompt = self._make_prompt(chunk)

        messages = [
            {
                "role": "system",
                "content": "You extract ontology candidates from phase-field modeling documents. Return JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        if getattr(self.tokenizer, "chat_template", None):
            rendered = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            rendered = (
                "System: You extract ontology candidates from phase-field modeling documents. Return JSON only.\n\n"
                f"User:\n{prompt}\n\nAssistant:\n"
            )

        inputs = self.tokenizer(rendered, return_tensors="pt")
        input_device = next(self.model.parameters()).device
        inputs = {k: v.to(input_device) for k, v in inputs.items()}

        gen_kwargs = {
            "max_new_tokens": LOCAL_LLM_MAX_NEW_TOKENS,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "do_sample": LOCAL_LLM_TEMPERATURE > 0,
        }
        if LOCAL_LLM_TEMPERATURE > 0:
            gen_kwargs["temperature"] = LOCAL_LLM_TEMPERATURE
            gen_kwargs["top_p"] = LOCAL_LLM_TOP_P

        with torch.inference_mode():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        raw_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        parsed = self._parse_json_output(raw_text)
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
    def _resolve_dtype(dtype_name: str):
        dtype_name = (dtype_name or "").lower()
        if dtype_name == "float16":
            return torch.float16
        if dtype_name == "float32":
            return torch.float32
        if dtype_name == "bfloat16":
            return torch.bfloat16
        return "auto"

    @staticmethod
    def _extract_first_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Model output does not contain a valid JSON object:\n{text}")
        return text[start:end + 1]

    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            candidate = self._extract_first_json_object(text)
            return json.loads(candidate)

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
8. Return JSON only. No markdown. No explanation text.

Chunk ID: {chunk.chunk_id}
Text:
{chunk.text}
""".strip()