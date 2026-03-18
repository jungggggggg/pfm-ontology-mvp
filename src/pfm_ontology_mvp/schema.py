from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    paper_id: str
    source_file: str
    title: Optional[str] = None
    text: str


class Chunk(BaseModel):
    paper_id: str
    chunk_id: str
    text: str
    source_pages: List[int] = Field(default_factory=list)


class NodeCandidate(BaseModel):
    label: str
    type: str
    evidence: str
    source_chunk_id: str
    paper_id: str
    confidence: float = 0.5
    canonical_label: Optional[str] = None
    matched_existing: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class EdgeCandidate(BaseModel):
    source: str
    relation: str
    target: str
    evidence: str
    source_chunk_id: str
    paper_id: str
    confidence: float = 0.5
    canonical_source: Optional[str] = None
    canonical_target: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class CandidateBundle(BaseModel):
    paper_id: str
    nodes: List[NodeCandidate] = Field(default_factory=list)
    edges: List[EdgeCandidate] = Field(default_factory=list)


class StoreNode(BaseModel):
    label: str
    type: str
    source_paper: str
    evidence: str
    aliases: List[str] = Field(default_factory=list)
    status: str = "accepted"


class StoreEdge(BaseModel):
    source: str
    relation: str
    target: str
    source_paper: str
    evidence: str
    status: str = "accepted"


class SchemaClass(BaseModel):
    label: str
    description: str


class SchemaRelation(BaseModel):
    label: str
    domain: str
    range: str


class SeedSchema(BaseModel):
    classes: List[SchemaClass]
    relations: List[SchemaRelation]
