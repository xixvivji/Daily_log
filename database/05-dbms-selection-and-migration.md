# 05. DBMS 선택, MySQL 대안, 마이그레이션

## 먼저 결론

MySQL query를 PostgreSQL 방식으로 다시 튜닝하거나, MySQL에서 다른 DBMS로 전환하는 것은 가능하다. 그러나 다음 세 작업을 구분해야 한다.

```text
같은 MySQL 안에서 튜닝
→ schema, query, index, 통계, 설정, topology 개선

호환 계열로 이전
→ MySQL → MariaDB, Aurora MySQL, TiDB 등

다른 엔진으로 전환
→ MySQL → PostgreSQL, Oracle, SQL Server, 분석 DB, NoSQL
```

호환을 표방하는 제품도 버전, optimizer, replication, transaction, extension이 완전히 같지는 않다. 반드시 실제 workload로 검증한다.

## 선택 기준

| 요구 | 우선 검토 후보 | 이유와 주의 |
| --- | --- | --- |
| 일반 웹 OLTP, 익숙한 생태계 | MySQL/InnoDB | 운영 인력과 도구가 풍부 |
| 복잡한 SQL, JSONB, GIS, extension | PostgreSQL | 표준 기능과 확장성이 강함 |
| MySQL 관리 부담 감소 | Aurora MySQL, Cloud SQL, RDS | 운영 자동화와 vendor lock-in 비교 |
| PostgreSQL 관리 부담 감소 | Aurora PostgreSQL, Cloud SQL, RDS | extension·version 지원 범위 확인 |
| 대기업 상용 기능과 지원 | Oracle, SQL Server | license와 전문 인력 비용 |
| 대량 columnar 분석 | BigQuery, Snowflake, Redshift, ClickHouse | OLTP 대체가 아니라 분석 workload 분리 |
| 검색·전문 검색 | Elasticsearch/OpenSearch | source of truth와 동기화 전략 필요 |
| cache·session·rate limit | Redis | 영속 DB의 무조건적 대체가 아님 |
| 시계열 | TimescaleDB, InfluxDB 등 | SQL 필요성, retention, cardinality 비교 |
| vector 유사도 검색 | pgvector 또는 전용 vector DB | 규모, filter, consistency, 운영 복잡성 비교 |
| 수평 확장 SQL | Spanner, CockroachDB, TiDB 등 | 지연, consistency, SQL 호환, 비용 검증 |

## MySQL을 먼저 튜닝해야 하는 경우

- 단일 query의 index와 plan이 문제
- N+1 또는 불필요한 `SELECT *`
- 긴 transaction과 lock contention
- 잘못된 connection pool
- buffer pool과 working set 불일치
- 오래된 statistics
- read/write 분리나 partitioning으로 충분

제품 교체는 이런 문제를 자동 해결하지 않는다.

## PostgreSQL로 옮길 이유가 될 수 있는 것

- window function, CTE, complex type과 고급 SQL을 적극 활용
- JSONB와 GIN, expression/partial index가 workload에 잘 맞음
- PostGIS, pgvector, TimescaleDB 같은 extension이 핵심
- PostgreSQL 생태계와 운영 역량이 이미 있음
- 특정 consistency, constraint, query 기능이 더 자연스럽게 구현됨

반대로 팀이 MySQL 운영에 익숙하고 기능 차이가 실제 병목과 무관하다면 migration의 위험이 이득보다 클 수 있다.

## SQL과 DDL의 대표 차이

| 관심사 | MySQL | PostgreSQL |
| --- | --- | --- |
| 자동 ID | `AUTO_INCREMENT` | `GENERATED ... AS IDENTITY` |
| upsert | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT ... DO UPDATE` |
| boolean | `BOOLEAN`은 `TINYINT(1)` 계열 | native `boolean` |
| JSON | binary internal JSON과 함수 | `json`, `jsonb`, GIN |
| 대소문자 무시 검색 | collation 영향, `LIKE` | `ILIKE`, collation, `citext` |
| identifier quote | backtick | double quote |
| string concat | `CONCAT()` | `||`, `concat()` |
| timezone | `TIMESTAMP`, `DATETIME` 동작 구분 | `timestamp`, `timestamptz` 구분 |
| index | generated/functional index 등 | expression, partial, INCLUDE, GIN/GiST 등 |

표는 출발점일 뿐이다. collation, NULL 정렬, implicit cast, integer division, alias 허용 범위도 결과를 바꿀 수 있다.

## Transaction과 동시성 차이

- MySQL InnoDB의 일반적 기본 격리는 Repeatable Read다.
- PostgreSQL의 일반적 기본 격리는 Read Committed다.
- MySQL InnoDB는 clustered primary key 구조이며 secondary index leaf에 PK가 포함된다.
- PostgreSQL heap과 index는 분리되어 있고 MVCC tuple 정리에 VACUUM이 중요하다.
- deadlock, gap lock, `SELECT FOR UPDATE`, DDL lock의 범위와 관찰 도구가 다르다.

같은 schema와 query를 옮겨도 contention pattern이 달라질 수 있으므로 동시성 test가 필수다.

## 마이그레이션 단계

### 1. Inventory

- table, view, materialized view
- index, constraint, partition
- procedure, function, trigger, event scheduler
- user, role, privilege
- ORM dialect, native query, batch
- CDC, ETL, BI, backup, monitoring

### 2. Compatibility Assessment

- 타입 범위와 정밀도
- default, generated column, sequence
- SQL 함수와 문법
- collation과 정렬
- NULL과 빈 문자열 의미
- isolation과 locking
- extension과 plugin 대체

### 3. Schema Conversion

자동 변환 결과를 그대로 신뢰하지 않는다. ID 생성, timestamp, enum, JSON, index, partition을 사람이 검토한다.

### 4. Data Movement

- offline dump/restore
- bulk load
- CDC로 변경분 지속 복제
- 큰 table의 chunk 분할과 검증

### 5. Application Dual Preparation

두 DB에 무조건 dual write하면 부분 실패 처리 때문에 더 위험할 수 있다. CDC, outbox, migration service 중 일관성 모델에 맞는 방식을 택한다.

### 6. Verification

- table별 row count
- PK 범위별 checksum 또는 aggregate
- 중요 업무 query 결과 비교
- 제약 위반과 orphan 확인
- 성능·동시성·장애 test

### 7. Cutover와 Rollback

```text
쓰기 동결 또는 최종 CDC catch-up
→ replication lag 0 확인
→ application endpoint 전환
→ smoke test
→ 집중 관찰
```

rollback 시 새 DB에서 발생한 쓰기를 어떻게 되돌릴지가 문서화되지 않았다면 rollback plan이 아니다.

## 도구 예시

- MySQL → PostgreSQL: `pgloader`, AWS DMS, cloud migration service, Debezium
- PostgreSQL 논리 이동: `pg_dump/pg_restore`, logical replication
- MySQL 논리 이동: `mysqldump`, MySQL Shell dump/load

도구가 schema와 data를 옮겨도 의미와 성능을 검증하는 책임까지 대신하지 않는다.

## 성능 비교 방법

1. production을 대표하는 query mix를 만든다.
2. 동일한 데이터 양과 분포를 준비한다.
3. cold/warm cache를 구분한다.
4. 단일 query뿐 아니라 동시 사용자 부하를 준다.
5. p50/p95/p99, throughput, error, CPU, I/O, lock을 기록한다.
6. failover, backup, restore까지 시험한다.
7. license, storage, network, 운영 인력까지 총비용을 계산한다.

## 결정 질문

```text
현재 병목이 DB 제품의 구조적 한계인가?
현재 DB에서 해결할 수 있는 방법을 측정했는가?
새 DB가 핵심 workload를 실제로 더 잘 처리하는가?
팀이 backup, restore, failover, tuning을 운영할 수 있는가?
전환 중 데이터 정합성과 rollback을 보장할 수 있는가?
```

