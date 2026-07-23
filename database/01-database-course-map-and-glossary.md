# 01. 데이터베이스 강의 전체 지도와 핵심 용어

## 강의 전체 흐름

PDF의 33개 장은 다음 여섯 덩어리로 묶을 수 있다.

| 영역 | PDF 주제 | 실무 질문 |
| --- | --- | --- |
| 기초 원리 | DB 개요, ACID, WAL, 관계형 모델 | 데이터가 깨지지 않는 이유는 무엇인가? |
| 설계 | ERD, 정규화, 개념·논리·물리 모델 | 업무 규칙을 어떤 테이블과 제약으로 표현할까? |
| SQL | DDL, DML, JOIN, 서브쿼리, CTE, Window Function | 원하는 결과를 정확히 어떻게 질의할까? |
| 성능·동시성 | 인덱스, 실행 계획, 튜닝, MVCC, Lock | 왜 느리고, 동시 요청에서 왜 충돌할까? |
| 확장 | MSA DB, Cloud DB, 분산 DB, DW, Vector DB | 한 DB로 해결되지 않을 때 무엇을 분리할까? |
| 운영 | 보안, 백업·복구, HA, 모니터링 | 장애가 나도 복구하고 안전하게 운영할 수 있는가? |

강의 실습의 중심 DBMS는 PostgreSQL이다. MySQL, MariaDB, Oracle, SQL Server와 Cloud DB의 차이를 함께 비교하며, 후반부에는 TimescaleDB, pgvector, NewSQL, 분석 DB까지 넓힌다.

## PDF 페이지 지도

PDF viewer에 표시되는 실제 page 기준이다.

| 페이지 | 장 |
| --- | --- |
| 7~22 | 1. DB 개요, ACID, WAL, 격리 수준 |
| 23~36 | 2. 관계형 모델과 정규화 |
| 37~45 | 3. ERD |
| 46~52 | 4. 개념·논리·물리 모델 |
| 53~69 | 5. Schema 전략과 RDBMS 비교 |
| 70~95 | 6~8. DDL, DML, 1차 실습 |
| 97~223 | 9~16. DB 생태계와 중·고급 SQL |
| 225~325 | 17~23. Index, plan, tuning, MVCC, lock, 고급 설계 |
| 327~353 | 24~25. Stored procedure, function, trigger |
| 354~378 | 26~28. Cloud·분산 DB, Data Warehouse |
| 379~391 | 29. NewSQL, 시계열, Vector DB, AI+DB |
| 392~433 | 30. 보안과 권한 |
| 434~440 | 31. Backup, recovery, HA |
| 441~452 | 32. Monitoring과 운영 |
| 453~460 | 33. E-commerce 종합 실습 |

## DB, DBMS, RDBMS

- **Database(DB)**: 관련 데이터를 일정한 규칙으로 저장한 집합이다.
- **DBMS**: 데이터를 정의하고 읽고 변경하며, 동시성·권한·복구를 관리하는 소프트웨어다.
- **RDBMS**: 관계형 모델을 구현한 DBMS다. PostgreSQL, MySQL, Oracle, SQL Server가 대표적이다.
- **SQL**: 관계형 DBMS와 대화하는 선언형 언어다. “어떻게 순회할지”보다 “어떤 결과가 필요한지”를 표현한다.

제품 이름과 데이터 모델을 구분해야 한다. PostgreSQL은 제품이고 관계형 모델은 이론이며, SQL은 언어다.

## Table, Row, Column

- **Relation/Table**: 같은 구조를 가진 튜플의 집합이다.
- **Tuple/Row/Record**: 하나의 데이터 인스턴스다.
- **Attribute/Column**: 데이터의 한 속성이다.
- **Domain**: 한 속성이 가질 수 있는 값의 범위다. 타입뿐 아니라 `NOT NULL`, `CHECK` 같은 규칙도 포함한다.

SQL 테이블에는 물리적 행 순서가 보장되지 않는다. `ORDER BY`가 없으면 조회 순서를 의존해서는 안 된다.

## Schema의 두 가지 의미

`schema`는 문맥에 따라 뜻이 다르다.

1. 데이터 구조 전체: 테이블, 컬럼, 관계, 제약 조건의 정의
2. DB 객체 namespace: PostgreSQL의 `public.sales`, SQL Server의 `dbo.orders`

MySQL에서 `CREATE SCHEMA`는 사실상 `CREATE DATABASE`의 동의어에 가깝다. PostgreSQL의 한 database 안에 여러 schema를 두는 방식과 같다고 보면 안 된다. → [왜 다른지 자세히 보기](concepts/mysql-vs-postgresql-schema.md)

## Key와 Constraint

- **Candidate Key**: 행을 유일하게 식별할 수 있는 최소 컬럼 집합
- **Primary Key(PK)**: 후보 키 중 대표로 선택한 키
- **Alternate Key**: 선택되지 않은 나머지 후보 키
- **Foreign Key(FK)**: 다른 테이블의 PK 또는 UNIQUE key를 참조하는 제약
- **Natural Key**: 업무 의미가 있는 키
- **Surrogate Key**: 인위적으로 만든 식별자
- **Composite Key**: 두 개 이상 컬럼으로 구성한 키
- **UNIQUE**: 중복을 막는 제약
- **CHECK**: 값이 업무 조건을 만족하는지 검사하는 제약
- **NOT NULL**: 값의 부재를 허용하지 않는 제약

FK는 단순한 “연결 표시”가 아니라 존재 무결성을 DB가 검사하게 만드는 장치다. 인덱스와는 별개이므로, 자주 탐색하거나 부모 삭제·갱신 시 검사가 필요한 FK 컬럼에는 인덱스를 따로 검토한다.

## Cardinality와 Optionality

- **Cardinality**: 한 엔티티가 상대 엔티티 몇 개와 관계를 맺는지 나타낸다. `1:1`, `1:N`, `N:M`이 있다.
- **Optionality**: 관계 참여가 필수인지 선택인지 나타낸다. `0..1`, `1`, `0..N`, `1..N`처럼 표현한다.
- **Junction Table**: `N:M` 관계를 두 개의 `1:N`으로 풀어내는 교차 테이블이다.
- **Weak Entity**: 부모 없이는 식별되거나 존재할 수 없는 엔티티다.

약한 엔티티라고 해서 `ON DELETE CASCADE`가 항상 필수인 것은 아니다. 삭제 정책은 보존 의무, 감사, soft delete 여부에 따라 `RESTRICT`, `CASCADE`, 논리 삭제 중 선택한다.

## Transaction과 ACID

- **Atomicity**: 트랜잭션의 작업은 전부 성공하거나 전부 취소된다.
- **Consistency**: 트랜잭션이 끝난 뒤 정의된 무결성 규칙을 만족한다.
- **Isolation**: 동시에 실행되는 트랜잭션의 중간 상태 노출을 제어한다.
- **Durability**: commit된 결과는 장애 후에도 복구할 수 있다.

일관성을 DBMS가 자동으로 “업무적으로 올바르게” 만들어 주는 것은 아니다. PK, FK, UNIQUE, CHECK, 트랜잭션 경계 같은 규칙을 설계해야 DBMS가 지킬 수 있다.

→ [DBMS별 ACID 지원과 구현 차이 자세히 보기](concepts/dbms-acid-differences.md)

## WAL, Undo, Redo

- **WAL(Write-Ahead Logging)**: 데이터 페이지보다 복구용 로그를 먼저 영속화하는 원칙
- **Redo**: commit되었지만 데이터 파일에 반영되지 않은 변경을 재적용
- **Undo**: 취소할 변경을 이전 상태로 되돌리거나 MVCC의 과거 버전을 제공
- **Checkpoint**: 복구 시 다시 처리할 로그 범위를 줄이도록 메모리의 변경 페이지를 정리하는 기준점

PostgreSQL의 WAL, MySQL InnoDB의 redo log, Oracle의 redo log는 용어와 구현이 완전히 같지는 않지만 “commit 결과를 장애 후 재현한다”는 목적을 공유한다.

→ [WAL, Undo, Redo, Checkpoint 동작 자세히 보기](concepts/wal-undo-redo-checkpoint.md)

→ [WAL과 Consensus의 차이 및 결합 방식 자세히 보기](concepts/wal-and-consensus.md)

## Query 처리 용어

- **Parser**: SQL 문법과 객체 참조를 검사
- **Rewriter**: view나 규칙을 내부 질의로 변환
- **Optimizer/Planner**: 가능한 실행 방법의 비용을 추정해 plan 선택
- **Executor**: 선택된 plan의 scan, join, sort, aggregate를 수행
- **Statistics**: row 수와 값 분포를 추정하기 위한 통계
- **Selectivity**: 조건이 전체 중 얼마나 적은 행을 선택하는지 나타내는 성질
- **Cardinality Estimate**: 각 plan node가 처리할 행 수의 추정

`cost`는 밀리초가 아니다. 옵티마이저가 plan을 비교하기 위한 상대값이다.

## OLTP, OLAP, HTAP

- **OLTP**: 짧은 쓰기·조회 트랜잭션이 많은 운영 업무
- **OLAP**: 많은 행을 스캔·집계하는 분석 업무
- **HTAP**: OLTP와 OLAP을 하나의 계열에서 함께 처리하려는 구조
- **Data Warehouse**: 분석을 위해 여러 원천의 데이터를 통합한 저장소
- **Columnar Storage**: 값을 행보다 컬럼 중심으로 저장해 대량 스캔·압축에 유리한 방식

운영 DB의 read replica를 분석에 활용할 수는 있지만, 무거운 분석 쿼리가 복제 지연과 자원 경합을 일으키는지 확인해야 한다.

## Scale-up, Scale-out, Replication, Sharding

- **Scale-up**: 한 서버의 CPU, RAM, 스토리지를 키움
- **Scale-out**: 노드를 늘려 부하를 분산
- **Replication**: 같은 데이터를 여러 노드에 복제
- **Partitioning**: 한 논리 테이블을 기준에 따라 내부 조각으로 분할
- **Sharding**: 데이터 집합을 여러 독립 DB 노드에 나눔
- **Failover**: 장애 난 primary 대신 standby를 승격

replica를 늘린다고 일반적인 쓰기 처리량이 자동으로 늘지는 않는다. 단일 primary 구조에서는 쓰기가 여전히 primary에 모인다.

## 수치로 보는 운영 용어

- **QPS**: 초당 query 수
- **TPS**: 초당 완료 transaction 수
- **Latency**: 한 요청이 끝나는 데 걸린 시간
- **Throughput**: 단위 시간당 처리량
- **p95/p99**: 요청의 95% 또는 99%가 이 값 이하에서 끝났다는 percentile
- **Replication Lag**: primary 변경이 replica에 반영되기까지의 지연
- **Cache Hit Ratio**: 요청한 page나 결과를 cache에서 찾은 비율

평균 latency만 보면 일부 사용자의 매우 느린 요청을 숨길 수 있다. p95, p99와 분포를 함께 본다.

## 강의 자료를 읽을 때 바로잡을 점

- PostgreSQL 기본 포트는 일반적으로 OS와 무관하게 `5432`다. 특정 설치나 기존 프로세스 때문에 다른 포트를 쓸 수 있다.
- SQL 표준 준수도가 높아도 DBMS 전환이 자동으로 되지는 않는다. 타입, 함수, DDL, 격리 구현, procedural language, 운영 도구가 다르다.
- ORM은 문법 차이 일부를 흡수하지만 native query, dialect 기능, lock, ID 생성, migration까지 자동 이식하지 않는다.
- 높은 cache hit ratio는 목표가 아니라 workload의 결과다. 무조건 `90%+` 같은 숫자를 적용하지 않는다.
- `SERIALIZABLE`은 “순서대로 한 개씩 실행”한다는 뜻이 아니라, 결과가 어떤 직렬 실행과 동등하도록 보장한다는 뜻이다.
