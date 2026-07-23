# 06. 분산·Cloud DB와 운영

## 관리형 DB와 분산 DB를 구분한다

- **Managed Database**: provider가 patch, backup, monitoring, failover 일부를 대신 운영
- **Distributed Database**: 여러 node에 data와 처리를 분산하는 architecture
- **Serverless Database**: 사용량에 따라 capacity와 billing을 자동 조정하는 운영 모델

RDS에서 PostgreSQL을 쓴다고 자동으로 분산 DB가 되는 것은 아니다. 반대로 분산 DB도 운영 책임이 사라지는 것은 아니다.

## Replication과 Consistency

### Synchronous Replication

replica의 확인을 기다려 durability를 강화하지만 write latency와 가용성에 영향을 줄 수 있다.

### Asynchronous Replication

primary가 먼저 응답해 latency가 낮지만 장애 전환 시 아직 복제되지 않은 data를 잃을 수 있다.

### Read Replica

read 부하를 분산하지만 replication lag 때문에 방금 쓴 값을 못 읽을 수 있다. read-after-write가 필요한 요청은 primary로 routing하거나 consistency token 같은 제품 기능을 검토한다.

## Consensus

Raft와 Paxos 계열 consensus는 여러 node가 log 순서나 leader에 합의하도록 돕는다. WAL이 한 DB instance의 장애 복구 기록이라면 consensus log는 여러 node의 상태 합의를 다룬다. 실제 분산 DB에서는 두 개념이 결합될 수 있다.

## CAP를 과도하게 단순화하지 않기

CAP는 network partition이 발생했을 때 consistency와 availability를 동시에 완전히 만족할 수 없다는 성질을 설명한다. 평상시 latency와 consistency 선택까지 `CP/AP` 두 글자로 모두 설명하지 못한다.

PACELC는 partition 때의 선택뿐 아니라 정상 상태에서 latency와 consistency trade-off도 보자는 관점이다.

## MSA의 Database per Service

각 service가 자신의 data를 소유하면 독립 배포와 기술 선택에 유리하다. 대신 cross-service JOIN과 transaction이 사라지는 것이 아니라 API, event, read model 문제로 이동한다.

- **Saga**: local transaction과 compensation
- **Outbox**: DB 변경과 event 기록의 원자성
- **CDC**: transaction log에서 변경 event 추출
- **CQRS**: command model과 query model 분리
- **Eventual Consistency**: 시간이 지나면 replica나 derived view가 수렴

eventual consistency는 “언젠가 맞겠지”가 아니다. 허용 지연, 재처리, 순서 뒤바뀜, 중복, reconciliation을 설계해야 한다.

## Redis, Kafka, Elasticsearch의 역할

### Redis

cache, session, rate limit, short-lived coordination에 유용하다. cache miss, stampede, invalidation, persistence 정책을 설계한다.

### Kafka

durable event stream과 service decoupling에 유용하다. partition key, ordering 범위, consumer offset, schema compatibility, duplicate 처리를 정한다.

### Elasticsearch/OpenSearch

전문 검색과 log 분석에 유용하다. 일반적으로 RDBMS의 source of truth를 대체하기보다 CDC 등으로 search index를 만든다. refresh 지연과 재색인을 고려한다.

## Data Warehouse와 분석 DB

운영 query와 분석 query는 접근 패턴이 다르다.

```text
OLTP
→ 소수 row, 짧은 transaction, 높은 동시성

OLAP
→ 많은 row scan, JOIN과 aggregate, columnar 처리
```

ETL은 추출 후 변환해 적재하고, ELT는 먼저 적재한 뒤 warehouse 안에서 변환한다. pipeline에는 schema evolution, late event, replay, data quality가 필요하다.

## 보안

### Identity와 최소 권한

- 사람 계정과 application 계정 분리
- schema owner와 runtime role 분리
- runtime application에 DDL 권한 금지
- role에 권한을 주고 user에는 role 부여
- secret rotation과 접속 위치 제한

### SQL Injection

값은 prepared statement로 binding한다. column명과 `ORDER BY` 방향처럼 identifier 위치에는 parameter binding을 쓸 수 없으므로 allowlist로 선택한다.

ORM도 raw SQL에 문자열을 이어 붙이면 취약하다.

### 암호화

- in transit: TLS
- at rest: disk/storage encryption 또는 TDE
- field/column: application 또는 DB 기능으로 민감값 선택 암호화
- key: KMS와 접근 권한, rotation, recovery 관리

암호화는 권한 통제와 감사를 대체하지 않는다. key와 data가 같은 권한 경계에 있으면 공격자에게 함께 노출될 수 있다.

## Backup, Restore, HA, DR

- **Backup**: 복구 가능한 별도 사본
- **Snapshot**: 특정 시점 storage 상태
- **PITR**: base backup과 transaction log로 원하는 시점 복구
- **HA**: 같은 서비스 영역의 장애에서 빠른 복구
- **DR**: region 상실 같은 큰 재해에서 복구
- **RPO**: 허용 가능한 data loss 시간
- **RTO**: 허용 가능한 복구 시간

replication은 backup이 아니다. 실수로 삭제하거나 corruption이 생기면 replica에도 전파된다.

backup 성공 알림보다 restore test가 중요하다. 복원한 DB의 무결성과 application 연결까지 정기적으로 검증한다.

## 모니터링

### 사용자 관점

- 성공률과 timeout
- p50/p95/p99 latency
- transaction throughput

### DB 관점

- active/idle connection과 pool wait
- CPU, memory, IOPS, storage latency
- buffer/cache hit와 eviction
- slow query와 plan 변화
- lock wait와 deadlock
- replication lag
- transaction log와 storage 증가
- autovacuum/purge 진행

### 알람 원칙

한순간의 CPU 80%보다 사용자 영향과 지속 시간을 연결한다.

```text
p99 상승 + lock wait 증가
replication lag 지속 + replica read 오류
storage 증가율 + 남은 시간 예측
connection 사용률 + pool wait
```

## 운영 runbook

각 알람에는 다음이 있어야 한다.

1. 무엇이 정상이고 무엇이 이상인가
2. dashboard와 확인 query
3. 최근 배포·schema 변경 확인 방법
4. 안전한 완화 조치
5. escalation 담당자
6. 복구 확인 기준
7. 사후 분석에 남길 자료

