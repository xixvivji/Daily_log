# 데이터베이스 첫걸음

[← Database 목차로 돌아가기](README.md)

## 이 문서를 먼저 읽는 이유

데이터베이스 강의에서는 첫날부터 DBMS, schema, transaction, WAL 같은 단어가 나온다. 이런 단어를 바로 외우면 각각의 관계를 놓치기 쉽다.

이 문서는 다음 질문부터 시작한다.

```text
데이터베이스는 왜 필요한가?
Excel 파일과 무엇이 다른가?
MySQL과 PostgreSQL은 무엇인가?
SQL은 프로그램인가, 언어인가?
Table과 Schema는 어떤 관계인가?
```

## 1. 데이터란 무엇인가

데이터는 어떤 사실을 기록한 값이다.

```text
회원 번호: 101
이름: 김개발
이메일: dev@example.com
가입일: 2026-07-23
```

값 몇 개만 있을 때는 메모장이나 Excel로도 관리할 수 있다. 하지만 사용자가 늘어나면 다음 문제가 생긴다.

- 두 사람이 같은 파일을 동시에 수정하면 충돌한다.
- 같은 이메일이 여러 번 저장될 수 있다.
- 주문은 저장됐는데 결제 기록은 사라질 수 있다.
- 누가 어떤 정보를 볼 수 있는지 통제하기 어렵다.
- 서버가 꺼진 뒤 어디까지 저장됐는지 판단하기 어렵다.

데이터베이스는 값을 저장하는 공간뿐 아니라 이런 규칙과 동시 작업, 복구를 관리한다.

## 2. Database와 DBMS

### Database

서로 관련된 데이터를 일정한 구조로 모은 것이다.

```text
쇼핑몰 Database
├── 회원 데이터
├── 상품 데이터
├── 주문 데이터
└── 결제 데이터
```

### DBMS

Database를 생성하고 읽고 수정하고 보호하는 software다.

대표적인 DBMS:

- MySQL
- PostgreSQL
- Oracle Database
- Microsoft SQL Server

비유하면:

```text
Database
→ 도서관에 보관된 책과 정보

DBMS
→ 책을 분류하고 대출하고 권한을 관리하는 도서관 시스템

SQL
→ 도서관 시스템에 요청하는 언어
```

MySQL과 PostgreSQL은 database 그 자체의 일반 명칭이 아니라 DBMS 제품 이름이다.

## 3. 관계형 Database

관계형 Database는 데이터를 table 형태로 표현하고 table 사이의 관계를 정의한다.

### 회원 Table

| id | name | email |
| ---: | --- | --- |
| 1 | 김개발 | kim@example.com |
| 2 | 이데이터 | lee@example.com |

### 주문 Table

| id | member_id | amount |
| ---: | ---: | ---: |
| 1001 | 1 | 30000 |
| 1002 | 1 | 15000 |
| 1003 | 2 | 22000 |

`orders.member_id`가 `members.id`를 가리키므로 어떤 회원의 주문인지 찾을 수 있다.

## 4. Table, Row, Column

```text
Table
→ 같은 종류의 데이터를 모은 표

Row
→ 하나의 대상 또는 사건

Column
→ 대상이 가진 한 가지 속성
```

회원 table에서:

```text
Table  = members
Row    = 한 명의 회원
Column = id, name, email
```

table은 Excel sheet와 비슷하게 보이지만 중요한 차이가 있다.

- column마다 type과 constraint를 정의할 수 있다.
- 여러 사용자의 동시 변경을 transaction으로 제어한다.
- table 사이의 관계를 FK로 보호한다.
- index와 optimizer로 큰 데이터도 효율적으로 찾는다.
- backup과 recovery 기능이 있다.

## 5. Primary Key

Primary Key는 각 row를 유일하게 식별하는 값이다.

```sql
CREATE TABLE members (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```

동명이인이 있을 수 있으므로 이름은 좋은 PK가 아니다.

| id | name |
| ---: | --- |
| 1 | 김민수 |
| 2 | 김민수 |

`id`가 다르기 때문에 서로 다른 회원으로 식별할 수 있다.

PK의 일반적인 특성:

- 중복 불가
- `NULL` 불가
- 한 table에 하나의 PK constraint
- 여러 column을 묶은 복합 PK도 가능

## 6. Foreign Key

Foreign Key는 다른 table의 존재하는 row를 참조하도록 만드는 제약이다.

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id)
);
```

회원 999가 존재하지 않으면 다음 주문을 저장하지 못하게 할 수 있다.

```sql
INSERT INTO orders(id, member_id, amount)
VALUES (1004, 999, 10000);
```

FK는 단순히 두 table을 JOIN하기 위한 표시가 아니다. 존재하지 않는 회원의 주문 같은 잘못된 상태를 DB가 차단하는 규칙이다.

## 7. SQL과 Query

SQL은 관계형 DBMS에 원하는 작업을 표현하는 언어다.

### 조회

```sql
SELECT id, name, email
FROM members
WHERE id = 1;
```

### 입력

```sql
INSERT INTO members(id, name, email)
VALUES (1, '김개발', 'kim@example.com');
```

### 수정

```sql
UPDATE members
SET email = 'new@example.com'
WHERE id = 1;
```

### 삭제

```sql
DELETE FROM members
WHERE id = 1;
```

Query는 DB에 보내는 요청을 뜻한다. 일상적으로 `SELECT`뿐 아니라 INSERT, UPDATE, DELETE statement도 query라고 부르기도 한다.

SQL은 선언형 언어다.

```text
개발자가 표현
→ 어떤 결과가 필요한가

DBMS Optimizer가 결정
→ 어떤 index와 JOIN 순서로 실행할 것인가
```

## 8. Server, Database, Schema, Table

이 계층은 DBMS마다 다르다.

### MySQL

```text
MySQL Server
└── Database(Schema)
    └── Table
```

MySQL에서는 database와 schema를 사실상 같은 의미로 사용한다.

```sql
CREATE DATABASE shop;
CREATE SCHEMA campus;
```

### PostgreSQL

```text
PostgreSQL Server
└── Database
    └── Schema
        └── Table
```

한 database 안에 여러 schema를 만들 수 있다.

```sql
CREATE SCHEMA sales;
CREATE SCHEMA inventory;
```

### Oracle

Oracle의 schema는 일반적으로 database user가 소유한 객체 집합과 밀접하게 연결된다.

```text
Oracle Database
└── User·Schema
    ├── Table
    ├── View
    ├── Sequence
    └── Procedure
```

같은 `schema`라는 단어를 제품마다 똑같이 해석하면 안 된다.

[MySQL과 PostgreSQL Schema 차이 자세히 보기](concepts/mysql-vs-postgresql-schema.md)

## 9. Constraint

Constraint는 저장할 수 있는 data의 규칙이다.

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    stock INT NOT NULL,
    CONSTRAINT chk_products_price CHECK (price >= 0),
    CONSTRAINT chk_products_stock CHECK (stock >= 0)
);
```

- `PRIMARY KEY`: row 식별
- `FOREIGN KEY`: 다른 row 참조
- `UNIQUE`: 중복 금지
- `NOT NULL`: 값 누락 금지
- `CHECK`: 조건을 만족하는 값만 허용

Application에서도 validation해야 하지만 DB constraint는 동시 요청과 여러 application이 접근하는 상황의 최종 방어선이다.

## 10. Transaction

Transaction은 여러 DB 작업을 하나의 업무 단위로 묶는다.

쇼핑몰 주문:

```text
주문 생성
→ 재고 차감
→ 결제 기록
```

재고만 줄고 주문 저장이 실패하면 data가 깨진다.

```sql
BEGIN;

INSERT INTO orders ...;
UPDATE products SET stock = stock - 1 ...;
INSERT INTO payments ...;

COMMIT;
```

중간에 실패하면:

```sql
ROLLBACK;
```

`COMMIT`은 변경을 확정하고, `ROLLBACK`은 transaction의 변경을 취소한다.

## 11. ACID

ACID는 transaction이 지켜야 할 대표적인 네 가지 성질이다.

### Atomicity

전부 성공하거나 전부 취소된다.

### Consistency

transaction 전후에 정의한 data 규칙을 만족한다.

### Isolation

동시에 실행되는 transaction이 서로의 중간 상태를 함부로 보지 않게 한다.

### Durability

성공적으로 commit된 결과는 장애 후에도 복구할 수 있어야 한다.

[DBMS별 ACID 차이 자세히 보기](concepts/dbms-acid-differences.md)

## 12. Index

Index는 원하는 row를 빨리 찾기 위한 별도 자료 구조다.

책에서 특정 단어를 찾는 상황에 비유할 수 있다.

```text
Index 없음
→ 첫 page부터 모두 읽음

색인 있음
→ 색인에서 page 위치를 찾은 뒤 해당 page로 이동
```

```sql
CREATE INDEX idx_members_email
ON members(email);
```

Index는 조회를 빠르게 할 수 있지만 공짜가 아니다.

- INSERT할 때 index에도 값을 추가
- UPDATE할 때 index도 변경될 수 있음
- DELETE할 때 index entry도 정리
- disk와 memory 추가 사용

모든 column에 index를 만들면 오히려 쓰기가 느려진다.

## 13. 실행 계획

DBMS는 SQL을 받은 뒤 가능한 실행 방법을 비교한다.

```text
Table 전체 읽기
Index 사용
먼저 orders를 읽기
먼저 members를 읽기
Nested Loop
Hash Join
```

실제로 선택한 방법을 실행 계획이라고 한다.

PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM members
WHERE email = 'kim@example.com';
```

MySQL:

```sql
EXPLAIN ANALYZE
SELECT *
FROM members
WHERE email = 'kim@example.com';
```

Oracle:

```sql
EXPLAIN PLAN FOR
SELECT *
FROM members
WHERE email = 'kim@example.com';

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
```

출력 형식과 node 이름은 다르지만 공통 질문은 같다.

```text
몇 row를 읽었는가?
몇 row를 반환했는가?
Index를 사용했는가?
어떤 순서로 JOIN했는가?
예상 row와 실제 row가 얼마나 다른가?
```

## 14. MySQL만 외우면 안 되는 이유

관계형 개념은 공통이지만 구현과 문법은 다르다.

예를 들어 자동 증가 ID:

```sql
-- MySQL
id BIGINT AUTO_INCREMENT PRIMARY KEY
```

```sql
-- PostgreSQL
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

```sql
-- Oracle
id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

문법을 외우기 전에 공통 목적을 먼저 말할 수 있어야 한다.

```text
공통 목적
→ 각 row의 고유 ID를 DB가 생성

제품별 구현
→ AUTO_INCREMENT, IDENTITY, SEQUENCE
```

## 15. 공부하는 방법

각 개념을 다음 순서로 정리한다.

```text
1. 이 기능은 어떤 문제를 해결하는가?
2. 모든 관계형 DB에 공통인 원리는 무엇인가?
3. MySQL에서는 어떻게 사용하는가?
4. PostgreSQL에서는 무엇이 다른가?
5. Oracle에서는 무엇이 다른가?
6. 실제로 실행 계획이나 결과를 확인했는가?
```

나쁜 암기:

```text
PostgreSQL은 EXPLAIN ANALYZE를 쓴다.
```

좋은 이해:

```text
실행 계획은 DB가 SQL을 어떤 scan과 JOIN으로 처리하는지 보여준다.
PostgreSQL에서는 EXPLAIN ANALYZE,
MySQL에서는 EXPLAIN ANALYZE,
Oracle에서는 DBMS_XPLAN 등의 방식으로 확인한다.
```

## 다음에 읽을 문서

1. [PPT 1~33장 순차 학습 가이드](00-ppt-sequential-study-guide.md)
2. [MySQL·PostgreSQL·Oracle 비교 가이드](08-cross-dbms-comparison-guide.md)
3. [강의 전체 지도와 용어](01-database-course-map-and-glossary.md)

