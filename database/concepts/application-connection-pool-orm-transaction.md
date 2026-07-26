# Application·Connection Pool·ORM·Transaction 상세

이 문서는 애플리케이션 요청 하나가 DB까지 어떻게 도달하는지, 연결과 트랜잭션을 잘못 관리하면 왜 장애가 나는지를 설명한다.

```text
사용자 요청
→ Application Thread·Coroutine
→ Connection Pool에서 Connection 대여
→ SQL 전송
→ DB Session에서 Parse·Execute·Fetch
→ Commit 또는 Rollback
→ Connection을 Pool에 반환
```

## 1. Connection과 Session

애플리케이션은 DB 파일을 직접 읽지 않는다. 보통 TCP 연결을 만들고 인증한 뒤 DBMS와 protocol로 통신한다. 이 논리적 연결을 connection이라 부르며, DBMS 쪽에서는 session 또는 backend process/thread와 연결된다.

연결마다 다음과 같은 상태가 생길 수 있다.

- 인증된 사용자와 권한
- 현재 database·schema
- session timezone과 locale
- transaction 상태와 isolation level
- 임시 table
- session variable
- 준비된 statement
- 열린 cursor

따라서 connection은 단순한 전선이 아니다. 이전 사용자의 session 상태가 남은 connection을 pool에서 다시 빌릴 수 있으므로 반환할 때 transaction과 session 상태를 정리해야 한다.

## 2. 새 Connection이 비싼 이유

새 연결에는 TCP 연결, TLS handshake, 인증, DB session 초기화 등이 필요하다. 요청마다 연결하고 끊으면 latency와 CPU 사용량이 증가하고 짧은 순간에도 DB connection 수가 급증한다.

```text
잘못된 방식: 요청마다 connect → query → disconnect
일반적인 방식: 시작 시 pool 준비 → 대여 → query → 반환
```

## 3. Connection Pool

Connection Pool은 미리 만들었거나 재사용 가능한 연결 집합이다. 요청은 connection을 소유하는 것이 아니라 잠시 빌린다.

### 기본 용어

| 용어 | 의미 |
|---|---|
| minimum/idle size | 유휴 상태로 유지할 최소 연결 수 |
| maximum pool size | 해당 application instance가 동시에 보유할 최대 연결 수 |
| acquire timeout | pool에서 connection을 기다릴 최대 시간 |
| idle timeout | 오래 사용하지 않은 connection을 정리하는 기준 |
| max lifetime | connection을 재생성하기 전 최대 수명 |
| validation | 빌리기 전 연결이 살아 있는지 검사 |

### Pool을 크게 하면 왜 위험한가

DB connection은 memory와 scheduler 자원을 사용한다. application instance가 20개이고 각 pool max가 50이면 이론상 1,000개 연결이 DB에 몰릴 수 있다.

```text
전체 잠재 연결 수
= instance 수 × instance당 pool max
+ 관리자·batch·monitoring·migration 연결
```

연결 수가 많다고 처리량이 계속 증가하지 않는다. DB CPU core와 disk가 감당할 수 있는 동시 query를 넘으면 context switching, lock 경쟁, cache 오염이 증가해 오히려 느려진다.

Pool 크기는 다음을 함께 측정해 정한다.

- DB의 connection 한도와 운영 예약분
- application instance 수와 autoscaling 최대치
- query latency와 transaction 길이
- 동시에 DB를 사용하는 요청 비율
- DB CPU·I/O 포화 지점
- primary, replica, batch용 pool 분리 여부

### Pool 대기와 DB 지연을 구분한다

요청이 느릴 때 실제 SQL 실행 전 pool에서 기다렸을 수 있다.

```text
요청 2초
├─ connection 대기 1.7초
└─ SQL 실행 0.3초
```

따라서 acquire time, active/idle/pending connection, query time을 따로 관찰한다.

## 4. Timeout 종류

| Timeout | 막으려는 상황 | 발생 위치 |
|---|---|---|
| connect timeout | DB에 연결 자체가 되지 않음 | driver/network |
| acquire timeout | pool에 반환되는 connection이 없음 | application pool |
| query/statement timeout | SQL 실행이 너무 오래 걸림 | driver 또는 DBMS |
| lock timeout | 필요한 lock을 오래 기다림 | DBMS |
| transaction timeout | 업무 transaction 전체가 너무 김 | framework/application |
| socket/read timeout | 응답 packet이 오지 않음 | driver/network |
| idle-in-transaction timeout | transaction을 연 채 아무 일도 하지 않음 | 지원 DBMS |

이들은 서로 대체하지 않는다. application 요청 timeout이 3초인데 DB query는 30초 동안 계속 실행되도록 두면 사용자는 이미 떠났어도 DB 자원은 계속 소비될 수 있다. cancellation이 DB까지 전달되는지 검증한다.

## 5. Connection Leak

Connection을 빌린 뒤 반환하지 않는 상태다. 시간이 지나면 pool의 active connection이 max에 붙고 새 요청은 acquire timeout으로 실패한다.

대표 원인:

- 예외 경로에서 close를 호출하지 않음
- result set·statement만 닫고 connection을 반환하지 않음
- 비동기 작업에 connection을 넘기고 수명 관리 실패
- 외부 API 호출 중 transaction과 connection을 계속 점유
- streaming result를 끝까지 소비하거나 닫지 않음

언어의 `try-with-resources`, `using`, context manager처럼 예외에도 자동 정리되는 구조를 사용한다. Pool에서 반환된다는 의미의 `close()`는 물리 연결 종료가 아니라 pool 반환일 수 있다.

Leak 의심 지표:

- active=max가 지속
- idle=0, pending 증가
- DB에는 긴 query가 없는데 application은 connection 부족
- 요청 완료 후에도 session이 transaction 상태

## 6. Prepared Statement와 Bind Parameter

값을 SQL 문자열에 이어 붙이지 않고 placeholder로 전달한다.

```sql
SELECT member_id, name
FROM members
WHERE email = ?;
```

장점:

- 값과 SQL 구조를 분리해 SQL injection 방지
- 반복 parse 비용 감소 가능
- type 전달이 명확해질 수 있음

단, table명·column명·정렬 방향 같은 identifier는 일반 bind parameter로 바꿀 수 없다. 허용 목록에서 선택한다.

Prepared Statement가 항상 같은 최적 계획을 보장하지는 않는다. 값마다 선택도가 크게 다르면 PostgreSQL generic/custom plan, SQL Server parameter sniffing, Oracle bind peeking·adaptive cursor sharing 등 제품별 plan 선택 문제를 확인한다.

## 7. ORM이 하는 일과 하지 않는 일

ORM은 object와 row 사이의 mapping, SQL 생성, 변경 감지, 관계 로딩을 돕는다. 그러나 다음을 자동으로 해결하지는 않는다.

- 올바른 table·index 설계
- query 수와 result 크기
- transaction 경계
- lock과 deadlock
- DBMS별 type·function 차이
- 실행 계획 검증

### N+1 문제

회원 100명을 한 번 조회한 뒤 각 회원의 주문을 따로 조회하면 총 101번 query가 발생한다.

```text
SELECT members ...            -- 1회
SELECT orders WHERE member=1  -- N회 시작
SELECT orders WHERE member=2
...
```

해결 후보:

- 필요한 관계를 JOIN/fetch join으로 가져오기
- `IN (...)` batch loading
- projection으로 필요한 column만 조회
- API 요구에 맞춘 별도 query

무조건 JOIN 하나로 합치는 것도 답은 아니다. 1:N:N 관계를 한꺼번에 JOIN하면 row가 곱해지고 network 전송과 ORM 중복 제거 비용이 커질 수 있다.

### Lazy와 Eager Loading

- Lazy: 실제 접근할 때 관계 조회. 불필요한 로딩을 줄이지만 N+1과 transaction 종료 후 접근 오류 가능
- Eager: 처음부터 관계 조회. 사용은 편하지만 과도한 JOIN과 대량 로딩 가능

기본 전략 이름보다 API별 실제 SQL 횟수와 row 수를 측정한다.

### ORM 변경 감지와 Bulk SQL

ORM이 entity 10만 개를 읽어 하나씩 변경하면 memory, 변경 감지, SQL 왕복 비용이 크다. 하나의 집합 기반 `UPDATE`가 적합한 업무인지 검토한다. Bulk SQL 후 ORM의 1차 cache가 이전 값을 들고 있을 수 있으므로 clear/refresh 전략이 필요하다.

## 8. Transaction 경계

Transaction은 여러 SQL을 하나의 원자적 업무 단위로 묶는다.

```text
BEGIN
→ 재고 확인·차감
→ 주문 생성
→ 결제 상태 기록
COMMIT
```

### 너무 짧으면

서로 함께 성공해야 할 변경이 분리돼 중간 상태가 남는다.

### 너무 길면

- connection을 오래 점유
- lock 유지 시간이 증가
- deadlock 가능성 증가
- PostgreSQL VACUUM, MySQL purge 등 old version 정리를 방해
- 실패 시 rollback 작업량 증가

### 외부 API를 Transaction 안에서 호출하지 않기

결제사나 다른 service 응답을 기다리는 동안 DB transaction을 열어 두면 connection과 lock을 장시간 잡는다. local DB transaction과 외부 메시지 전달을 함께 다뤄야 한다면 outbox, saga, idempotency 같은 패턴을 검토한다.

### Framework Annotation의 함정

`@Transactional` 같은 기능은 보통 proxy/interceptor를 통해 동작한다. 다음은 framework에 따라 transaction이 적용되지 않거나 예상과 다를 수 있다.

- 같은 객체 내부의 self-invocation
- private method
- 새 thread·비동기 작업으로 넘어감
- rollback 대상 예외 분류가 다름
- read-only가 물리적으로 쓰기를 완전히 차단하지 않음

annotation 존재만 보지 말고 실제 BEGIN/COMMIT, connection binding, 예외 시 rollback을 test한다.

## 9. 동시 갱신 패턴

### 원자적 조건 UPDATE

```sql
UPDATE products
SET stock = stock - 1
WHERE product_id = :id
  AND stock > 0;
```

영향받은 row가 1이면 성공, 0이면 품절로 처리한다. `SELECT` 후 application에서 계산하고 `UPDATE`하는 사이의 경쟁을 줄인다.

### Pessimistic Lock

`SELECT ... FOR UPDATE` 등으로 먼저 lock을 얻는다. 충돌이 잦고 업무 규칙이 복잡할 때 유용하지만 lock 순서, timeout, deadlock retry가 필요하다.

### Optimistic Lock

`version` column을 조건에 포함한다.

```sql
UPDATE orders
SET status = :new_status, version = version + 1
WHERE order_id = :id
  AND version = :old_version;
```

0행이면 다른 transaction이 먼저 변경한 것이므로 재조회·재시도 또는 사용자 충돌 처리를 한다.

## 10. DBMS와 Proxy 차이

| 영역 | MySQL | PostgreSQL | Oracle |
|---|---|---|---|
| session 구현 | server thread/session과 연결 | 보통 connection당 backend process | server process/session 구조 |
| 외부 pool/proxy 예 | application pool, ProxySQL, cloud proxy | application pool, PgBouncer, cloud proxy | application pool, DRCP 등 |
| transaction 주의 | autocommit, InnoDB lock/purge | aborted transaction 상태, long transaction·VACUUM | session state, cursor와 undo 관리 |

Transaction pooling proxy에서는 session affinity가 약해질 수 있다. session temporary table, session variable, prepared statement, advisory lock 등 기능이 proxy mode와 호환되는지 확인한다.

## 11. 장애 진단 순서

```text
1. 요청 latency를 pool 대기·SQL 실행·fetch로 분해
2. active/idle/pending connection 확인
3. DB current session과 transaction 상태 확인
4. 긴 query·lock wait·idle transaction 확인
5. instance 수 × pool max로 전체 연결 상한 계산
6. timeout과 cancellation 전달 확인
7. leak인지 DB 처리량 포화인지 구분
```

## 12. 최종 점검표

- connection을 모든 정상·예외 경로에서 반환하는가?
- 전체 pool 상한에 autoscaling 최대 instance 수를 반영했는가?
- 관리자와 장애 대응용 connection을 남겨 두었는가?
- pool 대기와 query 실행 시간을 따로 측정하는가?
- bind parameter와 identifier allowlist를 사용하는가?
- endpoint별 SQL 횟수와 N+1을 관찰하는가?
- transaction 안에서 network 호출이나 긴 계산을 하지 않는가?
- timeout, cancellation, retry가 중복 처리되지 않도록 멱등성을 갖췄는가?
- deadlock과 optimistic conflict를 정상적인 동시성 사건으로 재시도할 수 있는가?
