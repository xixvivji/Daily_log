# 00. PPT 1~33장 순차 학습 가이드

이 문서는 PDF를 처음부터 순서대로 보면서 정리 내용을 찾기 위한 목차다. 먼저 현재 PDF page를 찾고, 오른쪽의 `정리 문서`를 누르면 해당 설명으로 이동한다.

[← Database 목차로 돌아가기](README.md)

## 먼저 읽기

다음 용어가 아직 낯설다면 PPT로 바로 들어가지 말고 기초 문서를 먼저 읽는다.

```text
Server, Database, Table, Row, Column
Primary Key, Foreign Key
SQL, Query, Transaction
```

- [DB 첫걸음](00-beginner-database-foundation.md)
- [MySQL·PostgreSQL·Oracle 비교 가이드](08-cross-dbms-comparison-guide.md)

PPT 실습이 PostgreSQL이라고 해서 PostgreSQL 문법만 외우지 않는다. 먼저 모든 관계형 DB에 공통인 개념을 이해하고, 각 장에서 MySQL·PostgreSQL·Oracle이 무엇이 다른지 확인한다.

## 문서 구조

```text
PDF를 순서대로 공부
→ 이 문서에서 현재 장 번호 확인
→ 연결된 기본 정리 읽기
→ 필요한 경우 concepts 상세 설명 열기
```

기존 `01~07` 문서는 주제별 심화 노트라 PPT 순서와 완전히 같지 않다. 이 문서가 PPT와 심화 노트 사이의 길잡이다.

## Day 1 - DB 기초, 모델링, 기본 SQL

### 1. 데이터베이스 개요 - PDF 7~22

PPT 흐름:

```text
필요성과 발전 과정
→ ACID
→ DBMS별 ACID 차이
→ WAL
→ Consensus
→ Isolation Level과 Phantom Read
```

정리 문서:

- [DB·DBMS·RDBMS와 ACID 기본](01-database-course-map-and-glossary.md)
- [DBMS별 ACID 지원 차이](concepts/dbms-acid-differences.md)
- [WAL·Undo·Redo·Checkpoint](concepts/wal-undo-redo-checkpoint.md)
- [WAL과 Consensus](concepts/wal-and-consensus.md)
- [Isolation Level별 이상 현상 허용 여부](concepts/isolation-level-anomalies.md)

### 2. 관계형 모델 핵심 개념 - PDF 23~36

PPT 흐름:

```text
Table·Row·Column
→ PK·FK·UK
→ 1:1·1:N·N:M
→ 정규화 필요성
→ 1NF·2NF·3NF
```

정리 문서:

- [Table·Row·Column과 Key](01-database-course-map-and-glossary.md)
- [관계 구현과 정규화](concepts/relationship-and-normalization.md)

### 3. ERD - PDF 37~45

PPT 흐름:

```text
PostgreSQL 실습 환경
→ Entity
→ Attribute
→ Relationship
→ Cardinality·Optionality
→ Crow's Foot
→ DBML
```

정리 문서:

- [ERD 작성 순서](concepts/erd-writing-process.md)
- [Cardinality와 Optionality](concepts/cardinality-and-optionality.md)
- [IE 표기법·Crow's Foot 읽는 방법](concepts/ie-crows-foot-notation.md)
- [DBML로 ERD 작성하기](concepts/dbml-erd-guide.md)

### 4. 개념적·논리적·물리적 모델 - PDF 46~52

PPT 흐름:

```text
개념 모델
→ 논리 모델
→ 물리 모델
→ 타입·Index·Partition
→ Optimistic·Pessimistic Lock
→ Weak Entity와 Junction Table
```

정리 문서:

- [설계의 세 단계](02-relational-modeling-and-sql.md)
- [Optimistic·Pessimistic Lock](04-mvcc-transaction-and-lock.md)
- [Weak Entity와 Junction Table](01-database-course-map-and-glossary.md)

### 5. Schema 전략과 RDBMS 비교 - PDF 53~69

PPT 흐름:

```text
Silo·Pool·Bridge Model
→ MySQL·MariaDB
→ PostgreSQL
→ ANSI SQL
→ Oracle
→ SQL Server
→ 관리형 Cloud DB
```

정리 문서:

- [Schema의 두 가지 의미](01-database-course-map-and-glossary.md)
- [MySQL과 PostgreSQL Schema 차이](concepts/mysql-vs-postgresql-schema.md)
- [DBMS 선택 기준](05-dbms-selection-and-migration.md)
- [MySQL과 PostgreSQL SQL·DDL 차이](05-dbms-selection-and-migration.md)
- [Silo·Pool·Bridge 멀티테넌시와 ANSI SQL](concepts/schema-multitenancy-and-ansi-sql.md)

### 6. SQL 기초 DDL - PDF 70~86

PPT 흐름:

```text
CREATE DATABASE
→ CREATE TABLE
→ ALTER·DROP
→ Data Type
→ PK·FK·UNIQUE·CHECK·NOT NULL
```

정리 문서:

- [DDL·DML·DCL·TCL](02-relational-modeling-and-sql.md)
- [타입 선택](02-relational-modeling-and-sql.md)
- [Key와 Constraint](01-database-course-map-and-glossary.md)
- [DDL·DML을 MySQL·PostgreSQL·Oracle로 비교](concepts/ddl-dml-cross-dbms.md)

### 7. SQL 기초 DML - PDF 87~91

PPT 흐름:

```text
SELECT
→ INSERT
→ UPDATE
→ DELETE
→ 함수와 CASE
```

정리 문서:

- [DDL·DML 구분](02-relational-modeling-and-sql.md)
- [DDL·DML을 MySQL·PostgreSQL·Oracle로 비교](concepts/ddl-dml-cross-dbms.md)

### 8. 종합 실습 1 - PDF 92~95

학사 관리 시스템을 ERD에서 DDL과 기본 조회까지 구현하는 구간이다.

복습 순서:

1. [ERD 작성 순서](concepts/erd-writing-process.md)
2. [관계 구현과 정규화](concepts/relationship-and-normalization.md)
3. [타입 선택](02-relational-modeling-and-sql.md)
4. [Key와 Constraint](01-database-course-map-and-glossary.md)

## Day 2 - DB 생태계와 중·고급 SQL

### 9. Day 1 복습과 DBMS 생태계 - PDF 97~101

PPT 흐름:

```text
DDL·DML 복습
→ DBMS·DW·Data Mining
→ MSA
→ Kafka·Elasticsearch·Redis 연동
```

정리 문서:

- [OLTP·OLAP·HTAP](01-database-course-map-and-glossary.md)
- [Redis·Kafka·Elasticsearch 역할](06-distributed-cloud-and-operations.md)

### 10. SQL 집계와 그룹화 - PDF 102~109

PPT 흐름:

```text
COUNT·SUM·AVG·MIN·MAX
→ GROUP BY
→ HAVING
→ ROLLUP·CUBE
→ FILTER
```

정리 위치:

- [관계형 모델링과 SQL](02-relational-modeling-and-sql.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 11. JOIN 알고리즘 - PDF 110~116

PPT 흐름:

```text
Nested Loop
→ Hash Join
→ Merge Join
→ BNL·BKA
→ DBMS별 차이
```

정리 문서:

- [JOIN 알고리즘](03-index-query-plan-and-tuning.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 12. JOIN 종류 - PDF 117~124

PPT 흐름:

```text
INNER
→ LEFT·RIGHT·FULL OUTER
→ SELF
→ CROSS
→ Semi Join
→ Anti Join
```

정리 문서:

- [JOIN 종류와 결과 집합](02-relational-modeling-and-sql.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 13. Subquery와 집합 연산자 - PDF 125~129

PPT 흐름:

```text
Scalar Subquery
→ Inline View
→ Correlated Subquery
→ EXISTS·IN·ANY·ALL
→ UNION·INTERSECT·EXCEPT
```

정리 문서:

- [Subquery·CTE·View 기본](02-relational-modeling-and-sql.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 14. CTE·View·Materialized View - PDF 130~135

PPT 흐름:

```text
WITH
→ Recursive CTE
→ View
→ Materialized View
→ Refresh 전략
```

정리 문서:

- [CTE·View·Materialized View](02-relational-modeling-and-sql.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 15. Window Function과 SQL 실전 패턴 - PDF 136~212

PPT 흐름:

```text
ROW_NUMBER·RANK·DENSE_RANK
→ NTILE
→ LAG·LEAD
→ 누적합·이동평균
→ STRING_AGG·ARRAY_AGG·JSON_AGG
→ JSONB 등 SQL 실전 패턴
```

정리 문서:

- [Window Function](02-relational-modeling-and-sql.md)
- [PostgreSQL로 옮길 이유와 JSONB](05-dbms-selection-and-migration.md)
- [집계·JOIN·Subquery·CTE·Window Function 상세](concepts/advanced-sql-cross-dbms.md)

### 16. 종합 실습 2 - PDF 213~223

CampusHub 예제로 JOIN, Subquery, Window Function을 함께 연습하는 구간이다.

복습 순서:

1. [JOIN 종류](02-relational-modeling-and-sql.md)
2. [Subquery와 CTE](02-relational-modeling-and-sql.md)
3. [Window Function](02-relational-modeling-and-sql.md)

## Day 3 - 성능, MVCC, Lock, 고급 설계

### 17. Index 설계와 최적화 - PDF 225~240

PPT 흐름:

```text
B-Tree·Hash
→ GIN·GiST·BRIN
→ 복합 Index
→ Covering·Partial·Expression Index
```

정리 문서:

- [B-Tree와 복합 Index](03-index-query-plan-and-tuning.md)
- [Covering·Partial·Expression Index](03-index-query-plan-and-tuning.md)
- [특수 Index·Partition·고급 설계](concepts/advanced-index-partition-design.md)

### 18. 실행 계획 분석 - PDF 241~248

PPT 흐름:

```text
EXPLAIN
→ EXPLAIN ANALYZE
→ Scan
→ 예상 row와 실제 row
→ JOIN·Sort·Loop
```

정리 문서:

- [대표 Scan](03-index-query-plan-and-tuning.md)
- [실행 계획에서 볼 것](03-index-query-plan-and-tuning.md)
- [특수 Index·Partition·고급 설계](concepts/advanced-index-partition-design.md)

### 19. SQL 튜닝과 느린 Query - PDF 249~267

PPT 흐름:

```text
Index 컬럼 함수 적용
→ SELECT *
→ 큰 OFFSET와 기타 Anti-pattern
→ Slow Query
→ pg_stat_statements
→ Partitioning
```

정리 문서:

- [흔한 SQL Anti-pattern](03-index-query-plan-and-tuning.md)
- [느린 Query 찾기](03-index-query-plan-and-tuning.md)
- [튜닝 순서](03-index-query-plan-and-tuning.md)
- [특수 Index·Partition·고급 설계](concepts/advanced-index-partition-design.md)

### 20. MVCC와 Isolation Level - PDF 268~278

PPT 흐름:

```text
MVCC
→ Snapshot
→ Isolation Level
→ PostgreSQL·MySQL 차이
→ 동시성 이상 현상
```

정리 문서:

- [MVCC](04-mvcc-transaction-and-lock.md)
- [Isolation Level 개요](04-mvcc-transaction-and-lock.md)
- [Isolation Level별 이상 현상 상세](concepts/isolation-level-anomalies.md)

### 21. Lock과 Deadlock - PDF 279~290

PPT 흐름:

```text
Row·Table Lock
→ Gap·Next-key Lock
→ Advisory Lock
→ Deadlock 발생
→ 감지·해소·Monitoring
```

정리 문서:

- [Lock 종류](04-mvcc-transaction-and-lock.md)
- [Deadlock](04-mvcc-transaction-and-lock.md)

### 22. 고급 DB 설계 - PDF 291~319

PPT 흐름:

```text
BCNF·4NF·5NF
→ 반정규화
→ SCD
→ Sharding
→ MSA의 Saga·CQRS·Outbox
```

정리 문서:

- [BCNF와 반정규화](02-relational-modeling-and-sql.md)
- [Scale-out·Sharding](01-database-course-map-and-glossary.md)
- [MSA Database per Service](06-distributed-cloud-and-operations.md)
- [분산 Transaction](04-mvcc-transaction-and-lock.md)
- [특수 Index·Partition·고급 설계](concepts/advanced-index-partition-design.md)

### 23. 종합 실습 3 - PDF 320~325

HR DB의 느린 query를 `EXPLAIN` 전후로 비교하는 실습이다.

복습 순서:

1. [실행 계획에서 볼 것](03-index-query-plan-and-tuning.md)
2. [튜닝 순서](03-index-query-plan-and-tuning.md)
3. [녹음의 실행 계획 설명](07-audio-notes.md)

## Day 4 - DB Programming, Cloud, 보안, 운영

### 24. Stored Procedure와 Function - PDF 327~338

PPT 흐름:

```text
Procedure·Function
→ DBMS별 문법
→ DETERMINISTIC·IMMUTABLE
→ 보안
→ Application과 DB의 역할
```

정리 문서:

- [녹음: DB와 Application 역할](07-audio-notes.md)
- [Procedure·Function·Trigger 상세](concepts/db-programming-procedure-trigger.md)

### 25. Trigger와 Event 처리 - PDF 339~353

PPT 흐름:

```text
DML Trigger
→ 감사 Log
→ Trigger 실행 순서
→ CDC
→ pg_notify
→ DB Logic과 Application Logic 구분
```

정리 문서:

- [CDC와 Outbox 기본](06-distributed-cloud-and-operations.md)
- [Procedure·Function·Trigger 상세](concepts/db-programming-procedure-trigger.md)

### 26. Cloud DB 개요 - PDF 354~363

PPT 흐름:

```text
On-Premise와 DBaaS
→ AWS RDS
→ Aurora
→ GCP Cloud SQL
→ Azure Database
```

정리 문서:

- [관리형 DB와 분산 DB 구분](06-distributed-cloud-and-operations.md)
- [RDS와 Aurora의 ACID·구조 차이](concepts/dbms-acid-differences.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 27. Serverless와 분산 Cloud DB - PDF 364~368

PPT 흐름:

```text
Aurora Serverless
→ Spanner
→ Cosmos DB
→ PlanetScale
→ Neon·Supabase
```

정리 문서:

- [Replication과 Consistency](06-distributed-cloud-and-operations.md)
- [WAL과 Consensus](concepts/wal-and-consensus.md)
- [CAP 해석](06-distributed-cloud-and-operations.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 28. Data Warehouse와 분석 DB - PDF 369~378

PPT 흐름:

```text
OLTP와 OLAP
→ Columnar Storage
→ Partition Pruning
→ Vectorized Execution
→ Redshift·BigQuery·Snowflake·ClickHouse
```

정리 문서:

- [OLTP·OLAP·HTAP](01-database-course-map-and-glossary.md)
- [Data Warehouse와 분석 DB](06-distributed-cloud-and-operations.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 29. 현재 DB Trend - PDF 379~391

PPT 흐름:

```text
NewSQL
→ TimescaleDB
→ Vector DB·pgvector·RAG
→ AI·ML과 DB
→ GraphQL·Edge DB
```

정리 문서:

- [DB 선택 기준](05-dbms-selection-and-migration.md)
- [녹음: Vector DB와 Chunking](07-audio-notes.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 30. 보안과 권한 - PDF 392~433

PPT 흐름:

```text
Authentication·Authorization
→ Role·Privilege
→ Row-Level Security
→ SQL Injection
→ TLS·TDE·Column Encryption
→ 최소 권한과 감사
```

정리 문서:

- [보안](06-distributed-cloud-and-operations.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 31. Backup·Recovery·HA - PDF 434~440

PPT 흐름:

```text
Full·Incremental Backup
→ PITR
→ Streaming Replication
→ Failover
→ DBMS별 HA
```

정리 문서:

- [Backup·Restore·HA·DR](06-distributed-cloud-and-operations.md)
- [WAL과 PITR](concepts/wal-undo-redo-checkpoint.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 32. Monitoring과 운영 - PDF 441~452

PPT 흐름:

```text
TPS·QPS·Latency
→ Prometheus·Grafana
→ Cloud Monitoring
→ 이상 징후
→ Alert
```

정리 문서:

- [운영 수치 용어](01-database-course-map-and-glossary.md)
- [Monitoring](06-distributed-cloud-and-operations.md)
- [운영 Runbook](06-distributed-cloud-and-operations.md)
- [Cloud DB·보안·백업·모니터링 비교](concepts/cloud-security-backup-monitoring.md)

### 33. 종합 실습 4 - PDF 453~460

E-commerce data로 매출, AOV, category 성과, 재구매, RFM, 재고를 분석하고 실행 계획과 Materialized View로 개선하는 실습이다.

복습 순서:

1. [JOIN과 Window Function](02-relational-modeling-and-sql.md)
2. [Materialized View](02-relational-modeling-and-sql.md)
3. [실행 계획](03-index-query-plan-and-tuning.md)
4. [튜닝 순서](03-index-query-plan-and-tuning.md)

## 지금까지 추가된 상세 설명 위치

PPT를 보다가 아래 개념이 나오면 해당 링크를 누른다.

| PPT 개념 | 상세 설명 |
| --- | --- |
| MySQL과 PostgreSQL Schema | [Schema 차이](concepts/mysql-vs-postgresql-schema.md) |
| DBMS별 ACID | [ACID 구현 차이](concepts/dbms-acid-differences.md) |
| WAL·Undo·Redo·Checkpoint | [Log와 복구](concepts/wal-undo-redo-checkpoint.md) |
| WAL과 Consensus | [Local 복구와 분산 합의](concepts/wal-and-consensus.md) |
| Isolation Level 허용 현상 | [동시성 이상 현상](concepts/isolation-level-anomalies.md) |

## 사용 방법

예를 들어 PDF 18쪽을 보고 있다면:

```text
PDF 18쪽
→ 1장 데이터베이스 개요
→ Isolation Level 구간
→ 이 문서의 1장 항목
→ Isolation Level별 이상 현상 링크
```

새로운 상세 설명을 추가할 때도 반드시 이 순차 가이드의 해당 장에 링크를 함께 추가한다.
