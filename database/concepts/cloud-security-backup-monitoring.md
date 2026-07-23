# Cloud DB·보안·백업·모니터링

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## On-Premise와 Managed DB

### On-Premise

조직이 server, storage, OS, DBMS를 직접 운영한다.

책임:

- Hardware
- OS patch
- DB 설치·upgrade
- Backup
- Replication·Failover
- Monitoring

### Managed DB·DBaaS

Cloud provider가 infrastructure와 일부 DB 운영을 대신한다.

사용자 책임이 남는 영역:

- Schema·Query·Index
- User·Role
- Network 접근
- Backup retention 선택
- Restore 검증
- 비용·용량
- Application transaction

Managed라고 자동으로 안전하거나 빠른 것은 아니다.

## RDS

Amazon RDS는 MySQL, PostgreSQL, MariaDB, Oracle, SQL Server 등을 관리하는 서비스다.

```text
RDS for MySQL
→ MySQL engine 특성을 따름

RDS for PostgreSQL
→ PostgreSQL engine 특성을 따름
```

주요 기능:

- Automated backup
- Snapshot
- Multi-AZ
- Read Replica
- Monitoring integration

Multi-AZ standby와 read replica는 목적이 다르다.

```text
Multi-AZ
→ HA·Failover

Read Replica
→ Read scaling, replication lag 가능
```

## Aurora

MySQL·PostgreSQL 호환 interface와 cloud-native distributed storage를 결합한다.

- Compute와 cluster storage 분리
- 여러 AZ에 storage copy
- Writer와 reader instance
- Failover 자동화
- Storage 자동 확장

일반 구성은 single writer이므로 storage가 분산됐다고 write가 무제한 scale-out되는 것은 아니다.

## Cloud SQL과 Azure Database

### Google Cloud SQL

MySQL, PostgreSQL, SQL Server managed service다. HA, backup, read replica, IAM·network integration을 제공한다.

### Azure Database

Azure Database for PostgreSQL, Azure SQL 계열 등 제품별 architecture와 호환 범위가 다르다.

같은 “Managed PostgreSQL”이어도 extension, superuser 권한, version, backup 방식이 다를 수 있다.

## Serverless DB

사용량에 따라 compute capacity를 자동 조정하거나 scale-to-zero를 제공하는 운영 모델이다.

확인할 항목:

- Cold start
- 최소·최대 capacity
- Connection 수와 pooling
- Transaction 중 scaling
- Storage·I/O 비용
- Scale-to-zero 시 background 작업

Serverless는 DB 종류가 아니라 capacity 운영·billing 방식이다.

## Spanner

분산 SQL과 synchronous replication, global consistency를 목표로 하는 managed distributed DB다.

- SQL interface
- Horizontal scaling
- Consensus replication
- Timestamp·TrueTime 기반 transaction 설계

일반 단일-node MySQL의 drop-in replacement로 보면 안 된다. Key 설계, hotspot, inter-region latency와 비용을 검토한다.

## Cosmos DB

Azure의 globally distributed multi-model NoSQL service다.

- Partition key 중요
- 여러 consistency level
- Request Unit 기반 capacity 모델

관계형 JOIN과 transaction 범위가 RDBMS와 다르다.

## PlanetScale·Neon·Supabase

### PlanetScale

MySQL 계열 distributed architecture와 online schema workflow로 알려져 있다. 제공 기능과 FK 지원 정책은 시점·plan·제품 변경을 확인한다.

### Neon

PostgreSQL-compatible serverless platform으로 compute와 storage 분리, branching 등의 기능을 제공한다.

### Supabase

Managed PostgreSQL을 중심으로 authentication, storage, realtime API 등을 결합한 platform이다.

제품은 빠르게 변하므로 실제 선택 시 공식 문서와 현재 plan을 확인한다.

## DW와 분석 DB

### Redshift

AWS columnar data warehouse. Distribution style·sort key와 workload management가 중요하다.

### BigQuery

Serverless 분석 warehouse. Scan data 양과 partition·clustering이 비용과 성능에 영향을 준다.

### Snowflake

Storage와 compute warehouse 분리, 독립 scaling과 data sharing 기능을 제공한다.

### ClickHouse

Columnar OLAP DB로 빠른 aggregate와 compression에 강하다. MergeTree 계열 table engine과 sorting key 설계가 중요하다.

OLTP의 짧은 row update와 강한 transaction을 그대로 대체하는 용도로 선택하지 않는다.

## NewSQL

관계형 SQL·ACID와 수평 확장을 함께 제공하려는 DB 계열이다.

- CockroachDB
- TiDB
- YugabyteDB
- Spanner

“MySQL-compatible”은 client protocol이나 SQL 일부 호환을 의미할 수 있으며 optimizer, transaction, DDL, 운영이 동일하다는 뜻은 아니다.

## TimescaleDB

PostgreSQL extension 기반 시계열 기능을 제공한다.

- Hypertable
- Time·space partition
- Compression
- Retention
- Continuous Aggregate

일반 PostgreSQL table에서 시작할 수 있지만 extension version과 managed service 지원을 확인한다.

## pgvector

PostgreSQL에서 vector type과 similarity search를 제공한다.

```sql
CREATE EXTENSION vector;

CREATE TABLE documents (
    id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536)
);
```

Index:

- HNSW
- IVFFlat

선택 기준:

- Recall
- Query latency
- Build time
- Memory
- Filter와 vector search 결합

전용 Vector DB와 비교할 때 규모, 운영 일원화, consistency, metadata filter를 본다.

## Authentication과 Authorization

```text
Authentication
→ 누구인가?

Authorization
→ 무엇을 할 수 있는가?
```

Application runtime 계정과 migration 계정을 분리한다.

## MySQL Role

```sql
CREATE ROLE 'app_reader';
GRANT SELECT ON shop.* TO 'app_reader';

CREATE USER 'app_user'@'10.%' IDENTIFIED BY 'strong-password';
GRANT 'app_reader' TO 'app_user'@'10.%';
SET DEFAULT ROLE 'app_reader' TO 'app_user'@'10.%';
```

MySQL은 `user@host`로 접속 위치까지 계정 식별에 포함한다.

## PostgreSQL Role

```sql
CREATE ROLE app_reader NOLOGIN;
GRANT CONNECT ON DATABASE shop TO app_reader;
GRANT USAGE ON SCHEMA public TO app_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;

CREATE ROLE app_user LOGIN PASSWORD 'strong-password';
GRANT app_reader TO app_user;
```

Default privilege를 별도로 설정하지 않으면 미래 table에 권한이 자동 부여되지 않을 수 있다.

## Oracle Role

```sql
CREATE ROLE app_reader;
GRANT CREATE SESSION TO app_reader;
GRANT SELECT ON shop.orders TO app_reader;
GRANT app_reader TO app_user;
```

`SELECT ANY TABLE`처럼 과도하게 넓은 system privilege를 피하고 object 단위 권한을 검토한다.

## Row-Level Security

같은 table에서 현재 tenant가 볼 수 있는 row를 제한한다.

PostgreSQL:

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_orders
ON orders
USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
```

주의:

- Tenant context를 신뢰할 수 있게 설정
- Table owner와 bypass role
- Connection pool에서 이전 tenant context 초기화
- INSERT의 `WITH CHECK`

MySQL에는 PostgreSQL과 동일한 native RLS가 없으므로 view, stored routine, application filter, 별도 database 등을 조합한다. Oracle에는 VPD·FGAC 같은 기능이 있다.

## SQL Injection

값은 parameter binding한다.

```text
위험
→ SQL 문자열 + 사용자 입력

안전
→ Prepared Statement의 bind parameter
```

Table·column·ORDER BY 방향은 bind parameter가 될 수 없는 경우가 많으므로 allowlist로 선택한다.

## 암호화

### In Transit

Client와 DB 사이 TLS.

### At Rest

Disk·storage encryption 또는 TDE.

### Column·Application Encryption

민감 column을 선택적으로 암호화한다.

### Key Management

KMS, rotation, 접근 권한, backup key를 관리한다.

Encryption은 authorization과 audit를 대체하지 않는다.

## Backup 종류

### Logical Backup

SQL 또는 logical object 형태.

```text
MySQL
→ mysqldump·MySQL Shell

PostgreSQL
→ pg_dump·pg_restore

Oracle
→ Data Pump
```

장점:

- Object 선택
- 다른 version·platform 이동에 유용

단점:

- 대용량에서 느릴 수 있음
- 완전한 physical state 복구와 다름

### Physical Backup

Data file와 필요한 log를 물리적으로 복사한다.

```text
PostgreSQL
→ Base Backup

MySQL
→ Physical Backup 도구

Oracle
→ RMAN
```

## PITR

Base backup 이후 transaction log를 재생해 원하는 시점까지 복구한다.

```text
PostgreSQL
→ Archived WAL

MySQL
→ Binary Log와 Backup

Oracle
→ Archived Redo와 RMAN
```

PITR 목표 시각은 timezone과 transaction 경계를 명확히 한다.

## RPO와 RTO

```text
RPO
→ 얼마만큼의 data loss를 허용하는가?

RTO
→ 얼마 안에 service를 복구해야 하는가?
```

Backup 주기만으로 결정하지 않고 log archive, replication, restore 시간, DNS·application 전환을 포함한다.

## Replication은 Backup이 아니다

```text
DELETE 실수
→ Replica에도 전달

잘못된 UPDATE
→ Replica에도 전달

Application corruption
→ Replica에도 전달
```

별도 보존·불변 backup과 restore test가 필요하다.

## HA와 DR

```text
HA
→ Instance·AZ 장애에서 빠른 복구

DR
→ Region 상실·대규모 재해에서 복구
```

Standby가 있다는 사실보다 실제 failover와 application reconnect를 test해야 한다.

## Monitoring 기본 지표

### 사용자 영향

- Error rate
- p50·p95·p99 latency
- Timeout
- Throughput

### DB 자원

- CPU
- Memory
- IOPS·storage latency
- Connection
- Temp space

### DB 내부

- Slow query
- Lock wait·deadlock
- Replication lag
- Transaction log 증가
- PostgreSQL VACUUM
- MySQL purge history
- Oracle wait event

## DBMS별 관찰 예

### PostgreSQL

- `pg_stat_activity`
- `pg_stat_statements`
- `pg_locks`
- `pg_stat_replication`

### MySQL

- Performance Schema
- `sys` schema
- Slow Query Log
- `SHOW ENGINE INNODB STATUS`

### Oracle

- Dynamic Performance View
- AWR·ASH 사용 가능 여부와 license
- `V$SESSION`, `V$SQL`, wait event

## Prometheus와 Grafana

```text
Exporter
→ DB metric 노출

Prometheus
→ 주기적으로 metric 수집·저장

Grafana
→ Dashboard 시각화

Alertmanager
→ Alert 전달
```

대표 exporter:

- postgres_exporter
- mysqld_exporter
- Oracle exporter 계열

Exporter 계정에는 monitoring에 필요한 최소 권한만 준다.

## Alert 예시

```text
p99 latency 5분 이상 상승
Lock wait 증가와 함께 발생

Replication lag가 허용 범위 초과

Connection 사용률 증가
Application pool wait도 동시 증가

Storage 남은 시간이 증가율 기준 7일 미만
```

CPU 80% 한 번처럼 사용자 영향이 없는 순간값만으로 page하지 않는다.

## 운영 Runbook

Alert마다 다음을 기록한다.

1. 증상과 사용자 영향
2. Dashboard
3. 확인 SQL
4. 최근 배포·DDL
5. 안전한 완화 조치
6. Failover 조건
7. 복구 확인
8. 사후 분석 자료

## Cloud 전환 Check

On-Premise에서 Cloud DB로 이동할 때:

```text
지원 Version
Extension·Plugin
Superuser 제한
Storage·IOPS
Connection limit
Private Network
TLS
Backup retention
PITR 범위
Multi-AZ
Read Replica lag
Parameter 변경 범위
Maintenance window
Monitoring export
Data egress 비용
Vendor lock-in
```

