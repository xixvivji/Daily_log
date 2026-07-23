# DDL·DML - MySQL·PostgreSQL·Oracle 비교

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## 먼저 구분하기

```text
DDL
→ Data Definition Language
→ Database 구조 정의
→ CREATE, ALTER, DROP, TRUNCATE

DML
→ Data Manipulation Language
→ Data 조회·입력·수정·삭제
→ SELECT, INSERT, UPDATE, DELETE, MERGE
```

## CREATE DATABASE

### MySQL

```sql
CREATE DATABASE shop
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

MySQL에서 database와 schema는 사실상 같은 계층이다.

### PostgreSQL

```sql
CREATE DATABASE shop
    WITH ENCODING 'UTF8';
```

database를 만든 뒤 해당 database에 접속하여 schema와 table을 만든다.

### Oracle

Oracle database 생성은 일반 application 개발자가 실행하는 단순 DDL보다 instance·storage·character set을 포함하는 관리자 작업에 가깝다. 일반적으로 application용 user와 schema, tablespace를 준비한다.

```sql
CREATE USER shop_app IDENTIFIED BY "strong-password";
```

Cloud와 조직 환경에서는 DBA나 관리 서비스가 database를 생성한다.

## CREATE SCHEMA

```sql
-- MySQL: CREATE DATABASE와 사실상 같은 의미
CREATE SCHEMA shop;
```

```sql
-- PostgreSQL: 현재 database 안의 namespace
CREATE SCHEMA sales;
```

Oracle schema는 user가 소유한 객체 집합과 밀접하게 연결된다.

## CREATE TABLE 공통 예제

```sql
CREATE TABLE members (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT chk_members_status
        CHECK (status IN ('ACTIVE', 'BLOCKED'))
);
```

개념적으로 공통이지만 type과 ID 생성 방식은 조정한다.

## 자동 ID 비교

### MySQL

```sql
id BIGINT AUTO_INCREMENT PRIMARY KEY
```

### PostgreSQL

```sql
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

### Oracle

```sql
id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

Legacy Oracle에서는 sequence를 사용할 수 있다.

```sql
CREATE SEQUENCE members_seq START WITH 1 INCREMENT BY 1;
```

## ALTER TABLE

### Column 추가

```sql
ALTER TABLE members
ADD COLUMN phone VARCHAR(30);
```

Oracle에서는 `COLUMN` keyword 없이 작성하는 형식이 일반적이다.

```sql
ALTER TABLE members
ADD phone VARCHAR2(30);
```

### Column type 변경

```sql
-- MySQL
ALTER TABLE members
MODIFY COLUMN phone VARCHAR(50);

-- PostgreSQL
ALTER TABLE members
ALTER COLUMN phone TYPE VARCHAR(50);

-- Oracle
ALTER TABLE members
MODIFY phone VARCHAR2(50);
```

Type 변경은 table rewrite, lock, 긴 실행 시간, 변환 실패를 일으킬 수 있다. 큰 table에서는 online schema change와 단계적 migration을 검토한다.

### NOT NULL 추가

기존 NULL row가 있으면 바로 실패할 수 있다.

안전한 흐름:

```text
1. Nullable column 추가
2. Application이 새 값을 쓰도록 배포
3. 기존 row backfill
4. NULL 검증
5. NOT NULL constraint 적용
```

### Column 삭제

```sql
ALTER TABLE members
DROP COLUMN phone;
```

먼저 application의 old version이 해당 column을 참조하지 않는지 확인한다.

## DROP과 TRUNCATE

```sql
DROP TABLE members;
```

table 구조와 data를 제거한다.

```sql
TRUNCATE TABLE logs;
```

대량 row를 빠르게 비우는 데 사용하지만 transaction, FK, identity 초기화 동작이 DBMS마다 다르다.

## DDL Transaction 차이

### PostgreSQL

많은 DDL을 transaction 안에서 rollback할 수 있다.

```sql
BEGIN;
ALTER TABLE members ADD COLUMN nickname VARCHAR(100);
ROLLBACK;
```

일부 작업은 transaction block 제약이 있으므로 명령별 확인이 필요하다.

### MySQL

많은 DDL이 implicit commit을 발생시키거나 atomic DDL 방식으로 동작한다. 일반 DML처럼 transaction rollback될 것이라고 가정하면 안 된다.

### Oracle

DDL은 일반적으로 implicit commit과 연결된다. 실행 전후 transaction 영향에 주의한다.

## INSERT

```sql
INSERT INTO members(id, email, name, status, created_at)
VALUES (1, 'kim@example.com', '김개발', 'ACTIVE', CURRENT_TIMESTAMP);
```

여러 row:

```sql
INSERT INTO members(id, email, name, status, created_at)
VALUES
    (2, 'lee@example.com', '이데이터', 'ACTIVE', CURRENT_TIMESTAMP),
    (3, 'park@example.com', '박DB', 'BLOCKED', CURRENT_TIMESTAMP);
```

Oracle version과 문법에서는 multi-row INSERT 형식 차이를 확인한다.

## SELECT

```sql
SELECT id, email, name
FROM members
WHERE status = 'ACTIVE'
ORDER BY created_at DESC;
```

SQL의 논리적 처리 순서를 이해한다.

```text
FROM·JOIN
→ WHERE
→ GROUP BY
→ HAVING
→ SELECT
→ ORDER BY
→ Pagination
```

Optimizer의 실제 물리 실행 순서는 달라질 수 있다.

## UPDATE

```sql
UPDATE members
SET status = 'BLOCKED'
WHERE id = 3;
```

`WHERE`를 빠뜨리면 모든 row가 변경된다.

안전 확인:

```sql
SELECT *
FROM members
WHERE id = 3;
```

같은 조건을 먼저 SELECT해 범위를 확인한다.

## DELETE

```sql
DELETE FROM members
WHERE id = 3;
```

부모 row를 삭제하면 FK option에 따라 자식 삭제가 거절되거나 CASCADE·SET NULL이 발생한다.

Soft Delete:

```sql
UPDATE members
SET status = 'DELETED',
    deleted_at = CURRENT_TIMESTAMP
WHERE id = 3;
```

Soft Delete를 사용하면 모든 query의 filter, UNIQUE 정책, 보존 기간, 실제 purge가 필요하다.

## CASE WHEN

조건에 따라 값을 반환한다.

```sql
SELECT
    id,
    name,
    CASE
        WHEN status = 'ACTIVE' THEN '사용 중'
        WHEN status = 'BLOCKED' THEN '차단'
        ELSE '기타'
    END AS status_name
FROM members;
```

조건부 집계:

```sql
SELECT
    COUNT(*) AS total_count,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_count
FROM members;
```

PostgreSQL에서는 `FILTER`도 사용할 수 있다.

```sql
SELECT
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count
FROM members;
```

MySQL·Oracle 이식성이 중요하면 CASE 기반 조건부 집계를 우선 검토한다.

## NULL

`NULL`은 빈 문자열이나 0이 아니라 값이 없거나 알려지지 않았음을 나타낸다.

잘못된 비교:

```sql
WHERE deleted_at = NULL
```

올바른 비교:

```sql
WHERE deleted_at IS NULL
```

Oracle에서는 SQL의 빈 문자열 `''`을 NULL처럼 취급하는 특성이 있어 MySQL·PostgreSQL migration 시 중요하다.

## COALESCE와 DBMS별 함수

표준성이 높은 방식:

```sql
SELECT COALESCE(nickname, name)
FROM members;
```

제품별 함수:

```text
MySQL IFNULL
Oracle NVL
PostgreSQL에서도 COALESCE 권장 가능
```

다른 DBMS로 이동할 가능성이 있으면 `COALESCE` 같은 표준 표현을 우선 검토한다.

## 문자열 함수 차이

```sql
-- MySQL
SELECT CONCAT(first_name, ' ', last_name);

-- PostgreSQL·Oracle
SELECT first_name || ' ' || last_name;
```

문자열 길이, substring, 날짜 변환 함수 이름과 argument도 제품별로 다를 수 있다.

## 날짜 범위 조회

Index column에 함수를 적용하기보다 범위를 사용한다.

```sql
WHERE ordered_at >= TIMESTAMP '2026-01-01 00:00:00'
  AND ordered_at <  TIMESTAMP '2027-01-01 00:00:00'
```

MySQL의 literal·cast 문법은 조정할 수 있다. 핵심은 반열린 구간 `[start, end)`을 사용해 시간 정밀도 문제를 피하는 것이다.

## Upsert

### MySQL

```sql
INSERT INTO members(email, name)
VALUES ('kim@example.com', '김개발')
ON DUPLICATE KEY UPDATE
name = VALUES(name);
```

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

## Pagination

```sql
-- MySQL·PostgreSQL
LIMIT 20 OFFSET 100;
```

```sql
-- Oracle·표준 계열
OFFSET 100 ROWS FETCH NEXT 20 ROWS ONLY;
```

큰 OFFSET은 앞 row를 읽고 버리는 비용이 증가할 수 있다. Keyset pagination을 검토한다.

## DML과 Transaction

```sql
BEGIN;

UPDATE products
SET stock = stock - 1
WHERE id = 10
  AND stock >= 1;

INSERT INTO orders(...);

COMMIT;
```

중간 실패 시 `ROLLBACK`한다. Autocommit 기본값과 application framework의 transaction 경계를 확인한다.

## Migration Check

MySQL에서 PostgreSQL·Oracle로 옮길 때:

```text
AUTO_INCREMENT 변환
VARCHAR·TEXT·CLOB 범위
BOOLEAN 표현
DATETIME·TIMESTAMP·timezone
ENUM
UNSIGNED number
Zero date
빈 문자열과 NULL
Upsert
Pagination
ALTER TABLE 문법
DDL implicit commit
```

문법 변환 후에는 row count만 보지 말고 업무 query 결과와 정렬, NULL, 날짜 경계를 검증한다.

