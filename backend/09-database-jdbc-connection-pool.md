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

## 설명할 때 핵심 문장

```text
DB는 백엔드가 데이터를 안전하게 저장하고 조회하는 핵심 저장소다.
JDBC는 Java에서 DB에 접근하기 위한 표준 API이고, JPA나 MyBatis도 결국 JDBC 위에서 동작한다.
Connection Pool은 DB connection을 미리 만들어 재사용해 성능을 높이지만, 고갈되면 전체 API 응답 지연으로 이어질 수 있다.
Index는 조회 성능을 높이지만 쓰기 비용과 저장 공간 비용이 있다.
```
