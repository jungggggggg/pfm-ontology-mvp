# PFM Ontology MVP

PFM(Phase-Field Modeling) 관련 논문/PDF에서 개념과 관계 후보를 추출하고, 정규화와 검토 단계를 거쳐 온톨로지 형태로 누적 저장하는 MVP입니다.

## Pipeline

`PDF -> Parse -> Chunk -> Extract -> Normalize -> Propose -> Accept -> Export -> Validate`

## Main Features

- PDF 텍스트 파싱
- 개념/관계 후보 추출
- alias 및 유사도 기반 정규화
- proposal queue 저장
- 승인된 ontology 저장
- RDF/Turtle export
- SHACL validation
- rule / local LLM / endpoint 기반 추출 지원

## Project Structure

```text
pfm_ontology_mvp/
├─ data/
│  ├─ raw_papers/     # input PDFs
│  ├─ parsed/         # parsed text
│  ├─ chunks/         # chunked text
│  ├─ candidates/     # extracted candidates
│  ├─ normalized/     # normalized results
│  ├─ proposals/      # review queue
│  └─ store/          # accepted ontology + exports
├─ ontology/
│  ├─ seed_schema.yaml
│  └─ aliases.yaml
├─ src/pfm_ontology_mvp/
│  ├─ cli.py
│  ├─ pipeline.py
│  ├─ pdf_parser.py
│  ├─ chunker.py
│  ├─ normalize.py
│  ├─ ontology_store.py
│  ├─ rdf_export.py
│  ├─ shacl_utils.py
│  └─ extractors/
│     ├─ rule_based.py
│     ├─ llm_openai.py
│     └─ llm_local.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Quick Start

### 1. Clone or download

```bash
git clone https://github.com/your-username/pfm-ontology-mvp.git
cd pfm-ontology-mvp
```

압축 파일로 받았다면:

```bash
unzip pfm_ontology_mvp.zip
cd pfm_ontology_mvp
```

### 2. Create venv and install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Put PDFs into input folder

```bash
cp /path/to/your/paper.pdf data/raw_papers/
```

### 4. Run pipeline

```bash
PYTHONPATH=src python -m pfm_ontology_mvp.cli run
```

### 5. Check outputs

주요 결과 파일:

- `data/proposals/proposed_nodes.jsonl`
- `data/proposals/proposed_edges.jsonl`
- `data/store/nodes.jsonl`
- `data/store/edges.jsonl`
- `data/store/ontology.ttl`
- `data/store/shacl_report.txt`

## Extractor Modes

- `rule` : rule-based extractor
- `llm` : OpenAI-compatible endpoint
- `local_llm` : local Hugging Face model
- `auto` : automatically choose available option

## Configuration

`.env` 예시:

```env
EXTRACTOR=local_llm

# Local LLM
LOCAL_LLM_MODEL_PATH=/absolute/path/to/Meta-Llama-3.1-8B-Instruct
LOCAL_LLM_TORCH_DTYPE=bfloat16
LOCAL_LLM_MAX_NEW_TOKENS=900
LOCAL_LLM_TEMPERATURE=0.1
LOCAL_LLM_TOP_P=0.9

# Optional OpenAI-compatible endpoint
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini

# Embedding / matching
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
AUTO_ACCEPT_CONFIDENCE=0.82
FUZZY_MATCH_THRESHOLD=90
SEMANTIC_MATCH_THRESHOLD=0.86
MAX_CHUNKS_PER_DOC=
```

로컬 LLM을 쓰는 경우에는 `LOCAL_LLM_MODEL_PATH`만 실제 경로로 맞추시면 됩니다.

## Example Run

```bash
source .venv/bin/activate
cp /path/to/pfm_paper.pdf data/raw_papers/
PYTHONPATH=src python -m pfm_ontology_mvp.cli run
```

## Output Overview

- `parsed/` : PDF 텍스트 추출 결과
- `chunks/` : 청크 분할 결과
- `candidates/` : 추출 후보
- `normalized/` : 정규화 결과
- `proposals/` : 검토 대기 항목
- `store/` : 승인된 ontology 및 export 결과

## Notes

- 이 프로젝트는 완전 자동 반영 시스템이 아니라, 자동 추출 결과를 누적하고 검토 가능한 형태로 관리하는 MVP입니다.
- 초기 품질은 alias 사전, 추출기 성능, 문서 품질에 크게 영향을 받습니다.
- `.env`나 민감한 인증 정보는 저장소에 올리지 않는 것을 권장합니다.
