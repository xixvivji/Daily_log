# DBMS별 ACID 지원과 구현 차이

[← 핵심 용어 문서로 돌아가기](../01-database-course-map-and-glossary.md)

## 먼저 이해할 점

“이 DBMS는 ACID를 지원한다”는 말만으로 실제 보장 수준을 전부 설명할 수 없다. 다음 조건에 따라 결과가 달라진다.

- 사용하는 storage engine
- transaction isolation level
- durability 관련 설정
- synchronous 또는 asynchronous replication
- 단일 node인지 분산 환경인지
- application이 설정한 transaction 경계

ACID와 isolation level은 같은 개념도 아니다. ACID의 `I`가 isolation이며, 어떤 동시성 현상까지 차단할지는 선택한 isolation level과 DBMS 구현에 따라 달라진다.

## MySQL InnoDB

InnoDB는 transaction, rollback, crash recovery, FK와 MVCC를 지원하는 MySQL의 기본 storage engine이다.

- **Atomicity**: undo log 등을 이용해 rollback
- **Consistency**: PK, FK, UNIQUE, CHECK 등의 constraint와 transaction으로 유지
- **Isolation**: MVCC와 lock으로 구현
- **Durability**: redo log와 binary log, flush 설정 등을 이용
- 일반적인 기본 isolation level: `REPEATABLE READ`

```sql
SHOW VARIABLES LIKE 'default_storage_engine';
SELECT @@transaction_isolation;
```

“완전한 ACID”라고만 외우기보다 durability 설정을 함께 봐야 한다. 예를 들어 log를 disk에 언제 flush할지 정하는 설정을 성능 위주로 완화하면 장애 시 최근 commit을 잃을 가능성이 달라질 수 있다.

## MySQL MyISAM

MyISAM은 transaction을 지원하지 않는다.

- `COMMIT`, `ROLLBACK`으로 여러 statement를 하나의 원자적 작업으로 묶을 수 없음
- FK constraint를 지원하지 않음
- row-level lock 대신 table-level lock 사용
- crash recovery와 동시성 특성이 InnoDB와 다름

따라서 일반적인 OLTP transaction 관점에서는 ACID를 지원하는 engine으로 보면 안 된다.

```sql
CREATE TABLE legacy_logs (
    id BIGINT PRIMARY KEY
) ENGINE = MyISAM;
```

현재 MySQL의 기본 engine은 일반적으로 InnoDB지만, legacy table은 MyISAM일 수 있으므로 table별 engine을 확인한다.

```sql
SELECT table_schema, table_name, engine
FROM information_schema.tables
WHERE table_schema = 'appdb';
```

## PostgreSQL

PostgreSQL은 storage engine을 table마다 바꾸는 MySQL 구조와 다르며, 기본 engine에서 transaction과 MVCC를 제공한다.

- **Atomicity·Durability**: WAL과 transaction 처리
- **Isolation**: MVCC와 lock
- 일반적인 기본 isolation level: `READ COMMITTED`
- Serializable 구현: **SSI(Serializable Snapshot Isolation)**

PostgreSQL은 SQL에서 네 가지 표준 isolation level 이름을 받을 수 있지만, `READ UNCOMMITTED`는 내부적으로 `READ COMMITTED`처럼 동작한다. 따라서 “네 수준을 모두 서로 다른 동작으로 구현한다”고 이해하면 안 된다.

SSI는 위험한 transaction 의존 관계를 감지하면 transaction 하나를 serialization failure로 중단할 수 있다. application은 전체 transaction을 retry할 수 있어야 한다.

## Oracle Database

Oracle도 undo와 redo, read consistency, lock을 이용해 성숙한 transaction 기능을 제공한다.

- 일반적인 기본 isolation level: `READ COMMITTED`
- `SERIALIZABLE`과 read-only transaction 지원
- undo data를 이용한 consistent read
- redo를 이용한 crash recovery

Oracle이 상용 환경에서 오랫동안 사용되었다는 사실과 “어떤 설정에서도 항상 더 강한 ACID를 제공한다”는 주장은 구분해야 한다. commit durability, replication, RAC/Data Guard 구성과 application transaction 설계를 함께 확인한다.

## Amazon RDS와 Aurora

### Amazon RDS

RDS는 MySQL, PostgreSQL, Oracle, SQL Server 등의 DB engine을 관리해 주는 서비스다. RDS 자체가 하나의 새로운 transaction engine은 아니다.

```text
RDS for MySQL의 transaction 특성
→ 기본적으로 MySQL/InnoDB 특성을 따름

RDS for PostgreSQL의 transaction 특성
→ 기본적으로 PostgreSQL 특성을 따름
```

Multi-AZ, backup, failover 같은 운영 기능을 제공하지만 “RDS를 사용하면 자동으로 write가 수평 확장된다”고 이해하면 안 된다.

### Amazon Aurora

Aurora는 MySQL 또는 PostgreSQL 호환 interface를 제공하면서 storage 계층을 cloud 환경에 맞게 별도로 설계한 DB다.

- cluster storage가 여러 AZ에 걸쳐 data copy를 유지
- 일반적으로 세 AZ에 두 copy씩, 총 여섯 copy를 유지하는 구조로 설명됨
- compute instance와 distributed storage가 분리
- reader instance로 read scale-out 가능
- writer failover와 storage 복구를 자동화

여기서 **여섯 copy**는 application이 여섯 DB에 직접 write한다는 뜻이 아니다. 일반적인 Aurora cluster에는 writer가 있고, storage 계층이 quorum 방식으로 write와 recovery를 처리한다.

Aurora도 일반적인 단일 writer 구성에서는 write가 무제한으로 수평 확장되는 것이 아니다. read scaling, storage 확장, failover 개선과 multi-writer 분산 DB를 구분해야 한다.

## 비교표

| DBMS·Engine | Transaction | MVCC·일관 읽기 | 일반적 기본 격리 | 핵심 주의사항 |
| --- | --- | --- | --- | --- |
| MySQL InnoDB | 지원 | 지원 | Repeatable Read | flush와 binary log 설정 확인 |
| MySQL MyISAM | 미지원 | 미지원 | 해당 없음 | rollback과 FK가 없음 |
| PostgreSQL | 지원 | 지원 | Read Committed | Read Uncommitted가 별도 동작하지 않음 |
| Oracle | 지원 | undo 기반 일관 읽기 | Read Committed | 지원 격리 수준과 운영 구성 확인 |
| RDS | 선택한 engine에 따름 | 선택한 engine에 따름 | 선택한 engine에 따름 | 관리형 서비스이지 단일 DB engine이 아님 |
| Aurora | 지원 | 호환 engine과 Aurora 구조에 따름 | 호환 engine 계열에 따름 | 여섯 storage copy와 write scale-out을 혼동하지 않기 |

## 선택할 때 확인할 질문

```text
어떤 storage engine을 사용하는가?
기본 isolation level과 실제 transaction 설정은 무엇인가?
commit 성공 후 어느 장애까지 data를 보존해야 하는가?
replica는 synchronous인가 asynchronous인가?
serialization failure와 deadlock을 application이 retry하는가?
failover 시 허용할 RPO와 RTO는 얼마인가?
```

