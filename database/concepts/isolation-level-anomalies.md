# Isolation Level별 동시성 이상 현상

[← MVCC·트랜잭션·Lock 문서로 돌아가기](../04-mvcc-transaction-and-lock.md)

## 먼저 보는 표

SQL 표준에서 전통적으로 설명하는 허용 여부다.

| Isolation Level | Dirty Read | Non-repeatable Read | Phantom Read |
| --- | --- | --- | --- |
| Read Uncommitted | 허용 가능 | 허용 가능 | 허용 가능 |
| Read Committed | 방지 | 허용 가능 | 허용 가능 |
| Repeatable Read | 방지 | 방지 | 허용 가능 |
| Serializable | 방지 | 방지 | 방지 |

여기서 “허용 가능”은 반드시 발생한다는 뜻이 아니다. 해당 isolation level의 표준 최소 보장만으로는 발생을 금지하지 않는다는 뜻이다.

실제 DBMS는 표준보다 더 강하게 막을 수 있다. 예를 들어 MySQL InnoDB의 Repeatable Read와 PostgreSQL의 Repeatable Read는 전통적인 표보다 phantom을 더 강하게 억제하지만 구현과 write 충돌 결과가 서로 다르다.

## Dirty Read

다른 transaction이 아직 commit하지 않은 값을 읽는 현상이다.

```text
초기 balance = 100

T1: UPDATE account SET balance = 0;
T2: balance를 조회 → 0
T1: ROLLBACK;

T2가 읽은 0은 실제로 확정된 적이 없는 값
```

Read Committed 이상에서는 일반적으로 방지한다.

### 왜 위험한가

- rollback될 값을 기준으로 결제나 알림 수행
- 존재하지 않는 중간 상태가 외부로 전파
- 다시 조회하면 결과의 근거가 사라짐

## Non-repeatable Read

한 transaction에서 같은 row를 두 번 조회했는데 다른 transaction의 commit 때문에 값이 달라지는 현상이다.

```text
초기 balance = 100

T1: SELECT balance → 100
T2: UPDATE balance = 50; COMMIT;
T1: SELECT balance → 50
```

Read Committed에서는 statement마다 새로운 snapshot을 볼 수 있으므로 발생할 수 있다. Repeatable Read 이상에서는 같은 transaction snapshot이나 lock을 이용해 방지한다.

## Phantom Read

같은 조건으로 다시 조회했는데 조건을 만족하는 row가 추가되거나 사라져 결과 집합이 달라지는 현상이다.

```text
T1: SELECT COUNT(*) FROM orders WHERE amount >= 100;
    → 5

T2: INSERT INTO orders(amount) VALUES (200);
    COMMIT;

T1: 같은 SELECT 실행
    → 6
```

Non-repeatable Read가 기존 row 값의 변화라면, Phantom Read는 조건 범위에 들어오는 row 집합의 변화에 초점이 있다.

## Lost Update

두 transaction이 같은 값을 읽고 각각 계산한 뒤, 나중에 저장한 값이 먼저 저장한 값을 덮어쓰는 현상이다.

```text
초기 stock = 10

T1: stock 10 읽음
T2: stock 10 읽음
T1: stock 9 저장
T2: stock 9 저장

두 번 판매했지만 결과는 9
```

전통적인 세 가지 현상 표에 없다고 중요하지 않은 것이 아니다.

대응 방법:

- `UPDATE stock = stock - 1` 같은 원자적 update
- version column을 이용한 optimistic locking
- `SELECT ... FOR UPDATE`
- DBMS가 제공하는 충돌 감지와 transaction retry

## Write Skew

두 transaction이 같은 조건을 읽지만 서로 다른 row를 수정하여 전체 업무 constraint가 깨지는 현상이다.

```text
조건: 당직 의사는 최소 1명이어야 함

현재 A와 B 모두 당직

T1: B가 당직인지 확인 → A를 당직 해제
T2: A가 당직인지 확인 → B를 당직 해제

각자 다른 row를 수정했으므로 직접 write conflict가 없을 수 있음
결과적으로 당직 의사 0명
```

Snapshot Isolation이 dirty/non-repeatable read를 막더라도 write skew가 가능할 수 있다. Serializable, explicit lock, constraint를 표현할 별도 row, advisory lock 등의 설계를 검토한다.

## Read Uncommitted

표준상 가장 약한 수준이다.

- Dirty Read 허용 가능
- Non-repeatable Read 허용 가능
- Phantom Read 허용 가능

그러나 MVCC DBMS가 실제 dirty read를 제공하지 않을 수도 있다. PostgreSQL은 `READ UNCOMMITTED`를 요청해도 `READ COMMITTED`처럼 처리한다.

## Read Committed

각 statement가 시작할 때까지 commit된 data를 읽는 방식이 일반적이다.

- Dirty Read 방지
- Non-repeatable Read 가능
- Phantom Read 가능

같은 transaction 안에서도 첫 번째 SELECT와 두 번째 SELECT가 서로 다른 committed snapshot을 볼 수 있다.

```sql
BEGIN ISOLATION LEVEL READ COMMITTED;

SELECT ...;
SELECT ...;

COMMIT;
```

PostgreSQL과 Oracle의 일반적인 기본 isolation level이다. 하지만 둘의 MVCC, undo, lock, statement 재평가 동작이 완전히 같지는 않다.

## Repeatable Read

transaction 동안 일관된 snapshot을 유지하거나 lock을 강화해 반복 읽기를 보호한다.

- Dirty Read 방지
- Non-repeatable Read 방지
- 표준 정의에서는 Phantom Read 허용 가능
- 실제 phantom 동작은 DBMS 구현에 따라 다름

### PostgreSQL

PostgreSQL Repeatable Read는 transaction-level snapshot을 사용하며 표준 최소 보장보다 강하다.

- 같은 snapshot을 계속 읽음
- 일반적인 phantom read를 보지 않음
- concurrent update 상황에서 serialization failure가 발생할 수 있음
- write skew 같은 serialization anomaly는 여전히 가능할 수 있음

### MySQL InnoDB

MySQL InnoDB의 일반적인 기본 수준이다.

- consistent non-locking read는 같은 snapshot을 사용
- locking read와 write에는 next-key lock과 gap lock이 사용될 수 있음
- range 안의 insert를 막아 phantom을 억제할 수 있음
- query 형태, index, locking read 여부에 따라 lock 범위가 달라짐

“MySQL Repeatable Read는 phantom을 무조건 허용한다” 또는 “무조건 완벽하게 막는다”라고 단정하지 않고 consistent read와 locking read를 구분한다.

## Serializable

동시에 실행된 transaction 결과가 어떤 직렬 실행 순서와 동등하도록 보장하는 수준이다.

- Dirty Read 방지
- Non-repeatable Read 방지
- Phantom Read 방지
- serialization anomaly 방지 목표

Serializable은 모든 transaction을 실제로 한 개씩 차례로 실행한다는 뜻이 아니다. DBMS는 MVCC, predicate lock, range lock, conflict detection 등으로 concurrency를 유지하면서 직렬화 가능성을 보장하려 한다.

보장할 수 없는 충돌이 발생하면 transaction을 기다리게 하거나 중단할 수 있다. application에는 retry가 필요하다.

## DBMS별 핵심 차이

| DBMS | 일반적 기본값 | 주요 구현 특성 |
| --- | --- | --- |
| PostgreSQL | Read Committed | MVCC, Repeatable Read는 transaction snapshot, Serializable은 SSI |
| MySQL InnoDB | Repeatable Read | MVCC consistent read, next-key·gap lock |
| Oracle | Read Committed | undo 기반 read consistency, Read Committed·Serializable·Read Only 중심 |
| SQL Server | Read Committed | 기본은 lock 기반이며 RCSI·Snapshot을 별도로 설정 가능 |

제품과 version, cloud 설정에 따라 기본값과 기능이 달라질 수 있으므로 실제 환경을 조회한다.

## PostgreSQL SSI

PostgreSQL의 Serializable은 SSI(Serializable Snapshot Isolation)를 사용한다.

```text
transaction이 snapshot을 읽으며 동시 실행
→ read/write dependency 추적
→ 직렬 실행으로 설명할 수 없는 위험한 구조 감지
→ transaction 하나를 serialization failure로 중단
```

따라서 Serializable에서 오류가 발생하는 것은 DB가 고장 난 것이 아니라 보장을 지키기 위한 정상 동작일 수 있다.

```text
SQLSTATE 40001
→ transaction 전체를 제한된 횟수로 retry
```

## Isolation을 높이면 생기는 비용

- lock wait 또는 conflict abort 증가
- deadlock 가능성 증가
- transaction retry 필요
- throughput 감소 가능
- long transaction의 version 보존 비용 증가

가장 높은 수준을 무조건 선택하기보다 업무 invariant를 먼저 정의한다.

```text
단순 목록 조회
→ Read Committed로 충분할 수 있음

재고·잔액 변경
→ 원자적 update, row lock, optimistic lock 검토

여러 row에 걸친 강한 업무 조건
→ Serializable 또는 명시적 동시성 설계 검토
```

## 직접 재현할 때 주의

동시성 현상은 한 query 창에서 순서대로 실행하면 재현할 수 없다. 두 connection을 열고 transaction을 겹쳐야 한다.

```text
Session A                    Session B
BEGIN;                       BEGIN;
SELECT ...;
                             UPDATE ...;
                             COMMIT;
SELECT ...;
COMMIT;
```

다음을 함께 기록한다.

- DBMS와 version
- storage engine
- isolation level
- autocommit 여부
- 사용한 index
- 일반 SELECT인지 locking read인지
- 두 session의 정확한 실행 순서

## 최종 정리

```text
Read Uncommitted
→ commit되지 않은 값까지 허용할 수 있음

Read Committed
→ statement 단위로 committed data 보장

Repeatable Read
→ transaction의 반복 읽기 안정성 강화

Serializable
→ 전체 결과가 어떤 직렬 실행과 동등하도록 보장
```

격리 수준 이름보다 실제 업무에서 막아야 하는 lost update, write skew, 중복 처리와 DBMS의 구현을 함께 확인해야 한다.

