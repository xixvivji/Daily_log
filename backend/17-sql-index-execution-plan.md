# 17. SQL과 Index 실행 계획 심화

## 왜 필요한가?

JPA를 사용해도 DB가 실행하는 것은 SQL이다. 느린 API를 개선하려면 Repository method 이름이 아니라 실제 SQL, 실행 계획, 읽은 row 수를 봐야 한다.

```text
API가 느림
→ 어떤 SQL이 실행됐는가?
→ 몇 번 실행됐는가?
→ 몇 row를 읽고 몇 row를 반환했는가?
→ index와 join 순서는 적절한가?
→ lock 대기가 있는가?
```

## SQL 실행 과정

```text
SQL parsing
→ 문법과 object 확인
→ query rewrite
→ planner/optimizer가 여러 실행 방법의 cost 비교
→ execution plan 선택
→ executor가 scan, join, sort, aggregate 수행
```

Optimizer의 cost는 실제 시간 그 자체가 아니라 통계 정보를 이용한 상대적 추정치다. 통계가 오래됐거나 column 값 분포가 치우치면 예상 row와 실제 row가 크게 달라질 수 있다.

## EXPLAIN과 EXPLAIN ANALYZE

```sql
EXPLAIN
SELECT * FROM orders
WHERE member_id = 10
ORDER BY created_at DESC;
```

`EXPLAIN`은 예상 plan을 보여준다. `EXPLAIN ANALYZE`는 query를 실제 실행하고 실제 시간과 row를 보여주므로 쓰기 query나 운영 환경에서는 부수 효과와 부하를 조심한다.

주요 확인 항목:

```text
Scan 방식
예상 rows와 실제 rows 차이
각 node 실행 시간
loop 횟수
sort와 temporary storage
filter로 버려진 row 수
join 방식과 순서
```

## Scan 방식

```text
Sequential Scan
→ table 전체 또는 많은 page를 순차적으로 읽음

Index Scan
→ index에서 row 위치를 찾고 table 접근

Index Only Scan
→ 필요한 값이 index에 있고 가시성 조건을 만족하면 table 접근 감소

Bitmap Index/Heap Scan
→ 여러 index 결과나 많은 row 위치를 bitmap으로 모아 table page 접근
```

Sequential Scan이 항상 나쁜 것은 아니다. table이 작거나 대부분의 row를 읽는 query라면 index 왕복보다 순차 읽기가 더 효율적일 수 있다.

## B-Tree Index

일반적으로 equality, range, sorting에 가장 많이 사용한다.

```sql
CREATE INDEX idx_orders_member_created
ON orders(member_id, created_at DESC);
```

유리한 query:

```sql
SELECT * FROM orders
WHERE member_id = :memberId
ORDER BY created_at DESC
LIMIT 20;
```

## 복합 Index 순서

복합 B-Tree는 앞 column부터 정렬된다.

```text
(member_id, created_at)
→ member_id별로 묶임
→ 같은 member_id 안에서 created_at 순서
```

설계 기준:

```text
equality 조건을 앞쪽에 배치
range와 정렬 조건을 그다음 검토
선택도만으로 순서를 결정하지 않음
실제 WHERE, JOIN, ORDER BY 조합으로 판단
```

`(member_id, status)` index가 있다고 `status`만 조회하는 모든 query에 효율적인 것은 아니다. 사용하는 DB의 skip scan과 planner 동작은 실행 계획으로 확인한다.

## Covering Index

조회에 필요한 column을 index만으로 제공하면 table 접근을 줄일 수 있다.

```sql
CREATE INDEX idx_members_email_cover
ON members(email) INCLUDE (id, nickname, status);
```

읽기는 빨라질 수 있지만 index 크기와 쓰기 비용이 증가한다. 응답 DTO의 모든 field를 무작정 index에 넣지 않는다.

## Unique, Partial, Expression Index

```sql
CREATE UNIQUE INDEX uk_members_email ON members(email);
```

동시 회원가입의 최종 중복 방어는 DB unique constraint가 담당한다.

PostgreSQL 예시:

```sql
CREATE INDEX idx_active_members_email
ON members(email)
WHERE status = 'ACTIVE';

CREATE INDEX idx_members_lower_email
ON members(lower(email));
```

Partial index는 조건에 해당하는 row만 저장하고 expression index는 계산 결과를 index화한다. Query 조건이 index 정의와 맞아야 한다.

## Index의 비용

```text
INSERT, UPDATE, DELETE 시 index도 변경
disk와 memory 사용 증가
cache 효율 저하
index 생성 중 lock과 I/O 발생 가능
불필요한 index가 optimizer 선택을 복잡하게 함
```

읽기 하나를 빠르게 만들기 위해 전체 쓰기 처리량을 희생할 수 있으므로 query 빈도와 변경 빈도를 함께 본다.

## Join 알고리즘

```text
Nested Loop
→ 바깥 row마다 안쪽을 조회
→ 바깥 결과가 작고 안쪽 index가 좋으면 효율적

Hash Join
→ 한쪽으로 hash table 생성 후 다른 쪽과 matching
→ 큰 equality join에 유리할 수 있음

Merge Join
→ 정렬된 두 입력을 순서대로 병합
→ 정렬 상태나 range 성격에 유리할 수 있음
```

Join 방식 이름보다 각 입력 row 수와 반복 횟수를 본다. 예상 1 row가 실제 10만 row면 잘못된 join 순서가 선택될 수 있다.

## N+1과 Fetch Join

```text
주문 목록 1회 조회
→ 각 주문의 회원을 N회 조회
```

해결 후보:

```text
fetch join
EntityGraph
batch fetch
DTO projection
query 자체를 use case에 맞게 재설계
```

ToMany fetch join과 pagination을 함께 사용하면 row가 중복되고 memory pagination이 발생할 수 있다. ID를 먼저 page 조회한 뒤 필요한 연관 데이터를 별도 query로 가져오는 방식도 고려한다.

## Pagination

Offset 방식:

```sql
SELECT * FROM orders
ORDER BY id DESC
LIMIT 20 OFFSET 100000;
```

뒤 page로 갈수록 많은 row를 건너뛸 수 있다.

Keyset 방식:

```sql
SELECT * FROM orders
WHERE id < :lastId
ORDER BY id DESC
LIMIT 20;
```

큰 목록에는 효율적이지만 임의 page 이동과 복잡한 정렬 조건 구현이 어려울 수 있다. 정렬 값이 중복되면 `(created_at, id)`처럼 안정적인 cursor를 사용한다.

## 느린 Query 분석 순서

```text
1. Trace에서 느린 API와 SQL 확인
2. 동일 SQL 호출 횟수 확인
3. parameter를 포함해 실행 계획 확인
4. 예상 rows와 실제 rows 비교
5. scan, join, sort, lock wait 확인
6. query 또는 index 변경 후보 작성
7. production과 유사한 데이터 분포로 측정
8. 쓰기 비용과 다른 query 회귀 확인
```

## 흔한 실수

```text
모든 column에 index 생성
개발 DB의 작은 데이터로만 판단
SELECT *로 불필요한 column 조회
함수 적용 때문에 일반 index를 사용하지 못함
LIKE '%keyword%'가 B-Tree를 잘 탈 것으로 기대
N+1을 connection pool 크기로 숨김
실행 계획 없이 index가 사용될 것이라고 추측
```

## 공식 참고 자료

- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)

## 설명할 때 핵심 문장

```text
Index는 조회 범위를 줄이지만 쓰기와 저장 공간 비용을 만든다.
복합 index는 실제 WHERE, JOIN, ORDER BY 조합과 column 순서로 설계한다.
성능 문제는 SQL 문자열만 보지 말고 실행 계획의 scan, row 수, loop, join, sort를 확인해야 한다.
```
