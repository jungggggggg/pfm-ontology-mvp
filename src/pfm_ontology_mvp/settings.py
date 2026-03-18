from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw_papers"
PARSED_DIR = DATA_DIR / "parsed"
CHUNKS_DIR = DATA_DIR / "chunks"
CANDIDATES_DIR = DATA_DIR / "candidates"
NORMALIZED_DIR = DATA_DIR / "normalized"
STORE_DIR = DATA_DIR / "store"
PROPOSALS_DIR = DATA_DIR / "proposals"
ONTOLOGY_DIR = ROOT / "ontology"

for path in [RAW_DIR, PARSED_DIR, CHUNKS_DIR, CANDIDATES_DIR, NORMALIZED_DIR, STORE_DIR, PROPOSALS_DIR, ONTOLOGY_DIR]:
    path.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

EXTRACTOR = os.getenv("EXTRACTOR", "auto").strip().lower()

# Local LLM
LOCAL_LLM_MODEL_PATH = os.getenv("LOCAL_LLM_MODEL_PATH", "").strip()
LOCAL_LLM_TORCH_DTYPE = os.getenv("LOCAL_LLM_TORCH_DTYPE", "bfloat16").strip().lower()
LOCAL_LLM_MAX_NEW_TOKENS = int(os.getenv("LOCAL_LLM_MAX_NEW_TOKENS", "900"))
LOCAL_LLM_TEMPERATURE = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.1"))
LOCAL_LLM_TOP_P = float(os.getenv("LOCAL_LLM_TOP_P", "0.9"))

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
AUTO_ACCEPT_CONFIDENCE = float(os.getenv("AUTO_ACCEPT_CONFIDENCE", "0.82"))
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", "90"))
SEMANTIC_MATCH_THRESHOLD = float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.86"))
MAX_CHUNKS_PER_DOC = os.getenv("MAX_CHUNKS_PER_DOC", "").strip()
MAX_CHUNKS_PER_DOC = int(MAX_CHUNKS_PER_DOC) if MAX_CHUNKS_PER_DOC else None