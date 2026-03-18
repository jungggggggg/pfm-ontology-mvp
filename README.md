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
└─ README.md
