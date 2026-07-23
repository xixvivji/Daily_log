# 04. MVCC, 트랜잭션, Lock

## 동시성 문제

- **Dirty Read**: commit되지 않은 값을 읽음
- **Non-repeatable Read**: 같은 row를 다시 읽었을 때 값이 달라짐
- **Phantom Read**: 같은 조건 query의 결과 집합이 달라짐
- **Lost Update**: 동시 수정 중 한쪽 변경이 덮어써짐
- **Write Skew**: 서로 다른 row를 수정했지만 함께 지켜야 할 조건이 깨짐

ANSI 격리 수준 표만 외우면 부족하다. 같은 이름이어도 PostgreSQL, MySQL InnoDB, Oracle, SQL Server의 snapshot과 lock 구현이 다르다.

## MVCC

MVCC는 여러 version을 이용해 reader와 writer가 서로 덜 막히게 하는 동시성 제어 방식이다.

```text
PostgreSQL
→ tuple에 xmin/xmax 같은 transaction 가시성 정보
→ 오래된 version은 VACUUM이 정리

MySQL InnoDB
→ undo log와 transaction metadata로 consistent read 구성
→ purge가 불필요한 과거 version 정리
```

“read가 write를 막지 않는다”는 일반적 장점이지 모든 작업에 lock이 없다는 뜻은 아니다. DDL lock, 명시적 locking read, FK 검사, unique 충돌 등에서는 대기가 생길 수 있다.

## Isolation Level

| 수준 | 핵심 의미 | 주의 |
| --- | --- | --- |
| Read Uncommitted | 가장 약한 격리 | 일부 DB는 사실상 Read Committed처럼 동작 |
| Read Committed | statement마다 새로운 committed snapshot 가능 | 같은 transaction에서도 재조회 결과가 달라질 수 있음 |
| Repeatable Read | transaction 동안 반복 읽기 안정성 강화 | phantom과 locking 동작은 DBMS별 차이 큼 |
| Serializable | 직렬 실행과 동등한 결과 보장 | abort/retry가 정상 동작의 일부일 수 있음 |

PostgreSQL 기본값은 Read Committed, MySQL InnoDB 기본값은 보통 Repeatable Read다. 운영 서비스나 cloud 설정에서 바뀔 수 있으므로 실제 설정을 확인한다.

→ [Isolation Level별 동시성 이상 현상 허용 여부 자세히 보기](concepts/isolation-level-anomalies.md)

## Snapshot Isolation과 Serializable

snapshot isolation은 transaction이 일관된 snapshot을 읽게 해 read/write 충돌을 줄인다. 그러나 write skew를 모두 막는 직렬화 보장과 같지는 않다.

PostgreSQL Serializable은 Serializable Snapshot Isolation을 사용해 위험한 의존 관계를 감지하고 transaction을 abort할 수 있다. 애플리케이션에는 전체 transaction retry가 필요하다.

## Lock 종류

- **Shared/Read Lock**: 여러 reader가 공유할 수 있는 lock
- **Exclusive/Write Lock**: 충돌하는 접근을 막는 lock
- **Row Lock**: 특정 row 변경 충돌 제어
- **Table Lock**: table 수준 작업 제어
- **Intent Lock**: 하위 수준 lock 의도를 상위 객체에 표시
- **Gap/Next-key Lock**: index record 사이 범위 또는 record+gap을 잠금
- **Advisory Lock**: 애플리케이션이 의미를 정해 명시적으로 사용하는 lock

“row lock이므로 정확히 한 행만 잠긴다”고 단정하면 안 된다. 접근한 index 범위, 격리 수준, 존재하지 않는 key 검색, FK와 DBMS 구현에 따라 범위가 넓어질 수 있다.

## Optimistic과 Pessimistic Locking

### Optimistic

충돌이 드물다고 보고 update 시 version을 검사한다.

```sql
UPDATE products
SET stock = :new_stock,
    version = version + 1
WHERE id = :id
  AND version = :old_version;
```

영향받은 row가 0이면 충돌로 보고 다시 읽거나 사용자에게 알린다.

### Pessimistic

먼저 lock을 잡고 작업한다.

```sql
SELECT stock
FROM products
WHERE id = :id
FOR UPDATE;
```

충돌이 잦고 작업 순서를 보장해야 할 때 유용하지만 lock wait와 deadlock 가능성이 있다. 외부 API 호출을 lock 안에서 오래 수행하지 않는다.

## 재고 차감은 원자적 조건 update도 가능

```sql
UPDATE products
SET stock = stock - :quantity
WHERE id = :id
  AND stock >= :quantity;
```

영향 row 수가 1이면 성공, 0이면 재고 부족 또는 상품 부재다. read 후 write보다 race window가 작고 별도 `SELECT FOR UPDATE` 없이 요구를 만족할 수 있다.

## Deadlock

두 transaction이 서로가 가진 lock을 기다리는 순환 상태다.

```text
T1: row A lock → row B 대기
T2: row B lock → row A 대기
```

DBMS는 보통 한 transaction을 victim으로 골라 rollback한다.

예방 원칙:

- 여러 자원을 항상 같은 순서로 접근
- transaction을 짧게 유지
- 적절한 index로 불필요하게 넓은 row를 잠그지 않기
- 사용자 입력, network 호출을 transaction 밖에서 처리
- deadlock error에 제한된 backoff retry 적용

timeout을 늘리는 것은 deadlock 해결책이 아니다.

## Long Transaction의 비용

- connection과 lock 장기 점유
- PostgreSQL VACUUM의 dead tuple 정리 지연
- MySQL undo history 증가와 purge 지연
- replication과 backup에 부담
- 장애 시 rollback 시간 증가

“query가 빠르다”와 “transaction이 짧다”는 별개의 문제다. 여러 빠른 query 사이에 애플리케이션 대기가 끼면 긴 transaction이 된다.

## 분산 트랜잭션

서로 다른 DB나 메시지 broker를 하나의 로컬 transaction으로 묶을 수 없다.

- **2PC**: coordinator가 여러 participant의 prepare와 commit을 조정
- **Saga**: local transaction과 실패 시 보상 작업의 연쇄
- **Transactional Outbox**: 업무 데이터와 발행할 event를 같은 DB transaction에 기록한 뒤 별도 relay가 전송
- **Idempotency**: 같은 요청이나 event가 반복되어도 결과가 중복되지 않게 설계

Kafka transaction만 켠다고 DB commit과 Kafka publish가 자동으로 하나의 원자적 transaction이 되는 것은 아니다. connector나 outbox, 2PC 지원 범위를 명확히 해야 한다.
