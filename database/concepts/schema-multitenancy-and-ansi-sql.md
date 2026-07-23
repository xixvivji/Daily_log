# Schema 멀티테넌시와 ANSI SQL

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## 멀티테넌시란?

하나의 서비스가 여러 고객사·조직·학교·상점을 함께 제공하는 구조다. 각 고객 단위를 tenant라고 부른다.

```text
SaaS 회계 서비스
├── A 회사
├── B 회사
└── C 회사
```

핵심 요구:

- A 회사가 B 회사의 data를 볼 수 없어야 한다.
- tenant가 늘어날 때 운영 가능한 비용이어야 한다.
- 장애와 backup의 영향 범위를 정해야 한다.
- schema change를 모든 tenant에 적용할 수 있어야 한다.

## Silo Model

tenant마다 database 또는 instance를 분리한다.

```text
Tenant A → Database A
Tenant B → Database B
Tenant C → Database C
```

장점:

- 강한 격리
- tenant별 backup·restore·삭제가 쉬움
- 큰 tenant만 별도로 확장 가능
- 장애 영향 범위가 tenant 단위

단점:

- database 수가 늘어남
- migration과 monitoring 대상 증가
- connection pool과 비용 증가
- 전체 tenant 분석이 어려움

금융·의료·대기업 전용 환경처럼 격리와 개별 운영이 중요할 때 검토한다.

## Pool Model

모든 tenant가 같은 table을 공유하고 `tenant_id`로 구분한다.

```sql
CREATE TABLE orders (
    tenant_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (tenant_id, order_id)
);
```

장점:

- 적은 수의 database로 운영
- schema migration이 단순
- 자원 효율이 좋음
- 전체 tenant 분석이 쉬움

단점:

- 모든 query에서 tenant 조건이 필요
- 조건 누락 시 data 유출
- noisy neighbor 문제
- 특정 tenant 복구·분리가 어려움

안전 원칙:

```text
PK·UNIQUE에 tenant_id 포함 검토
모든 FK에도 tenant_id 포함 검토
Repository 공통 filter
PostgreSQL RLS 같은 DB 보안
tenant context의 위조 방지
```

잘못된 unique:

```sql
UNIQUE (email)
```

tenant마다 같은 이메일을 허용해야 한다면:

```sql
UNIQUE (tenant_id, email)
```

## Bridge Model

여러 tenant가 database 또는 schema를 일정 그룹으로 나눠 공유한다.

```text
Database Group 1
→ Tenant A, B, C

Database Group 2
→ Tenant D, E, F
```

Pool의 운영 효율과 Silo의 격리를 절충한다.

활용 예:

- region별 database
- 요금제별 database
- 큰 tenant는 전용 database
- 작은 tenant는 shared pool

어떤 tenant가 어느 database에 있는지 찾는 routing metadata가 필요하다.

## PostgreSQL Schema-per-tenant

한 database 안에 tenant별 schema를 둘 수 있다.

```text
appdb
├── tenant_a.orders
├── tenant_b.orders
└── tenant_c.orders
```

장점:

- table 이름과 namespace 분리
- tenant별 schema export 가능

주의:

- tenant가 많으면 table·index·catalog object 폭증
- 모든 schema에 migration 적용 필요
- connection의 `search_path`를 잘못 사용하면 다른 tenant 접근 위험
- database 전체 장애는 공유

MySQL의 `schema`는 database와 사실상 같은 의미이므로 PostgreSQL schema-per-tenant와 같은 계층으로 보면 안 된다.

## 선택 기준

| 질문 | Silo | Pool | Bridge |
| --- | --- | --- | --- |
| 격리 | 가장 강함 | 논리적 격리 중심 | 중간 |
| 운영 대상 수 | 많음 | 적음 | 중간 |
| Tenant별 복구 | 쉬움 | 어려움 | 그룹 단위·일부 가능 |
| 전체 분석 | 어려움 | 쉬움 | 통합 과정 필요 |
| 비용 효율 | 낮을 수 있음 | 높음 | 중간 |
| Noisy Neighbor | 작음 | 큼 | 그룹 안에서 발생 |

## ANSI SQL이란?

SQL의 국제 표준을 말한다. DBMS가 공통으로 이해할 수 있는 문법과 의미의 기준을 제공한다.

```text
표준 SQL
→ 공통 언어의 기준

DBMS Dialect
→ 각 제품이 추가하거나 다르게 구현한 문법
```

표준 SQL을 사용하면 이식성이 좋아질 수 있지만 DBMS 전환이 자동으로 되는 것은 아니다.

## 공통성이 높은 SQL

```sql
SELECT department_id, COUNT(*) AS employee_count
FROM employees
WHERE status = 'ACTIVE'
GROUP BY department_id
HAVING COUNT(*) >= 5
ORDER BY employee_count DESC;
```

SELECT, WHERE, GROUP BY, HAVING, ORDER BY의 기본 구조는 여러 DBMS에서 공통성이 높다.

## 제품별 차이가 큰 영역

### 자동 ID

```text
MySQL
→ AUTO_INCREMENT

PostgreSQL
→ GENERATED AS IDENTITY

Oracle
→ IDENTITY 또는 SEQUENCE
```

### 문자열 연결

```sql
-- MySQL
SELECT CONCAT(first_name, ' ', last_name);

-- PostgreSQL·Oracle
SELECT first_name || ' ' || last_name;
```

### Pagination

```sql
-- MySQL·PostgreSQL
LIMIT 20 OFFSET 100;

-- 표준 계열·Oracle
OFFSET 100 ROWS FETCH NEXT 20 ROWS ONLY;
```

### Upsert

```text
MySQL
→ ON DUPLICATE KEY UPDATE

PostgreSQL
→ ON CONFLICT

Oracle
→ MERGE
```

### NULL 정렬

`ORDER BY`에서 NULL이 처음 또는 마지막에 오는 기본 동작이 다를 수 있다.

```sql
ORDER BY updated_at DESC NULLS LAST
```

지원 문법과 기본값을 확인한다.

## ORM이 모든 차이를 없애지 못하는 이유

ORM은 기본 CRUD와 parameter binding을 도와주지만 다음은 제품 차이가 남는다.

- Native SQL
- JSON·Array·GIS type
- Partial·Function-based index
- Lock hint와 isolation
- ID 생성
- Procedure·Function
- Migration DDL
- Pagination plan

JPA dialect를 바꿨다고 production migration이 완료되는 것이 아니다.

## 이식성을 높이는 방법

```text
업무 핵심 query는 표준 SQL 우선
제품 고유 기능은 사용 이유 기록
Native query inventory 관리
DB migration tool의 DBMS별 script 분리
Integration test를 대상 DBMS에서 실행
NULL·날짜·문자열·정렬 결과 비교
실행 계획과 성능을 별도 검증
```

## 제품 고유 기능을 써도 되는가?

가능하다. 이식성만을 위해 유용한 기능을 모두 포기할 필요는 없다.

```text
PostgreSQL JSONB·GIN
Oracle PL/SQL·Partitioning
MySQL InnoDB 특성
```

다만 선택 시 기록한다.

- 어떤 문제를 해결했는가?
- 표준 SQL 대안은 무엇인가?
- 다른 DBMS로 이동할 때 대체 기능은 무엇인가?
- migration 비용을 받아들일 가치가 있는가?

