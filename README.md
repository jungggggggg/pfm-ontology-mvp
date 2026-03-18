# PFM Ontology MVP

이 프로젝트는 **PFM 관련 PDF/논문을 넣으면** 텍스트를 파싱하고, 온톨로지 후보 노드/관계를 추출하고, alias 정규화와 중복 병합을 수행한 뒤, 자동 승인 가능한 항목은 ontology store에 반영하고 나머지는 proposal queue로 보내는 최소 동작형 파이프라인입니다.

핵심 흐름은 아래와 같습니다.

`PDF -> Text Parse -> Chunk -> Candidate Extraction -> Normalization -> Proposal Queue -> Accepted Ontology -> RDF/Turtle Export -> SHACL Validation`

## 왜 이 구조로 만들었는가

업로드해주신 Hi-BERT 논문은 생성형 AI로 트리플을 자동 생성하고, 그 트리플을 자연어 문장으로 바꿔 다른 도메인과의 의미적 연결을 학습하는 방식을 보여줍니다. 특히 자동 생성 트리플을 자연어 문장으로 변환해 학습에 쓰고, 서로 다른 도메인을 잇는 보조 표현으로 활용했다는 점이 중요합니다. 이 MVP는 그 아이디어를 **온톨로지 구축/업데이트 파이프라인** 쪽으로 가져와서, 먼저 구조화 추출과 검증 가능한 저장을 만들고, 나중에 contrastive encoder나 Hi-BERT류 보조 인코더를 붙일 수 있게 설계했습니다.

## 지금 이 프로젝트가 하는 일

1. `data/raw_papers/`에 PDF를 넣습니다.
2. PyMuPDF로 PDF 텍스트를 페이지 단위로 추출합니다.
3. 문단/문장 기준으로 chunk를 만듭니다.
4. 추출기는 두 가지 중 하나를 씁니다.
   - `rule`: 규칙 기반 추출기
   - `llm`: OpenAI 호환 API 기반 구조화 추출기
   - `auto`: API 키가 있으면 LLM, 없으면 rule
5. alias / fuzzy / embedding 유사도로 같은 개념을 정규화합니다.
6. confidence와 스키마 검사를 통과하면 accepted ontology에 반영합니다.
7. 애매하거나 신규성이 큰 것은 proposals로 보냅니다.
8. accepted ontology를 RDF/Turtle로 내보내고 SHACL로 검증합니다.

## macOS에서 바로 시작하는 방법

### 1) 프로젝트 준비

```bash
cd pfm_ontology_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2) PDF 넣기

PFM 논문 PDF를 `data/raw_papers/` 폴더에 넣으십시오.

예:

```bash
cp ~/Downloads/your_pfm_paper.pdf data/raw_papers/
```

### 3) 바로 실행

```bash
PYTHONPATH=src python -m pfm_ontology_mvp.cli run
```

실행이 끝나면 아래 파일들이 생깁니다.

- `data/parsed/*.json` : PDF 파싱 결과
- `data/chunks/*.json` : 청크 결과
- `data/candidates/*.json` : 추출된 후보
- `data/normalized/*.json` : 정규화 결과
- `data/proposals/proposed_nodes.jsonl`
- `data/proposals/proposed_edges.jsonl`
- `data/store/nodes.jsonl`
- `data/store/edges.jsonl`
- `data/store/ontology.ttl`
- `data/store/shacl_report.txt`

## LLM 추출을 붙이는 방법

### OpenAI / OpenAI-compatible endpoint

`.env`에 아래를 채우십시오.

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
EXTRACTOR=llm
```

### Ollama 같은 로컬 OpenAI 호환 서버

예를 들어 로컬에서 OpenAI 호환 엔드포인트를 띄워두었다면 이렇게 바꿀 수 있습니다.

```env
OPENAI_API_KEY=dummy
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=qwen2.5:7b-instruct
EXTRACTOR=llm
```

## Hugging Face / Sentence Transformers를 어디에 쓰는가

이 프로젝트는 `sentence-transformers`를 사용해 **정규화 단계**에서 semantic matching을 합니다. 즉, `phase-field model`, `PFM`, `phase field formulation`처럼 문자열이 완전히 같지 않아도 의미상 비슷하면 기존 개념 후보와 매칭시키는 데 씁니다.

## 현재 제공되는 seed schema

현재는 아래 클래스와 관계로 시작합니다.

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

## 이 프로젝트의 현실적인 사용법

이 MVP는 **완전 자동 반영 시스템**이 아니라 **자동 제안 + 부분 자동 승인 + RDF 저장 + 검증** 시스템입니다. 지금 단계에서는 이 방식이 맞습니다. 이유는 PFM 문헌에서 같은 개념이 다른 수식, 약어, 문맥으로 등장하고, 논문별로 정의 범위가 달라지기 때문에, 완전 자동 반영은 초기에 ontology를 오염시킬 가능성이 높기 때문입니다.

즉, 지금은 아래 순서로 쓰시면 됩니다.

1. 논문 1~3편으로 시작
2. accepted / proposals 결과 확인
3. aliases.yaml 보강
4. rule_based extractor 패턴 보강
5. LLM extractor 연결
6. 문서 수를 늘림
7. 나중에 Hi-BERT류 contrastive encoder나 re-ranker를 추가

## 추천 하드웨어

### 가장 가벼운 시작
- Apple Silicon Mac(M1/M2/M3) 또는 Intel Mac
- RAM 16GB 이상
- SSD 여유 20GB 이상
- LLM 추출은 API 사용

### 로컬 추출까지 해보고 싶을 때
- Apple Silicon 16GB~32GB RAM 권장
- 로컬 모델을 돌릴 경우 7B급 instruct 모델은 가능하지만 속도는 느릴 수 있음
- embedding 모델은 비교적 가볍게 동작

## 다음 확장 포인트

- 표/수식 기반 파싱 강화
- section-aware chunking
- 관계별 confidence calibration
- curator UI
- Neo4j/graph DB 연동
- Hi-BERT 스타일 ontology sentence encoder 추가

