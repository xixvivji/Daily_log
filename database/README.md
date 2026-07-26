# Database

데이터베이스 자체의 설계, SQL, 성능, 동시성, 제품 선택, 마이그레이션, 운영을 정리하는 공간이다.

## 학습 자료

- PDF: `스마트 데이터 이해 및 활용` 461쪽
- 녹음: `새로운 녹음 40.m4a` 9분 31초
- 정리일: 2026-07-23

원본 PDF는 저작권이 있는 강의 자료이므로 저장소에 복제하지 않고, 이 디렉터리에는 이해한 내용을 새로 설명한 학습 노트만 둔다.

> 현재 상태: 종합 실습의 문제별 정답을 제외한 29개 개념 장에 상세 본문과 DBMS별 설명을 연결했다. SQL은 DBMS version과 실행 환경에 따라 조정해야 하며, Production 적용 전 실행·성능·복구 검증이 필요하다. 범위와 검증 결과는 [PPT 33장 정리 완성도 점검표](09-ppt-coverage-audit.md)에서 확인한다.

## 읽는 순서

PPT를 보면서 공부할 때는 반드시 첫 번째 문서부터 시작한다.

1. [비전공자를 위한 DB 첫걸음](00-beginner-database-foundation.md)
2. [PPT 1~33장 순차 학습 가이드](00-ppt-sequential-study-guide.md)
3. [MySQL·PostgreSQL·Oracle 비교 가이드](08-cross-dbms-comparison-guide.md)
4. [강의 전체 지도와 용어](01-database-course-map-and-glossary.md)
5. [관계형 모델링과 SQL](02-relational-modeling-and-sql.md)
6. [인덱스, 실행 계획, SQL 튜닝](03-index-query-plan-and-tuning.md)
7. [MVCC, 트랜잭션, Lock](04-mvcc-transaction-and-lock.md)
8. [DBMS 선택, MySQL 대안, 마이그레이션](05-dbms-selection-and-migration.md)
9. [분산·Cloud DB와 운영](06-distributed-cloud-and-operations.md)
10. [녹음 구간 정리](07-audio-notes.md)
11. [PPT 33장 정리 완성도 점검표](09-ppt-coverage-audit.md)

## 상세 개념 전체 목차

### 입문·ERD·관계 모델링

- [ERD 작성 순서](concepts/erd-writing-process.md)
- [Cardinality와 Optionality](concepts/cardinality-and-optionality.md)
- [IE Crow's Foot 표기법](concepts/ie-crows-foot-notation.md)
- [DBML로 ERD 작성하기](concepts/dbml-erd-guide.md)
- [관계 구현과 정규화](concepts/relationship-and-normalization.md)

### Schema·SQL·DBMS 전환

- [MySQL과 PostgreSQL의 Schema 차이](concepts/mysql-vs-postgresql-schema.md)
- [Schema 멀티테넌시와 ANSI SQL](concepts/schema-multitenancy-and-ansi-sql.md)
- [DDL·DML을 MySQL·PostgreSQL·Oracle로 비교](concepts/ddl-dml-cross-dbms.md)
- [집계·JOIN·Subquery·CTE·Window Function](concepts/advanced-sql-cross-dbms.md)
- [NULL·Collation·Timezone](concepts/null-collation-timezone.md)

### Index·실행 계획·저장 구조

- [특수 Index·Partition·고급 설계](concepts/advanced-index-partition-design.md)
- [View·Materialized View·JOIN·Bitmap Scan](concepts/view-join-bitmap-execution-plan.md)
- [저장 구조·Page·Index·VACUUM 내부 원리](concepts/storage-page-index-vacuum-internals.md)

### Transaction·복구·분산 합의

- [DBMS별 ACID 지원 차이](concepts/dbms-acid-differences.md)
- [Isolation Level별 동시성 이상 현상](concepts/isolation-level-anomalies.md)
- [WAL·Undo·Redo·Checkpoint](concepts/wal-undo-redo-checkpoint.md)
- [WAL과 Consensus](concepts/wal-and-consensus.md)

### Application·운영·배포

- [Application·Connection Pool·ORM·Transaction](concepts/application-connection-pool-orm-transaction.md)
- [Procedure·Function·Trigger](concepts/db-programming-procedure-trigger.md)
- [Cloud DB·보안·백업·모니터링](concepts/cloud-security-backup-monitoring.md)
- [무중단 Schema Migration·Online DDL](concepts/zero-downtime-schema-migration.md)

```text
00-beginner 문서
→ 비전공자가 가장 먼저 읽는 기초

00-ppt 문서
→ PPT 순서대로 찾기 위한 목차

01~07 문서
→ 주제별로 다시 묶은 본문

08 문서
→ MySQL에서 배운 내용을 PostgreSQL·Oracle로 옮기는 비교표

09 문서
→ PPT 장별 포함 범위와 실행 검증 필요 항목

concepts 디렉터리
→ 링크를 눌렀을 때만 열리는 상세 설명
```

## 가장 먼저 잡을 기준

```text
논리 모델
→ 어떤 데이터를 어떤 규칙으로 보존할 것인가

물리 모델
→ 선택한 DBMS에서 타입, 인덱스, 파티션을 어떻게 구현할 것인가

쿼리 튜닝
→ 같은 의미의 결과를 더 적은 I/O, CPU, 메모리, 대기로 얻는가

DBMS 전환
→ SQL 문법만 바꾸는 일이 아니라 타입, 동시성, 운영 체계까지 옮기는 일
```

MySQL이 느리다고 바로 PostgreSQL이나 NoSQL로 바꾸는 것은 튜닝이 아니다. 먼저 병목이 쿼리, 인덱스, 통계, 락, 스토리지, 연결 수, 데이터 모델 중 어디인지 측정한다. 다른 엔진으로 바꿔도 같은 접근 패턴과 잘못된 모델을 가져가면 병목도 함께 이동한다.
