# 03. 인덱스, 실행 계획, SQL 튜닝

## 튜닝의 정의

SQL 튜닝은 DBMS 이름을 바꾸는 일이 아니다. 같은 업무 결과를 더 적은 자원과 안정적인 latency로 얻도록 query, index, 통계, schema, 설정을 개선하는 일이다.

```text
관찰 → 재현 → 실행 계획 확인 → 가설 → 한 가지 변경 → 재측정
```

평균 실행 시간 하나만 비교하지 않는다. 결과 row 수, buffer read, disk I/O, CPU, lock wait, temporary spill, p95/p99, 쓰기 부작용을 함께 본다.

## B-Tree 인덱스

B-Tree는 equality, range, prefix 정렬에 널리 사용된다.

```sql
CREATE INDEX idx_orders_customer_created
    ON orders(customer_id, created_at DESC);
```

다음 query와 잘 맞는다.

```sql
SELECT id, created_at, amount
FROM orders
WHERE customer_id = :customer_id
ORDER BY created_at DESC
LIMIT 20;
```

복합 인덱스는 “선택도가 높은 컬럼부터”라는 규칙만으로 정하지 않는다. 실제 equality 조건, range, 정렬, JOIN과 DBMS의 skip scan 지원을 함께 본다.

## 인덱스가 항상 빠르지 않은 이유

- table이 작으면 sequential scan이 더 저렴할 수 있다.
- 대부분의 row를 읽으면 index와 heap을 왕복하는 random I/O가 더 비쌀 수 있다.
- 통계가 틀리면 optimizer가 잘못된 plan을 선택할 수 있다.
- index가 많으면 INSERT, UPDATE, DELETE가 느려지고 storage와 cache를 사용한다.
- 값이 자주 바뀌는 컬럼의 index는 유지 비용이 크다.

## Covering, Partial, Expression Index

```sql
-- PostgreSQL
CREATE INDEX idx_members_email_cover
    ON members(email) INCLUDE (id, nickname);

CREATE INDEX idx_orders_open
    ON orders(customer_id, created_at)
    WHERE status = 'OPEN';

CREATE INDEX idx_members_lower_email
    ON members(lower(email));
```

- **Covering Index**: query에 필요한 컬럼을 index에서 제공
- **Partial Index**: 조건에 맞는 행만 index에 포함
- **Expression Index**: 함수나 식의 결과를 index

MySQL에는 PostgreSQL과 동일한 `INCLUDE`와 partial index 문법이 없다. secondary index가 PK를 포함하는 InnoDB 특성, generated column과 functional index 등을 이용해 다시 설계한다.

## 대표 scan

- **Sequential/Table Scan**: table page를 순차 탐색
- **Index Scan**: index에서 row 위치를 찾은 뒤 table 접근
- **Index Only Scan**: 필요한 값과 가시성 조건을 index만으로 해결
- **Bitmap Index/Heap Scan**: 여러 row 위치를 bitmap으로 모아 heap page 단위 접근

용어는 DBMS마다 다르다. MySQL `EXPLAIN`의 `ALL`, `range`, `ref`를 PostgreSQL node 이름과 일대일 대응시키지 않는다.

## JOIN 알고리즘

### Nested Loop

바깥쪽 각 row마다 안쪽 입력을 찾는다. 바깥 결과가 작고 안쪽 lookup index가 좋으면 강력하다. 예상보다 바깥 row가 많으면 반복이 폭증한다.

### Hash Join

한 입력으로 hash table을 만들고 다른 입력을 probe한다. 큰 equality JOIN에 유리할 수 있다. 메모리를 넘으면 disk batch가 생길 수 있다.

### Merge Join

정렬된 두 입력을 순서대로 병합한다. 이미 정렬되어 있거나 넓은 범위를 처리할 때 유리할 수 있다. 정렬 비용을 포함해 판단한다.

## 실행 계획에서 볼 것

1. 가장 많은 시간을 쓴 node
2. 예상 rows와 실제 rows의 차이
3. `loops`를 곱한 실제 작업량
4. filter에서 버린 row 수
5. sort/hash의 memory 사용과 disk spill
6. scan 방식과 읽은 page 수
7. JOIN 순서와 algorithm
8. planning time과 execution time
9. lock 또는 I/O 대기

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

`ANALYZE`는 실제 query를 실행한다. 운영의 쓰기 query나 매우 무거운 query에는 그대로 사용하면 안 된다.

## 느린 query 찾기

### PostgreSQL

- `pg_stat_statements`: 정규화된 query별 호출 수와 누적 시간
- `log_min_duration_statement`: 기준보다 느린 statement 기록
- `auto_explain`: 특정 query의 plan 자동 기록

### MySQL

- slow query log
- Performance Schema
- `sys` schema
- `EXPLAIN ANALYZE`

로그를 켤 때도 저장 공간, 개인 정보, parameter 노출, logging overhead를 검토한다.

## 흔한 anti-pattern

### 인덱스 컬럼을 가공

```sql
-- 일반 order_date 인덱스를 쓰기 어려울 수 있음
WHERE EXTRACT(YEAR FROM order_date) = 2026

-- 범위로 표현
WHERE order_date >= DATE '2026-01-01'
  AND order_date <  DATE '2027-01-01'
```

### 불필요한 SELECT *

network 전송, row materialization, covering 가능성, schema 변경 영향이 커진다. 필요한 컬럼만 조회한다.

### 선행 wildcard

```sql
WHERE title LIKE '%database%'
```

일반 B-Tree로 prefix를 활용하기 어렵다. PostgreSQL `pg_trgm` GIN/GiST, DB별 full-text search, Elasticsearch 등을 workload에 따라 검토한다.

### 큰 OFFSET

```sql
LIMIT 20 OFFSET 100000
```

앞의 행을 읽고 버리는 비용이 커질 수 있다. 안정적인 정렬 키로 keyset pagination을 검토한다.

### OR와 암시적 형 변환

여러 조건의 selectivity 추정이 어렵고 index 사용이 불안정할 수 있다. 문자열 컬럼과 숫자 parameter 비교처럼 암시적 cast가 생기면 컬럼 쪽 변환 여부를 plan에서 확인한다.

## 튜닝 순서

```text
1. 느린 API와 정확한 SQL, bind 값 확보
2. 호출 횟수 확인: N+1인지 먼저 판단
3. 운영과 비슷한 데이터 양·분포에서 재현
4. 실행 계획과 wait event 확인
5. query rewrite 또는 index 후보 작성
6. 변경 전후 동일 조건 측정
7. 쓰기 성능, storage, 다른 query 회귀 확인
8. 배포 후 실제 p95/p99와 error 관찰
```

## 튜닝과 DB 교체의 경계

다음은 먼저 현재 DB에서 고친다.

- 잘못된 index 또는 오래된 statistics
- N+1, 불필요한 대량 조회
- lock을 오래 잡는 transaction
- 과도한 connection과 pool 설정
- partition pruning을 방해하는 query

다음은 다른 DB 계열을 검토할 근거가 될 수 있다.

- 문서·검색·그래프·시계열 같은 주 접근 방식이 관계형과 크게 다름
- 단일 primary의 쓰기 한계를 넘어선 수평 확장이 필수
- columnar 대량 분석이 핵심 workload
- 전 세계 multi-region write와 합의가 필수

그래도 benchmark와 운영 난이도, 일관성 요구, migration 비용으로 검증해야 한다.

