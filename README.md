# PFM Ontology MVP

PFM(Phase-Field Modeling) 관련 논문이나 PDF를 입력으로 받아, 텍스트를 파싱하고 개념/관계 후보를 추출한 뒤 정규화와 검토 단계를 거쳐 온톨로지 형태로 누적 저장하는 최소 동작형 파이프라인입니다.

현재 목표는 다음과 같습니다.

- PFM 문헌에서 핵심 개념과 관계를 자동 추출
- 같은 개념의 다른 표현을 정규화하여 중복 축소
- 자동 승인 가능한 결과와 검토가 필요한 결과를 분리 저장
- 승인된 결과를 RDF/Turtle로 내보내고 기본 검증까지 수행

## Pipeline

`PDF -> Text Parse -> Chunking -> Candidate Extraction -> Normalization -> Proposal Queue -> Accepted Ontology -> RDF Export -> SHACL Validation`

## What this project does

1. `data/raw_papers/`에 있는 PDF를 읽습니다.
2. PDF 텍스트를 추출하여 문서별 JSON으로 저장합니다.
3. 텍스트를 청크 단위로 분할합니다.
4. 각 청크에서 개념(node)과 관계(edge) 후보를 추출합니다.
5. alias, fuzzy matching, semantic matching을 이용해 표기를 정규화합니다.
6. 신뢰도가 높고 스키마와 잘 맞는 결과는 자동 승인합니다.
7. 애매한 결과는 proposal queue에 저장해 후속 검토 대상으로 남깁니다.
8. 승인된 결과를 RDF/Turtle로 내보내고 SHACL 기반 검증 결과를 생성합니다.

## Project structure

```text
pfm_ontology_mvp/
├─ data/
│  ├─ raw_papers/      # 입력 PDF
│  ├─ parsed/          # PDF 파싱 결과
│  ├─ chunks/          # 청크 분할 결과
│  ├─ candidates/      # 추출된 후보
│  ├─ normalized/      # 정규화 결과
│  ├─ proposals/       # 검토 대기 노드/관계
│  └─ store/           # 승인된 ontology 저장소 및 RDF 출력
├─ ontology/
│  ├─ seed_schema.yaml # 초기 클래스/관계 정의
│  └─ aliases.yaml     # alias -> canonical 매핑
├─ src/pfm_ontology_mvp/
│  ├─ pdf_parser.py
│  ├─ chunker.py
│  ├─ normalize.py
│  ├─ ontology_store.py
│  ├─ rdf_export.py
│  ├─ shacl_utils.py
│  ├─ pipeline.py
│  ├─ cli.py
│  └─ extractors/
│     ├─ rule_based.py
│     └─ llm_openai.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Extractor modes

이 프로젝트는 세 가지 실행 모드를 지원합니다.

- `rule` : 규칙 기반 추출기만 사용
- `llm` : OpenAI 호환 endpoint 기반 추출기 사용
- `auto` : API 설정이 있으면 LLM, 없으면 rule 기반으로 동작

기본값은 `auto`입니다.

## Quick start

### 1. 프로젝트 클론 또는 다운로드

```bash
git clone https://github.com/your-username/pfm-ontology-mvp.git
cd pfm-ontology-mvp
```

압축 파일로 받았다면:

```bash
unzip pfm_ontology_mvp.zip
cd pfm_ontology_mvp
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r rements.txt
cp .env.example .env
```

### 3. PDF 넣기

PFM 논문이나 PDF를 `data/raw_papers/` 폴더에 넣습니다.

예시:

```bash
cp ~/Downloads/sample_pfm_paper.pdf data/raw_papers/
```

### 4. 실행

```bash
PYTHONPATH=src python -m pfm_ontology_mvp.cli run
```

### 5. 결과 확인

실행이 끝나면 아래 파일들을 확인하면 됩니다.

- `data/proposals/proposed_nodes.jsonl`
- `data/proposals/proposed_edges.jsonl`
- `data/store/nodes.jsonl`
- `data/store/edges.jsonl`
- `data/store/ontology.ttl`
- `data/store/shacl_report.txt`

## Configuration

`.env` 파일에서 아래 항목을 설정할 수 있습니다.

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
EXTRACTOR=auto
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
AUTO_ACCEPT_CONFIDENCE=0.82
FUZZY_MATCH_THRESHOLD=90
SEMANTIC_MATCH_THRESHOLD=0.86
MAX_CHUNKS_PER_DOC=
```

### OpenAI-compatible endpoint example

DGX, vLLM, Ollama, OpenRouter 등 OpenAI 호환 형식으로 열려 있는 endpoint를 사용할 수 있습니다.

예시:

```env
OPENAI_API_KEY=dummy
OPENAI_BASE_URL=http://your-server-address:8000/v1
OPENAI_MODEL=llama-7b-instruct
EXTRACTOR=llm
```

## Output files

실행 후 주요 결과물은 아래 위치에 저장됩니다.

- `data/parsed/*.json` : PDF 파싱 결과
- `data/chunks/*.json` : 청크 분할 결과
- `data/candidates/*.json` : 추출 후보
- `data/normalized/*.json` : 정규화 결과
- `data/proposals/proposed_nodes.jsonl` : 검토 대기 노드
- `data/proposals/proposed_edges.jsonl` : 검토 대기 관계
- `data/store/nodes.jsonl` : 승인된 노드 저장소
- `data/store/edges.jsonl` : 승인된 관계 저장소
- `data/store/ontology.ttl` : RDF/Turtle 출력
- `data/store/shacl_report.txt` : SHACL 검증 결과

## Seed schema

현재 MVP는 아래 핵심 클래스와 관계를 중심으로 시작합니다.

### Classes

- Paper
- SimulationType
- MaterialSystem
- GoverningEquation
- PhaseFieldVariable
- FreeEnergyTerm
- Parameter
- BoundaryCondition
- InitialCondition
- NumericalMethod
- PhysicalPhenomenon
- OutputMetric

### Relations

- describes
- appliedToMaterial
- usesEquation
- hasVariable
- hasFreeEnergyTerm
- hasParameter
- hasBoundaryCondition
- hasInitialCondition
- usesNumericalMethod
- modelsPhenomenon
- predictsOutput

## Current workflow

현재 단계에서는 아래 순서로 사용하는 것을 권장합니다.

1. 소수의 PDF로 먼저 실행
2. `proposals`와 `store` 결과 확인
3. `ontology/aliases.yaml` 보강
4. 규칙 기반 패턴 또는 LLM 프롬프트 보강
5. 문서 수를 점진적으로 확대

즉, 이 프로젝트는 완전 자동 반영 시스템이라기보다, 자동 추출과 정규화를 기반으로 온톨로지 초안을 누적하고 검토 가능한 형태로 관리하는 MVP입니다.

## Dependencies

- PyMuPDF
- pydantic
- PyYAML
- rapidfuzz
- sentence-transformers
- rdflib
- pyshacl
- requests
- python-dotenv
- numpy

## Future work

- 수식/표 중심 파싱 강화
- section-aware chunking
- relation별 confidence calibration
- curator UI 추가
- graph database 연동
- domain-specific encoder 또는 reranker 추가

## Notes

- 실제 운영 환경에서는 `.env`와 민감한 인증 정보는 저장소에 올리지 않는 것을 권장합니다.
- `data/raw_papers/`에는 저작권 또는 배포 정책을 고려하여 샘플 문서만 포함하는 것이 좋습니다.
- 초기 ontology 품질은 alias 사전과 추출기 품질에 크게 영향을 받습니다.
