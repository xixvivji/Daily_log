# MySQL·PostgreSQL·Oracle 비교 가이드

[← Database 목차로 돌아가기](README.md)

## 비교 원칙

이 문서는 한 DBMS의 문법을 다른 DBMS에서도 그대로 사용할 수 있다고 설명하지 않는다. 먼저 공통 목적을 이해하고, 제품별 구현을 구분한다.

```text
공통 개념
→ 관계형 모델, PK·FK, Transaction, Index, JOIN

제품별 구현
→ Type, 함수, ID 생성, MVCC, Lock, 실행 계획, 운영 도구
```

## 전체 성격

| 구분 | MySQL | PostgreSQL | Oracle |
| --- | --- | --- | --- |
| 제품 성격 | 사용하기 쉬운 오픈소스 RDBMS | 기능과 확장성이 강한 오픈소스 RDBMS | 엔터프라이즈 상용 RDBMS |
| 대표 engine·구조 | InnoDB | PostgreSQL 기본 storage 구조 | Oracle Database engine |
| 일반적인 기본 격리 | Repeatable Read | Read Committed | Read Committed |
| MVCC 과거 version | Undo log | Table tuple | Undo segment |
| 복구 log | InnoDB redo log | WAL | Redo log |
| 확장 기능 | Storage engine·plugin | Extension | Option·Pack·내장 엔터프라이즈 기능 |
| 자주 쓰는 환경 | Web service, 일반 OLTP | 복잡한 SQL, GIS, JSON, 확장 기능 | 금융·대기업 핵심 업무 |

“어느 DB가 무조건 최고”라는 결론은 없다. workload, 팀 경험, 운영 비용, license, cloud 환경으로 선택한다.

## Database와 Schema

| MySQL | PostgreSQL | Oracle |
| --- | --- | --- |
| Database와 schema가 사실상 동일 | Database 안에 여러 schema | User와 schema가 밀접하게 연결 |

```text
MySQL
Server → Database(Schema) → Table

PostgreSQL
Server → Database → Schema → Table

Oracle
Database → User·Schema → Object
```

[Schema 차이 상세 설명](concepts/mysql-vs-postgresql-schema.md)

## 자동 ID

### MySQL

```sql
CREATE TABLE members (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```

### PostgreSQL

```sql
CREATE TABLE members (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```

과거에는 `SERIAL`도 많이 사용했지만 새 설계에서는 SQL 표준에 가까운 identity를 우선 검토한다.

### Oracle

```sql
CREATE TABLE members (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100) NOT NULL
);
```

legacy Oracle에서는 sequence와 trigger 또는 `sequence.NEXTVAL`을 사용하는 구조도 많다.

## 문자열 Type

### MySQL

```sql
name VARCHAR(100)
description TEXT
```

charset와 collation 설정이 저장과 비교에 큰 영향을 준다.

### PostgreSQL

```sql
name VARCHAR(100)
description TEXT
```

`VARCHAR(n)`과 `TEXT`의 성능 차이보다 업무상 길이 제한 여부가 더 중요한 경우가 많다.

### Oracle

```sql
name VARCHAR2(100)
description CLOB
```

Oracle에서는 일반 문자열에 `VARCHAR2`를 사용한다. `VARCHAR`를 Oracle과 다른 DB에서 동일한 의미로 가정하지 않는다.

## 숫자와 금액

```text
정수 ID
→ BIGINT 또는 NUMBER 범위 검토

금액
→ DECIMAL·NUMERIC·NUMBER처럼 정확한 10진 type 사용

과학 계산
→ FLOAT·DOUBLE 같은 부동소수점 검토
```

```sql
-- MySQL
amount DECIMAL(12, 2)

-- PostgreSQL
amount NUMERIC(12, 2)

-- Oracle
amount NUMBER(12, 2)
```

금액에 binary floating point를 사용하면 반올림 오차가 발생할 수 있다.

## Boolean

### MySQL

`BOOLEAN`은 일반적으로 `TINYINT(1)`의 별칭처럼 처리된다.

```sql
is_active BOOLEAN NOT NULL DEFAULT TRUE
```

### PostgreSQL

native `boolean` type이 있다.

```sql
is_active BOOLEAN NOT NULL DEFAULT TRUE
```

### Oracle

최신 Oracle version과 SQL·PL/SQL 문맥의 boolean 지원 범위를 확인해야 한다. legacy schema에서는 다음 표현이 흔하다.

```sql
is_active CHAR(1)
    CHECK (is_active IN ('Y', 'N'))
```

Migration에서는 `0/1`, `TRUE/FALSE`, `Y/N` 의미를 명시적으로 변환한다.

## 날짜와 시간

날짜·시간은 가장 주의해야 하는 migration 항목 중 하나다.

### MySQL

- `DATE`
- `DATETIME`
- `TIMESTAMP`

`TIMESTAMP`와 `DATETIME`의 timezone 변환과 값 범위가 다르다.

### PostgreSQL

- `date`
- `timestamp without time zone`
- `timestamp with time zone`, 보통 `timestamptz`

`timestamptz`는 절대 시점을 저장하고 session timezone에 맞춰 표시하지만 원래 timezone 이름 자체를 보존하지 않는다.

### Oracle

- `DATE`: 날짜뿐 아니라 시·분·초 포함
- `TIMESTAMP`
- `TIMESTAMP WITH TIME ZONE`
- `TIMESTAMP WITH LOCAL TIME ZONE`

Oracle `DATE`를 PostgreSQL `date`로 무조건 변환하면 시간 정보가 사라질 수 있다.

## 현재 시각

```sql
-- MySQL
SELECT NOW();

-- PostgreSQL
SELECT CURRENT_TIMESTAMP;

-- Oracle
SELECT CURRENT_TIMESTAMP FROM dual;
```

transaction 시작 시각인지 statement 실행 시각인지도 함수별로 다를 수 있다.

## 문자열 연결

```sql
-- MySQL
SELECT CONCAT(first_name, ' ', last_name);

-- PostgreSQL
SELECT first_name || ' ' || last_name;

-- Oracle
SELECT first_name || ' ' || last_name FROM members;
```

`NULL`이 포함될 때 결과가 어떻게 되는지도 제품과 함수에 따라 확인한다.

## Pagination

### MySQL

```sql
SELECT *
FROM orders
ORDER BY id DESC
LIMIT 20 OFFSET 100;
```

### PostgreSQL

```sql
SELECT *
FROM orders
ORDER BY id DESC
LIMIT 20 OFFSET 100;
```

### Oracle

```sql
SELECT *
FROM orders
ORDER BY id DESC
OFFSET 100 ROWS FETCH NEXT 20 ROWS ONLY;
```

큰 OFFSET은 세 DB 모두 비용이 커질 수 있다. 안정적인 정렬 key를 이용한 keyset pagination을 검토한다.

## Upsert

### MySQL

```sql
INSERT INTO members(email, name)
VALUES ('kim@example.com', '김개발')
ON DUPLICATE KEY UPDATE
name = VALUES(name);
```

version에 따라 새 row alias 등 권장 문법을 확인한다.

### PostgreSQL

```sql
INSERT INTO members(email, name)
VALUES ('kim@example.com', '김개발')
ON CONFLICT (email)
DO UPDATE SET name = EXCLUDED.name;
```

### Oracle

```sql
MERGE INTO members m
USING (
    SELECT 'kim@example.com' email, '김개발' name
    FROM dual
) s
ON (m.email = s.email)
WHEN MATCHED THEN
    UPDATE SET m.name = s.name
WHEN NOT MATCHED THEN
    INSERT (email, name)
    VALUES (s.email, s.name);
```

Upsert는 unique constraint와 동시성 의미를 함께 확인한다.

## JSON

### MySQL

native JSON type과 JSON 함수를 제공한다.

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    attrs JSON
);
```

### PostgreSQL

`json`과 binary 처리·index 활용에 유리한 `jsonb`를 구분한다.

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    attrs JSONB
);

CREATE INDEX idx_products_attrs
ON products USING GIN(attrs);
```

### Oracle

version에 따라 native JSON type 또는 JSON constraint와 함수 지원 범위가 다르다.

JSON에 넣을 수 있다는 이유만으로 모든 column을 JSON으로 만들면 FK, type constraint, JOIN, 통계, update가 어려워질 수 있다.

## Index 기본

세 DB 모두 B-Tree 계열 index를 일반적인 equality·range 검색에 사용하지만 물리 구조와 추가 기능이 다르다.

### MySQL InnoDB

- PK가 clustered index
- table row가 PK 순서의 clustered 구조에 저장
- secondary index leaf에 PK 값 포함

### PostgreSQL

- heap table과 index가 분리
- B-Tree, Hash, GIN, GiST, SP-GiST, BRIN 등
- partial, expression, INCLUDE index

### Oracle

- B-Tree, bitmap, function-based index 등
- Index Organized Table 선택 가능
- bitmap index는 일반적인 고동시성 OLTP update에 주의

`Clustered Index`라는 같은 표현도 DBMS별 구조가 다르므로 이름만 대응시키지 않는다.

## 실행 계획

### MySQL

```sql
EXPLAIN ANALYZE
SELECT ...
```

Performance Schema와 slow query log도 활용한다.

### PostgreSQL

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

`pg_stat_statements`로 query별 누적 통계를 볼 수 있다.

### Oracle

```sql
EXPLAIN PLAN FOR
SELECT ...;

SELECT *
FROM TABLE(DBMS_XPLAN.DISPLAY);
```

실제 cursor plan과 실행 통계는 `DBMS_XPLAN.DISPLAY_CURSOR` 등을 검토한다.

공통 확인 항목:

- 예상 row와 실제 row
- scan 방식
- JOIN 순서와 algorithm
- sort와 temporary space
- 반복 횟수
- buffer·I/O

## MVCC와 Undo

| 관점 | MySQL InnoDB | PostgreSQL | Oracle |
| --- | --- | --- | --- |
| 과거 version | Undo log | Table의 old tuple | Undo segment |
| 불필요 version 정리 | Purge | VACUUM | Undo retention·재사용 |
| 기본 격리 | Repeatable Read | Read Committed | Read Committed |

[Isolation Level 상세 비교](concepts/isolation-level-anomalies.md)

## WAL과 Redo

| 목적 | MySQL InnoDB | PostgreSQL | Oracle |
| --- | --- | --- | --- |
| Crash recovery | Redo log | WAL | Redo log |
| Rollback·과거 version | Undo log | Tuple version | Undo segment |
| Replication·PITR 주요 log | Binary log 등 | WAL | Archived redo |

[WAL·Undo·Redo 상세 설명](concepts/wal-undo-redo-checkpoint.md)

## Procedure와 Function

### MySQL

stored procedure와 function을 지원하며 delimiter 처리와 routine 권한을 이해해야 한다.

### PostgreSQL

SQL, PL/pgSQL 등으로 function과 procedure를 작성할 수 있다. volatility 분류인 `IMMUTABLE`, `STABLE`, `VOLATILE`이 optimizer와 사용 위치에 영향을 준다.

### Oracle

PL/SQL package, procedure, function 생태계가 강력하다. package에 관련 type과 routine을 묶을 수 있다.

DB 내부 logic은 network 왕복과 set-based 처리를 줄일 수 있지만 다음 비용이 있다.

- Vendor lock-in
- Application과 DB로 logic 분산
- Test와 배포 체계 복잡
- DB server CPU 집중

## Trigger

세 DB 모두 trigger를 지원하지만 문법, row·statement 단위, 실행 순서, mutation 제약이 다르다.

Trigger가 적합할 수 있는 일:

- 짧고 결정적인 감사 정보
- DB를 거치는 모든 변경에 적용해야 하는 무결성 보조
- 단순 derived value

주의할 일:

- 외부 API 호출
- 긴 batch
- 복잡하고 자주 변하는 business flow
- trigger 안에서 또 다른 trigger를 연쇄 호출

## 사용자와 권한

### MySQL

```text
User@Host
→ 접속 계정과 접속 위치가 함께 중요
```

### PostgreSQL

user와 group을 `ROLE` 개념으로 통합하고 `LOGIN` 속성으로 접속 가능 여부를 구분한다.

### Oracle

user가 schema 소유와 밀접하게 연결되고 system privilege, object privilege, role을 구분한다.

공통 원칙:

- Application 계정에 관리자 권한 금지
- 읽기·쓰기·Migration role 분리
- 비밀번호와 secret rotation
- 최소 권한
- 감사 log

## Backup과 시점 복구

### MySQL

- Logical dump: `mysqldump`, MySQL Shell
- Physical backup 도구
- Binary log를 이용한 PITR

### PostgreSQL

- Logical: `pg_dump`, `pg_restore`
- Physical base backup
- Archived WAL을 이용한 PITR

### Oracle

- Data Pump
- RMAN
- Archived redo를 이용한 recovery

Replication은 backup이 아니다. 삭제 실수도 replica에 복제될 수 있다.

## Migration 점검표

MySQL에서 PostgreSQL이나 Oracle로 옮길 때 다음을 확인한다.

```text
Schema 계층
Type 범위와 정밀도
AUTO_INCREMENT·IDENTITY·SEQUENCE
Boolean 표현
날짜·시간과 timezone
Collation과 대소문자 비교
NULL과 빈 문자열
Upsert와 MERGE
JSON 함수
Index 종류
Isolation과 Lock
Procedure·Function·Trigger
사용자·Role·권한
Backup·PITR·Replication
Monitoring Query
```

특히 Oracle은 빈 문자열 `''`을 `NULL`처럼 취급하는 특성이 있어 MySQL·PostgreSQL application을 옮길 때 주의한다.

## 어떤 DB를 선택할까

### MySQL을 우선 검토할 상황

- 일반적인 Web OLTP
- 팀이 MySQL 운영에 익숙함
- MySQL 생태계와 호환 서비스 활용

### PostgreSQL을 우선 검토할 상황

- 복잡한 SQL
- JSONB, GIS, Vector, 시계열 extension
- partial·expression index
- 표준 기능과 확장성을 적극 활용

### Oracle을 우선 검토할 상황

- 기존 Oracle 핵심 업무와 통합
- PL/SQL과 상용 enterprise 기능 의존
- Vendor support와 조직 표준이 중요

기술 기능만으로 결정하지 않는다.

```text
License
Cloud 비용
운영 인력
Backup·복구 경험
Monitoring
Migration 위험
장애 대응 체계
```

## 학습할 때 작성할 비교표

새 기능을 배울 때 다음 틀로 기록한다.

| 질문 | 공통 개념 | MySQL | PostgreSQL | Oracle |
| --- | --- | --- | --- | --- |
| 어떤 문제를 해결하는가? |  |  |  |  |
| 기본 문법은? |  |  |  |  |
| 내부 동작은? |  |  |  |  |
| 성능 비용은? |  |  |  |  |
| 운영 시 주의점은? |  |  |  |  |
| 다른 DB로 옮길 때 무엇이 깨지는가? |  |  |  |  |

