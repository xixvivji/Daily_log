# WAL, Undo, Redo, Checkpoint 상세

[← 핵심 용어 문서로 돌아가기](../01-database-course-map-and-glossary.md)

## 한 문장으로 구분

```text
WAL
→ data page보다 복구 가능한 log를 먼저 안전하게 기록하는 원칙

Redo
→ commit된 변경을 장애 후 다시 적용하는 복구 방향

Undo
→ 미완료 변경을 취소하거나 과거 version을 보여주는 복구 방향

Checkpoint
→ 장애 복구를 어디부터 시작할지 범위를 줄이는 기준점
```

WAL과 redo는 완전히 같은 단어가 아니다. WAL은 **기록 순서에 관한 원칙**이고, redo는 **log를 이용해 변경을 재적용하는 동작 또는 그 목적의 log**다.

## 왜 data file에 바로 쓰지 않는가

DB가 row 하나를 변경하더라도 실제 storage에서는 보통 page 단위로 읽고 쓴다. 매 transaction마다 여러 data page를 즉시 disk에 쓰면 random I/O가 많아지고 commit이 느려진다.

그래서 일반적으로 다음 방식을 사용한다.

```text
1. memory의 data page를 변경한다.
2. 변경 내용을 설명하는 log를 먼저 기록한다.
3. commit에 필요한 log를 durable storage로 flush한다.
4. 변경된 data page는 나중에 background writer나 checkpoint가 기록한다.
```

log는 순차적으로 append하기 쉬워 흩어진 data page를 매번 쓰는 것보다 효율적일 수 있다.

## WAL의 핵심 규칙

WAL에는 다음 순서가 중요하다.

```text
해당 변경을 설명하는 log가 durable해지기 전에는
변경된 data page를 disk에 먼저 기록하면 안 된다.
```

그렇지 않으면 data file에는 변경이 있는데 이를 commit된 변경인지 판단하거나 되돌릴 log가 없는 상태가 생길 수 있다.

commit 응답 시점도 중요하다.

```text
COMMIT 성공 응답
→ 복구에 필요한 log가 DBMS가 약속한 durable 위치까지 기록됨
```

단, `fsync`, synchronous commit, storage cache와 cloud 설정을 완화하면 성능과 durability의 trade-off가 바뀔 수 있다.

## 장애 복구 예시

계좌 이체 transaction을 생각해 보자.

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 10000
WHERE id = 'A';

UPDATE accounts
SET balance = balance + 10000
WHERE id = 'B';

COMMIT;
```

### Commit log 기록 후 data page 기록 전 장애

```text
log: commit까지 안전하게 기록됨
data page: 일부 또는 전부 반영되지 않음
```

재시작할 때 DBMS가 log를 읽고 누락된 변경을 **redo**한다. 사용자가 성공 응답을 받은 transaction 결과를 복구하기 위한 것이다.

### Commit 전 장애

```text
log: 변경 기록은 일부 존재
transaction: commit되지 않음
```

DBMS는 이 transaction을 완료된 결과로 노출하면 안 된다. 제품 구현에 따라 undo로 물리적 변경을 되돌리거나, MVCC 가시성 규칙으로 미완료 version을 보이지 않게 하고 나중에 정리한다.

## Redo

Redo는 이미 commit된 변경이 data file에 완전히 반영되지 않았을 때 변경을 다시 적용한다.

주요 목적:

- process 또는 OS crash 후 recovery
- data page write보다 log flush를 먼저 수행해 commit latency 감소
- replica나 recovery 과정에서 변경 재현

Redo log가 “SQL 문장을 그대로 저장한다”고 이해하면 안 된다. 많은 DBMS는 page나 record 변경을 복구할 수 있는 내부 형식으로 기록한다. binary log처럼 논리적·statement·row 수준의 별도 log도 존재할 수 있다.

## Undo

Undo는 변경 이전 상태를 찾는 데 사용한다.

주요 목적:

- `ROLLBACK`
- commit되지 않은 transaction의 변경 취소
- MVCC consistent read를 위한 과거 version 제공

다만 모든 DBMS가 별도의 undo log를 같은 방식으로 사용하는 것은 아니다.

```text
MySQL InnoDB
→ undo log로 rollback과 consistent read 지원

Oracle
→ undo segment로 rollback과 read consistency 지원

PostgreSQL
→ row의 과거 version을 table 안에 새 tuple로 보존
→ 별도의 전통적 undo log로 MVCC를 구현하지 않음
```

PostgreSQL에서는 불필요해진 old tuple을 `VACUUM`이 정리한다.

## Checkpoint

Checkpoint는 “이 순간 모든 data가 완전히 반영되었다”라는 단순한 backup 지점과 같지 않다. DBMS가 dirty page를 정리하고, 장애 복구가 참고할 시작 정보를 기록해 recovery 범위를 제한하는 과정이다.

### Checkpoint가 너무 드물면

- 장애 복구 시 읽고 재적용할 log가 많아짐
- transaction log 보관량 증가 가능
- 정상 실행 중 checkpoint I/O 부담은 상대적으로 덜 자주 발생

### Checkpoint가 너무 잦으면

- dirty page write가 자주 발생
- storage I/O spike 가능
- 정상 workload latency에 영향
- 장애 복구 범위는 짧아질 수 있음

그래서 checkpoint 주기와 write 분산 설정은 정상 성능, 복구 시간, log 사용량을 함께 보고 조정한다.

## PostgreSQL

### 기본 구조

```text
변경
→ shared buffers의 page 변경
→ WAL record 생성
→ commit 시 필요한 WAL flush
→ data page는 background writer/checkpoint 등이 나중에 기록
```

PostgreSQL의 주요 개념:

- **WAL record**: 복구에 필요한 변경 정보
- **LSN(Log Sequence Number)**: WAL 위치
- **WAL segment**: WAL을 나눠 저장하는 file
- **WAL writer**: WAL buffer를 disk에 기록
- **Checkpointer**: checkpoint와 dirty buffer write 조정
- **Full Page Write**: torn page 위험에 대비해 checkpoint 후 처음 변경되는 page 전체 image 기록 가능
- **Archive/PITR**: base backup과 보관한 WAL을 이용한 시점 복구

PostgreSQL MVCC의 old version은 undo log가 아니라 table의 tuple로 존재한다. long transaction이 오래된 snapshot을 유지하면 VACUUM이 tuple을 정리하지 못해 table bloat가 커질 수 있다.

## MySQL InnoDB

InnoDB에서는 역할이 다른 log를 구분해야 한다.

### Redo Log

- InnoDB storage engine의 crash recovery
- 변경된 page를 다시 적용
- WAL 원칙에 따라 data page보다 먼저 필요한 redo 기록

### Undo Log

- rollback
- MVCC consistent read
- 아직 필요한 old version 제공

### Binary Log

- MySQL server 계층의 변경 log
- replication과 point-in-time recovery에 활용
- row, statement, mixed 형식

```text
InnoDB redo log ≠ MySQL binary log
```

둘은 목적과 계층이 다르다. commit 과정에서는 redo와 binary log의 일관성을 맞추기 위한 coordination이 필요하다.

### Doublewrite Buffer

page를 쓰다가 일부만 기록되는 torn page를 방지하기 위한 InnoDB 장치다. redo log와 목적이 겹치는 것처럼 보여도, redo 적용의 기반이 되는 page 자체가 손상되는 문제를 줄이는 역할을 한다.

## Oracle Database

Oracle에서는 다음 용어를 구분한다.

- **Redo Log Buffer**: memory에 있는 redo entry
- **Online Redo Log**: instance recovery에 사용하는 redo file
- **Archived Redo Log**: backup·media recovery·PITR 등에 사용하는 보관 redo
- **Undo Segment**: rollback과 read consistency를 위한 이전 정보
- **LGWR**: redo를 online redo log에 기록
- **DBWR**: dirty data buffer를 data file에 기록
- **CKPT**: checkpoint 관련 header와 control file 정보 갱신 조정

commit 시 LGWR의 redo 기록이 핵심이며, 모든 dirty data block이 commit 순간 data file에 기록될 필요는 없다.

## 세 DBMS 비교

| 관점 | PostgreSQL | MySQL InnoDB | Oracle |
| --- | --- | --- | --- |
| 재적용 log | WAL | redo log | redo log |
| MVCC 과거 version | table의 tuple | undo log | undo segment |
| rollback | transaction 상태와 tuple 가시성 | undo log | undo segment |
| replication용 주요 log | WAL | binary log 또는 redo 기반 제품 기능 | redo 기반 기능 |
| 오래된 version 정리 | VACUUM | purge | undo retention·재사용 관리 |
| 시점 복구 | base backup + archived WAL | backup + binary log 등 | backup + archived redo |

## 흔한 오해

### WAL이 있으면 data를 절대 잃지 않는다

아니다. flush 설정, storage 보장, filesystem, hardware, replication 구성에 따라 durability 범위가 달라진다.

### Commit 때 table file까지 전부 기록한다

일반적으로 아니다. commit에 필요한 log를 먼저 durable하게 만들고 dirty data page는 나중에 기록할 수 있다.

### WAL과 backup은 같다

아니다. log만으로 무한히 과거의 전체 DB를 복원할 수 있다고 가정하면 안 된다. base backup과 필요한 log 보관 정책이 함께 있어야 한다.

### Replication log가 있으면 backup이 필요 없다

아니다. 삭제 실수와 corruption도 replica에 전달될 수 있다.

### Checkpoint를 자주 하면 무조건 안전하다

복구 범위는 줄 수 있지만 정상 workload의 I/O가 증가한다. RPO는 checkpoint 하나가 아니라 commit log의 durability와 backup·replication 정책으로 결정한다.

## 장애 복구 흐름 요약

```text
정상 실행
변경 → WAL/redo 생성 → log flush → commit 성공
                         ↓
                dirty data page는 나중에 기록

장애 발생
마지막 checkpoint와 log 확인
→ commit된 변경 중 누락된 page를 redo
→ 미완료 transaction을 보이지 않게 하거나 undo
→ 일관된 상태로 service 재개
```

