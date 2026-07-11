# 09. Database, JDBC, Connection Pool

## DB를 알아야 하는 이유

백엔드의 핵심 책임 중 하나는 데이터를 안전하게 저장하고 조회하는 것이다.

대부분의 서비스는 데이터베이스와 연결된다.

```text
회원 정보
주문 정보
결제 기록
게시글
댓글
권한
로그
```

DB를 모르면 성능 문제, 정합성 문제, 트랜잭션 문제를 설명하기 어렵다.

## RDB

RDB는 관계형 데이터베이스다.

데이터를 table, row, column으로 저장한다.

```text
members table
id | email | nickname
```

대표 RDB:

```text
MySQL
PostgreSQL
Oracle
MariaDB
```

## SQL

SQL은 RDB와 통신하기 위한 언어다.

기본:

```sql
SELECT * FROM members WHERE id = 1;
INSERT INTO members(email, nickname) VALUES ('a@test.com', 'a');
UPDATE members SET nickname = 'b' WHERE id = 1;
DELETE FROM members WHERE id = 1;
```

백엔드 개발자는 ORM을 쓰더라도 SQL을 이해해야 한다.

JPA도 결국 SQL을 만들어 DB에 보낸다.

## Index

Index는 조회 성능을 높이기 위한 자료구조다.

예:

```sql
CREATE INDEX idx_member_email ON members(email);
```

장점:

```text
검색 속도 향상
정렬/조건 조회 최적화
unique 제약 가능
```

단점:

```text
쓰기 성능 비용
저장 공간 사용
불필요한 index는 오히려 부담
```

## JDBC

JDBC는 Java에서 DB에 접근하기 위한 표준 API다.

흐름:

```text
Connection 획득
SQL 준비
SQL 실행
ResultSet 처리
Connection 반환
```

JPA나 MyBatis를 쓰더라도 아래쪽에서는 JDBC를 사용한다.

## Connection

DB connection은 애플리케이션과 DB 사이의 연결이다.

요청마다 connection을 새로 만들면 비용이 크다.

```text
TCP 연결
인증
세션 생성
```

그래서 connection pool을 사용한다.

## Connection Pool

Connection Pool은 미리 DB connection을 만들어두고 재사용한다.

```text
요청 들어옴
→ pool에서 connection 대여
→ DB 작업
→ connection 반환
```

Spring Boot에서는 HikariCP를 기본으로 많이 사용한다.

중요한 설정:

```text
maximumPoolSize
connectionTimeout
idleTimeout
maxLifetime
```

## Connection Pool 고갈

Connection pool이 고갈되면 요청이 connection을 얻지 못하고 대기한다.

증상:

```text
응답 지연
timeout
thread pool 고갈
DB는 멀쩡한데 애플리케이션이 느림
```

원인:

```text
느린 쿼리
트랜잭션이 너무 김
connection 반환 누락
pool size 부족
DB max connection 부족
외부 API 호출을 트랜잭션 안에서 수행
```

## N+1 문제

ORM을 사용할 때 자주 나오는 문제다.

예:

```text
게시글 목록 1번 조회
각 게시글의 댓글을 N번 추가 조회
```

결과:

```text
1 + N번 SQL 실행
```

N+1은 JPA에서 특히 중요하다.

해결:

```text
fetch join
entity graph
batch size
DTO projection
```

## Key와 Constraint

```text
Primary Key
→ row를 유일하게 식별

Foreign Key
→ 다른 table의 row와 관계를 맺고 참조 무결성 보호

Unique
→ email처럼 중복되면 안 되는 값 보호

Not Null
→ 반드시 값이 있어야 하는 column 보호

Check
→ 수량이 0 이상인 것처럼 허용 범위를 제한
```

애플리케이션에서 중복 email을 먼저 조회해도 동시에 두 요청이 들어오면 둘 다 없다고 판단할 수 있다. 최종 정합성은 DB unique constraint로 보장하고, 애플리케이션은 constraint 위반을 의미 있는 `409 Conflict`로 변환한다.

## Table 관계

```text
1:1
→ 회원과 회원 상세 정보

1:N
→ 회원 한 명과 여러 주문

N:M
→ 학생과 강의
```

관계형 DB에서 N:M은 보통 연결 table로 풀어낸다.

```text
students
courses
student_courses(student_id, course_id, enrolled_at)
```

연결 table에 수강일, 상태 같은 관계 자체의 속성이 생길 수 있으므로 독립적인 개념으로 모델링하는 편이 유연하다.

## 정규화와 반정규화

정규화는 중복 데이터를 줄이고 변경 이상을 방지하도록 table을 분리하는 과정이다.

```text
회원 주소를 주문마다 참조
→ 회원 주소 변경 시 과거 주문 주소까지 바뀌면 안 될 수 있음
→ 주문 시점 배송 주소 snapshot을 별도로 저장
```

무조건 table을 많이 나누는 것이 정답은 아니다. 데이터의 의미와 변경 주기를 기준으로 경계를 잡는다. 반정규화는 조회 성능을 위해 값을 중복 저장하는 선택이며, 어느 값이 원본인지와 동기화 방법이 반드시 필요하다.

## JOIN과 집계

```sql
SELECT m.id, m.email, COUNT(o.id) AS order_count
FROM members m
LEFT JOIN orders o ON o.member_id = m.id
GROUP BY m.id, m.email;
```

```text
INNER JOIN
→ 양쪽에 일치하는 row만 반환

LEFT JOIN
→ 왼쪽 row는 유지하고 오른쪽이 없으면 null

GROUP BY
→ 같은 key의 row를 묶어 COUNT, SUM, AVG 같은 집계 수행
```

ORM을 사용해도 실제로 어떤 JOIN과 row 수가 발생하는지 SQL로 확인할 수 있어야 한다.

## 복합 Index

```sql
CREATE INDEX idx_orders_member_created
ON orders(member_id, created_at DESC);
```

복합 index는 column 순서가 중요하다. 위 index는 `member_id` 조건과 `created_at` 정렬을 함께 사용하는 query에 유리하지만 `created_at`만 조건으로 쓰는 query에는 효율적으로 사용되지 않을 수 있다.

Index 판단 기준:

```text
WHERE와 JOIN에 자주 쓰는가?
선택도가 충분한가?
ORDER BY까지 활용할 수 있는가?
쓰기 빈도와 저장 공간 비용은 감당 가능한가?
실제 실행 계획에서 사용되는가?
```

`EXPLAIN`으로 접근 방식, 예상 row 수, index 사용 여부, 정렬이나 임시 table 발생 여부를 확인한다. 느린 query는 실행 시간만 보지 말고 호출 빈도와 한 번에 읽는 row 수도 함께 본다.

## Pagination의 DB 비용

```sql
SELECT * FROM orders
ORDER BY id DESC
LIMIT 20 OFFSET 100000;
```

큰 offset은 앞의 row를 찾아 건너뛰는 비용이 커질 수 있다. 마지막 id를 cursor로 전달하면 다음처럼 범위를 바로 좁힐 수 있다.

```sql
SELECT * FROM orders
WHERE id < :lastId
ORDER BY id DESC
LIMIT 20;
```

## Connection Pool 크기

애플리케이션 instance마다 pool을 가진다.

```text
instance 5대 × maximumPoolSize 20
→ 최대 100개 application connection 가능
```

DB의 최대 connection에서 관리자 연결, batch, migration, 장애 여유분도 빼야 한다. pool을 크게 하면 대기 시간이 사라지는 것이 아니라 DB가 동시에 더 많은 query를 처리하느라 오히려 느려질 수 있다.

관찰할 metric:

```text
active connection
idle connection
pending request
connection acquire time
query latency
transaction duration
```

## Schema Migration

운영 DB schema는 Flyway나 Liquibase 같은 migration 도구로 버전 관리한다.

```text
V1__create_member.sql
V2__add_member_status.sql
V3__create_order.sql
```

JPA Entity와 schema는 같은 개념이 아니다. 개발 환경에서 `ddl-auto=create/update`를 쓸 수 있지만 운영에서는 migration으로 변경 이력을 관리하고 `validate`로 매핑 일치 여부를 확인하는 방식이 안전하다.

큰 table에 column이나 index를 추가하면 lock, 긴 실행 시간, 복제 지연이 생길 수 있으므로 이전·이후 application version과 호환되는 단계적 migration을 설계한다.

## 설명할 때 핵심 문장

```text
DB는 백엔드가 데이터를 안전하게 저장하고 조회하는 핵심 저장소다.
JDBC는 Java에서 DB에 접근하기 위한 표준 API이고, JPA나 MyBatis도 결국 JDBC 위에서 동작한다.
Connection Pool은 DB connection을 미리 만들어 재사용해 성능을 높이지만, 고갈되면 전체 API 응답 지연으로 이어질 수 있다.
Index는 조회 성능을 높이지만 쓰기 비용과 저장 공간 비용이 있다.
```
