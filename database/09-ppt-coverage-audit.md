# PPT 33장 정리 완성도 점검표

[← Database 목차로 돌아가기](README.md)

## 점검 범위

- 원본 PDF: 461쪽
- 강의 구성: 33개 장
- Database 문서: 28개
- 전체 분량: 약 8,596줄
- 종합 실습 1~4의 문제별 정답·제출 결과: 사용자 요청에 따라 제외

## 판정 기준

- **개념 상세**: PPT 핵심 개념, 비전공자 설명, 예제, DBMS 차이를 학습할 본문이 있음
- **정리 제외**: 종합 실습의 문제별 정답·제출 결과
- **실행 검증 필요**: 개념과 예제는 있지만 세 DBMS에서 실제 실행 결과를 자동 검증한 것은 아님

## 전체 결과

```text
PPT 33개 장의 위치와 주요 주제
→ 모두 순차 가이드에 포함

개념 장
→ 29개 장 모두 상세 본문 연결

종합 실습 장
→ 4개 장의 위치·목표는 포함
→ 문제별 정답은 정리 범위에서 제외

MySQL·PostgreSQL·Oracle 비교
→ Schema, Type, SQL, Index, Transaction,
  Procedure, Trigger, Security, Backup까지 포함

Production Migration 실행 보장
→ 별도 환경에서 실행·성능·복구 검증 필요
```

## 장별 확인

| 장 | PDF | 주제 | 상태 | 주요 상세 문서 |
| ---: | --- | --- | --- | --- |
| 1 | 7~22 | DB·ACID·WAL·Consensus·Isolation | 개념 상세 | ACID, WAL·Redo·Undo, Consensus, Isolation |
| 2 | 23~36 | 관계형 모델·Key·Relationship·정규화 | 개념 상세 | 관계 구현과 정규화 |
| 3 | 37~45 | ERD·Attribute·IE·DBML | 개념 상세 | ERD, Cardinality, IE, DBML |
| 4 | 46~52 | 개념·논리·물리 모델 | 개념 상세 | 관계형 모델링, Index·Partition 설계 |
| 5 | 53~69 | Schema 전략·RDBMS·ANSI SQL | 개념 상세 | Schema 차이, Silo·Pool·Bridge, ANSI SQL |
| 6 | 70~86 | DDL | 개념 상세 | Cross-DBMS DDL |
| 7 | 87~91 | DML·함수·CASE | 개념 상세 | Cross-DBMS DML |
| 8 | 92~95 | 종합 실습 1 | 정리 제외 | 목표와 복습 경로만 제공 |
| 9 | 97~101 | DBMS 생태계·MSA 연동 | 개념 상세 | Redis·Kafka·Elasticsearch·CDC |
| 10 | 102~109 | 집계·Group | 개념 상세 | Aggregate·ROLLUP·CUBE·FILTER |
| 11 | 110~116 | JOIN Algorithm | 개념 상세 | NL·Hash·Merge·BNL·BKA |
| 12 | 117~124 | JOIN 종류 | 개념 상세 | INNER·OUTER·Semi·Anti |
| 13 | 125~129 | Subquery·집합 연산 | 개념 상세 | IN·EXISTS·ANY·ALL·집합 연산 |
| 14 | 130~135 | CTE·View·Materialized View | 개념 상세 | Recursive CTE·DBMS별 MV |
| 15 | 136~212 | Window·SQL 실전 패턴 | 개념 상세 | Window Frame·집계·JSON |
| 16 | 213~223 | 종합 실습 2 | 정리 제외 | 목표와 복습 경로만 제공 |
| 17 | 225~240 | Index | 개념 상세 | B-Tree·Hash·GIN·GiST·BRIN |
| 18 | 241~248 | 실행 계획 | 개념 상세 | Scan·Join·Estimate·실행 계획 |
| 19 | 249~267 | SQL Tuning | 개념 상세 | Anti-pattern·통계·Partition Pruning |
| 20 | 268~278 | MVCC·Isolation | 개념 상세 | MVCC·SSI·DBMS별 격리 |
| 21 | 279~290 | Lock·Deadlock | 개념 상세 | Lock 종류·Deadlock·Retry |
| 22 | 291~319 | 고급 설계 | 개념 상세 | BCNF·4NF·5NF·SCD·Sharding |
| 23 | 320~325 | 종합 실습 3 | 정리 제외 | 목표와 복습 경로만 제공 |
| 24 | 327~338 | Procedure·Function | 개념 상세 | 세 DBMS Routine·Volatility |
| 25 | 339~353 | Trigger·Event | 개념 상세 | 세 DBMS Trigger·CDC·Scheduler |
| 26 | 354~363 | Cloud DB | 개념 상세 | RDS·Aurora·Cloud SQL·Azure |
| 27 | 364~368 | Serverless·분산 DB | 개념 상세 | Spanner·Cosmos·Serverless |
| 28 | 369~378 | DW·분석 DB | 개념 상세 | Redshift·BigQuery·Snowflake·ClickHouse |
| 29 | 379~391 | DB Trend | 개념 상세 | NewSQL·TimescaleDB·pgvector |
| 30 | 392~433 | 보안·권한 | 개념 상세 | Role·RLS·Injection·암호화 |
| 31 | 434~440 | Backup·Recovery·HA | 개념 상세 | Logical·Physical·PITR·RPO·RTO |
| 32 | 441~452 | Monitoring·운영 | 개념 상세 | DBMS 지표·Prometheus·Grafana |
| 33 | 453~460 | 종합 실습 4 | 정리 제외 | 목표와 복습 경로만 제공 |

## 비전공자 학습 가능성

### 가능한 부분

- Data와 Database의 차이부터 시작
- DBMS·SQL·Table·Row·Column 설명
- PK·FK·Constraint와 Relationship
- ERD·Cardinality·Optionality·IE 표기
- 정규화와 Transaction
- Index와 실행 계획
- 중·고급 SQL
- DB Programming과 Cloud 운영

### 실행하며 배울 때 추가로 필요한 것

- 실제 MySQL·PostgreSQL·Oracle 설치 또는 container 환경
- Sample schema와 seed data
- DBMS version별 실행 결과 확인
- 오류 발생 시 troubleshooting

판정:

```text
아무 배경지식 없이 개념을 앞에서부터 읽기
→ 가능

문서의 모든 SQL을 세 DBMS에서 그대로 실행
→ 문법 조정과 version 확인 필요
```

## DBMS 전환 범위

현재 포함:

- MySQL·PostgreSQL·Oracle의 schema 계층
- ID·문자열·숫자·Boolean·날짜·NULL
- DDL·DML·Upsert·Pagination
- Aggregate·JOIN·CTE·Window Function
- JSON·Index·Partition
- MVCC·Isolation·WAL·Redo·Undo
- Procedure·Function·Trigger·Scheduler
- User·Role·RLS·암호화
- Backup·PITR·Monitoring
- Inventory·호환성 평가·Data 이동·검증·Cutover·Rollback

실제 전환 전에 추가 검증:

- Version별 syntax
- Collation·Timezone·NULL 결과
- Stored routine 자동 변환 실패
- Data checksum
- 동시성·성능 benchmark
- Backup restore와 failover
- CDC schema change
- Cutover 후 rollback 가능성

판정:

```text
다른 DBMS로 옮길 때 무엇이 달라지는지 학습
→ 가능

문서만으로 Production Migration을 무검증 수행
→ 불가능하며 그렇게 사용하면 안 됨
```

## 링크 점검

```text
Header Fragment Link
→ 0개

깨진 File Link
→ 0개

모든 상세 Link
→ Markdown File 직접 열기 방식
```

