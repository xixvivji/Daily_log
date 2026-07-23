# 07. 녹음 구간 정리

## 전사 정보

- 길이: 약 9분 31초
- 언어: 한국어
- 방식: Whisper로 초벌 전사 후 데이터베이스 문맥에 맞게 교정
- 범위: 데이터베이스와 직접 관련된 약 0:00~8:16

녹음 품질과 전문 용어 때문에 초벌 전사에는 `TTL → TTR`, `Redis → 레디스`, `EXPLAIN ANALYZE → 익스프레인 에널라이저` 같은 오인식이 있었다. 아래 내용은 문맥상 명확한 부분만 요약했으며, 불명확한 문장을 임의로 확정하지 않았다.

## 00:00~01:00 Redis TTL 튜닝

강사가 말한 `TTR`은 문맥상 **TTL(Time To Live)**이다.

핵심 내용:

- Redis cache의 TTL은 짧거나 긴 것 자체가 정답이 아니다.
- 최신성이 중요하면 TTL을 짧게 하고, 변경이 드문 조회 data면 더 길게 둘 수 있다.
- TTL이 길수록 key가 memory에 오래 남아 memory pressure가 커질 수 있다.
- 실제 환경과 유사한 staging에서 memory와 hit/miss를 보며 조정하고, 운영 후 다시 점검한다.

### 더 정확한 튜닝 기준

TTL 하나만 조정해서는 부족하다.

```text
업무상 허용 가능한 stale 시간
cache hit ratio와 miss 비용
key 개수와 value 크기
eviction 정책과 memory 사용량
동시 만료로 인한 cache stampede
원본 DB의 read 부하
```

TTL을 무작위로 조금씩 흔드는 **jitter**를 주면 많은 key가 동시에 만료되는 현상을 줄일 수 있다. 자주 조회되는 key의 만료 순간에는 lock, request coalescing, stale-while-revalidate 같은 방법도 검토한다.

## 01:00~02:16 Vector DB와 chunking

핵심 내용:

- RAG 품질과 Vector DB 성능에는 chunk를 어디서 자르는지가 중요하다.
- PDF를 기계적으로 page 단위로 자르면 문장이 page 경계에서 끊길 수 있다.
- 문맥이 끊긴 chunk는 검색 결과와 답변 품질을 떨어뜨리고 hallucination 위험을 높일 수 있다.
- embedding과 검색 algorithm, 속도·정확도·memory 사이의 trade-off를 직접 비교해야 한다.
- quantization은 memory와 속도를 줄이는 대신 정확도 손실 가능성이 있다.

### 용어 보강

- **Chunk**: embedding하고 검색할 문서 조각
- **Chunk Size**: 한 조각의 token 또는 문자 크기
- **Overlap**: 인접 chunk에 일부 문맥을 중복
- **Embedding**: text 의미를 고차원 vector로 변환
- **ANN**: 정확한 전수 비교 대신 가까운 vector를 빠르게 찾는 approximate nearest neighbor
- **HNSW**: graph 기반 ANN index
- **IVF**: vector 공간을 여러 cluster/list로 나눠 일부만 탐색
- **Quantization**: vector 표현 정밀도를 줄여 memory와 계산량 절감
- **Recall@k**: 실제 관련 결과 중 상위 k개 검색 결과에 포함된 비율

페이지 단위보다 heading, paragraph, sentence 경계를 우선하고, 표와 code는 별도 처리하는 편이 낫다. 다만 최적 chunk 크기는 문서 종류와 질문 형태에 따라 달라지므로 평가 dataset으로 측정한다.

## 02:16~03:34 직접 비교하고 기록하기

이 구간에는 ML model 예시도 포함되어 있지만, 데이터베이스 학습에 적용할 메시지는 다음과 같다.

- 도구를 사용했다는 사실보다 어떤 parameter를 왜 바꾸었는지 설명할 수 있어야 한다.
- 변경 전후 수치를 기록해야 실제 tuning 경험이 된다.
- 프로젝트에서 한 선택을 기술 면접에서 재현 가능한 story로 만든다.

DB 실험 기록 예:

```text
문제: 주문 목록 p99 1.8초
관찰: 실제 20행 반환, 48만 행 scan
가설: customer_id + created_at 복합 index 필요
변경: index 추가 및 SELECT column 축소
결과: p99 140ms, 쓰기 p95 4ms 증가
판단: 조회 빈도가 높아 유지, index 크기와 write latency 모니터링
```

## 03:34~05:10 DB와 application의 역할

강사는 SQL, stored procedure 등 DB programming을 잘 활용하면 application code를 줄일 수 있으며, application과 DB 사이의 균형이 중요하다고 설명한다.

### 이 내용을 실무적으로 해석하기

DB가 잘하는 일:

- set-based filtering, JOIN, aggregate
- PK, FK, UNIQUE, CHECK를 통한 무결성
- transaction과 concurrency control
- data 가까이에서 처리해 network 왕복 감소

application이 맡기 좋은 일:

- 외부 API와 service orchestration
- 자주 변경되는 business flow
- version control, test, deployment가 중요한 domain logic
- DB 제품에 종속되면 곤란한 logic

stored procedure는 여러 statement를 DB 가까이에서 원자적으로 처리하거나 legacy·batch 환경에서는 강력하다. 반면 DB vendor lock-in, 배포·test·관찰 난이도, logic 분산을 키울 수 있다. “code line이 줄었다”만으로 좋은 설계라고 판단하지 않고 변경 빈도와 소유권을 본다.

## 05:16~06:15 실행 계획과 index tuning

핵심 내용:

- PostgreSQL query를 실행하고 실행 계획을 직접 찍어 본다.
- `EXPLAIN ANALYZE` 결과에서 full scan 또는 sequential scan 여부를 확인한다.
- index 적용 전후 성능 차이를 측정한다.
- RDBMS index뿐 아니라 Redis TTL처럼 제품별 tuning knob를 직접 바꾸고 결과를 기록한다.

### 교정할 점

Sequential Scan이 보인다고 무조건 index로 바꾸는 것은 아니다. table이 작거나 많은 row를 읽으면 sequential scan이 최적일 수 있다.

`clustered index를 걸어 DB가 다운됐다`는 표현은 실제 원인이 index 생성 중 CPU·I/O·lock 급증인지, disk 부족인지, online DDL 미지원인지 분리해야 한다. index 종류 자체보다 생성 방식, table 크기, maintenance window, resource limit을 기록해야 재현 가능한 경험이 된다.

## 06:16~08:16 DB와 모델을 비교해서 선택하기

핵심 내용:

- 하나의 DB나 모델만 외우지 말고 대안을 비교한다.
- 특징과 장단점을 표로 정리한다.
- “왜 A가 아니라 B를 선택했는가”를 workload와 측정 결과로 설명한다.
- 강의 자료를 그대로 암기하기보다 자신만의 요약과 실험 결과를 만든다.

DB 선택 story의 좋은 구조:

```text
요구사항
→ 후보 MySQL/PostgreSQL 비교
→ 핵심 query와 동시성 benchmark
→ 기능·운영·비용 trade-off
→ 선택
→ 운영 결과와 남은 한계
```

## 녹음에서 얻은 최종 과제

- Redis: TTL, memory, hit ratio, stampede를 바꿔가며 측정
- Vector DB: chunk size, overlap, embedding, HNSW parameter별 품질·latency 비교
- PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)`로 scan과 row 추정 확인
- DBMS: 같은 schema와 핵심 query를 MySQL/PostgreSQL에서 비교
- 기록: 변경값, 측정 환경, 전후 수치, 부작용까지 남기기

