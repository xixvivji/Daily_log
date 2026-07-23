# 특수 Index·Partition·고급 DB 설계

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## Index를 선택하는 기준

Index 종류는 column type만으로 정하지 않는다.

```text
어떤 연산을 하는가?
→ equality, range, 포함, 거리, 전문 검색

몇 row를 반환하는가?
→ selectivity

data가 어떻게 분포하는가?
→ 균등·편향·시간 순서

읽기와 쓰기 비율은?
→ index 유지 비용
```

## B-Tree

Equality, range, sorting에 가장 일반적으로 사용한다.

```sql
CREATE INDEX idx_orders_member_created
ON orders(member_id, created_at);
```

적합 query:

```sql
SELECT *
FROM orders
WHERE member_id = 10
  AND created_at >= TIMESTAMP '2026-01-01 00:00:00'
ORDER BY created_at;
```

## Hash Index

Hash는 equality lookup을 위한 구조다.

```text
유리할 수 있음
→ column = value

일반적으로 부적합
→ range, ORDER BY, prefix
```

PostgreSQL은 Hash index를 제공한다. MySQL에서 `USING HASH`의 실제 지원은 storage engine에 따라 다르며 InnoDB 일반 secondary index를 Hash index로 바꾸는 문법이라고 가정하면 안 된다. Oracle은 Hash Cluster 등 다른 구조와 구분한다.

## PostgreSQL GIN

GIN(Generalized Inverted Index)은 하나의 row가 여러 key를 포함하는 값에 유용하다.

- Array
- JSONB
- Full Text Search
- `pg_trgm`과 조합한 검색

```sql
CREATE INDEX idx_products_attrs
ON products USING GIN(attrs);

SELECT *
FROM products
WHERE attrs @> '{"color":"red"}';
```

Trade-off:

- 복합 값을 검색하는 읽기에 강함
- Index 크기와 쓰기 비용이 클 수 있음
- operator class와 query operator가 맞아야 함

MySQL JSON index와 Oracle JSON Search Index는 문법과 내부 구현이 다르므로 GIN DDL을 그대로 옮길 수 없다.

## PostgreSQL GiST

GiST(Generalized Search Tree)는 여러 검색 전략을 구현할 수 있는 framework형 index다.

- PostGIS 공간 범위
- Range type
- Nearest-neighbor
- 일부 text·similarity extension

```sql
CREATE INDEX idx_places_location
ON places USING GIST(location);
```

GIN과 GiST는 “둘 다 고급 index”가 아니라 지원 operator와 workload가 다르다. Full-text에서 GIN은 lookup이 빠를 수 있고 GiST는 compact·lossy 특성 등 다른 trade-off가 있다.

## PostgreSQL BRIN

BRIN(Block Range Index)은 table의 연속 block 범위에 대한 최소·최대 등 요약 정보를 저장한다.

```sql
CREATE INDEX idx_logs_created_brin
ON logs USING BRIN(created_at);
```

적합할 수 있는 상황:

- 매우 큰 append-only table
- `created_at`과 물리 저장 순서의 상관관계가 높음
- 정확한 row 위치보다 block 범위를 빠르게 제외하고 싶음

장점:

- Index가 매우 작음
- 생성·유지 비용이 낮을 수 있음

단점:

- B-Tree처럼 정확한 row 위치를 직접 찾지 않음
- 물리 순서와 값의 상관관계가 낮으면 효과 감소
- false positive block을 다시 검사

Oracle의 Zone Map, 다른 columnar DB의 min-max skipping과 목적이 비슷한 면이 있지만 같은 기능은 아니다.

## Bitmap Index

Oracle Bitmap Index는 값 종류가 적은 dimension column과 분석 workload에서 유용할 수 있다.

```sql
CREATE BITMAP INDEX idx_sales_region
ON sales(region_code);
```

OLTP에서 row update가 많으면 bitmap segment locking과 유지 비용 때문에 부적합할 수 있다.

PostgreSQL 실행 계획의 `Bitmap Heap Scan`은 영구적인 Oracle Bitmap Index와 같은 의미가 아니다. 여러 B-Tree 결과 등을 memory bitmap으로 결합하는 실행 방식이다.

## Function·Expression Index

```sql
-- PostgreSQL
CREATE INDEX idx_members_lower_email
ON members(lower(email));
```

```sql
-- Oracle
CREATE INDEX idx_members_lower_email
ON members(LOWER(email));
```

MySQL은 functional key part 또는 generated column 전략을 version에 맞게 사용한다.

Query의 표현식이 index 정의와 의미상 맞아야 한다.

## Index 선택표

| 요구 | 우선 검토 |
| --- | --- |
| Equality·Range·Sort | B-Tree |
| PostgreSQL JSONB·Array 포함 검색 | GIN |
| PostgreSQL 공간·Range·Nearest Neighbor | GiST |
| 시간 순서의 초대형 Append Table | BRIN |
| Oracle 분석용 저 Cardinality | Bitmap Index |
| `LOWER(email)` 검색 | Expression·Function-based |
| 전문 검색 | DB Full Text Index 또는 검색 engine |

## Cardinality Estimate

Optimizer는 실제 실행 전에 각 node의 row 수를 추정한다.

```text
예상 10 rows
실제 100,000 rows
```

이 차이가 크면 작은 입력에 적합한 Nested Loop를 선택했다가 반복이 폭증할 수 있다.

원인:

- 오래된 statistics
- column 값의 심한 편향
- 서로 연관된 column을 독립으로 추정
- expression과 function
- parameter 값마다 선택도가 다름

## Statistics

### PostgreSQL

```sql
ANALYZE orders;
```

`pg_stats`, statistics target, extended statistics를 검토한다.

```sql
CREATE STATISTICS st_orders_status_region
ON status, region_id
FROM orders;
```

상관된 column의 joint 분포 추정에 도움을 줄 수 있다.

### MySQL

InnoDB statistics, histogram, `ANALYZE TABLE`을 검토한다.

```sql
ANALYZE TABLE orders;
```

### Oracle

DBMS_STATS와 histogram을 사용한다.

```sql
BEGIN
  DBMS_STATS.GATHER_TABLE_STATS(
    ownname => 'SHOP',
    tabname => 'ORDERS'
  );
END;
/
```

통계를 자주 갱신할수록 항상 좋은 것은 아니다. 수집 비용과 plan 변화 안정성을 함께 본다.

## Parameter-sensitive Plan

같은 SQL도 parameter에 따라 최적 plan이 다를 수 있다.

```text
status = 'RARE'
→ Index Scan 유리

status = 'COMMON'
→ Full Scan 유리
```

MySQL, PostgreSQL prepared statement의 generic/custom plan, SQL Server parameter sniffing, Oracle bind peeking·adaptive cursor sharing처럼 제품별 대응이 다르다.

## Partitioning

큰 logical table을 기준에 따라 여러 partition으로 나눈다.

```text
orders
├── orders_2025
├── orders_2026
└── orders_2027
```

목적:

- 필요한 partition만 읽기
- 오래된 data의 빠른 archive·drop
- maintenance 범위 분리
- 일부 workload 관리 개선

Partitioning은 query 하나를 자동으로 빠르게 만드는 마법이 아니다.

## Range Partition

날짜·숫자 범위로 나눈다.

```sql
-- PostgreSQL
CREATE TABLE orders (
    id BIGINT,
    ordered_at TIMESTAMP NOT NULL,
    amount NUMERIC(12, 2)
) PARTITION BY RANGE (ordered_at);

CREATE TABLE orders_2026
PARTITION OF orders
FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

MySQL의 `PARTITION BY RANGE`, Oracle Range Partition 문법과 관리 기능은 다르다.

## List Partition

Region, 상태 같은 값 목록으로 나눈다.

```text
sales_kr
sales_jp
sales_us
```

값 종류가 계속 늘어날 때 default partition과 운영 정책을 검토한다.

## Hash Partition

Hash 결과로 row를 비교적 균등하게 분산한다.

```text
member_id hash
→ partition 0..7
```

특정 range 제거에는 불리하지만 hotspot 분산을 도울 수 있다.

## Partition Pruning

Query 조건으로 불필요한 partition을 제외한다.

```sql
SELECT SUM(amount)
FROM orders
WHERE ordered_at >= TIMESTAMP '2026-07-01 00:00:00'
  AND ordered_at <  TIMESTAMP '2026-08-01 00:00:00';
```

2026년 7월과 관련된 partition만 읽도록 pruning할 수 있다.

Pruning을 방해할 수 있는 예:

```sql
WHERE EXTRACT(YEAR FROM ordered_at) = 2026
```

DBMS가 expression을 partition 범위로 변환하지 못하면 더 많은 partition을 읽을 수 있다. 실행 계획에서 확인한다.

## Partitioning의 비용

- 모든 query가 partition key를 사용하지 않을 수 있음
- Global·Local Index 관리 차이
- FK와 UNIQUE 제약 제한 가능
- 너무 많은 partition은 catalog와 planning 비용 증가
- Partition key를 잘못 고르면 data skew
- DBMS 전환 시 DDL과 운영 script 재작성

## BCNF

모든 결정자가 후보 key가 되도록 요구한다.

```text
결정자 X
→ 어떤 속성 Y를 유일하게 결정하는 X
```

3NF보다 강하지만 dependency 보존과 분해 결과를 함께 검토한다.

## 4NF

서로 독립적인 다치 종속을 분리한다.

```text
Teacher
→ 여러 Subject
→ 여러 Hobby
```

정규화 전:

```text
TeacherSubjectHobby(teacher_id, subject, hobby)
```

Subject와 Hobby가 독립인데 모든 조합이 중복된다.

분리:

```text
TeacherSubject(teacher_id, subject)
TeacherHobby(teacher_id, hobby)
```

## 5NF

Join dependency 때문에 더 작은 relation으로 무손실 분해할 수 있는지를 다룬다.

```text
Supplier
Part
Project
```

세 관계의 모든 조합을 하나의 table에 저장하는 대신 업무 규칙이 허용하면 pair relation으로 분해할 수 있다. 실무에서 1NF~3NF·BCNF보다 자주 직접 언급되지는 않지만 복잡한 N-way relationship에서 의미가 있다.

## SCD

SCD(Slowly Changing Dimension)는 Data Warehouse에서 dimension 변경 이력을 관리하는 방식이다.

### Type 1

기존 값을 덮어쓴다.

```text
과거 이력 불필요
주소 오류 수정
```

### Type 2

새 row를 추가해 기간별 이력을 보존한다.

```text
customer_sk
customer_id
address
valid_from
valid_to
is_current
```

```sql
UPDATE dim_customer
SET valid_to = CURRENT_TIMESTAMP,
    is_current = 'N'
WHERE customer_id = 10
  AND is_current = 'Y';

INSERT INTO dim_customer(...)
VALUES (..., CURRENT_TIMESTAMP, NULL, 'Y');
```

### Type 3

현재 값과 이전 값 column을 함께 둔다.

```text
current_region
previous_region
```

제한된 이전 값만 필요할 때 사용한다.

## Sharding Key

Data를 여러 DB node에 나눌 기준이다.

좋은 후보 특성:

- 값이 균등하게 분포
- 대부분의 query가 shard key를 알고 있음
- 한 transaction의 data가 같은 shard에 모임
- 값이 잘 바뀌지 않음

나쁜 예:

```text
country_code
→ 특정 국가에 data 집중

created_month
→ 최신 shard에 write 집중
```

`tenant_id`, `member_id`도 workload에 따라 hotspot과 cross-shard query를 검토한다.

## Partitioning과 Sharding 차이

```text
Partitioning
→ 한 DBMS의 logical table 내부 분할일 수 있음

Sharding
→ 여러 독립 DB node에 data 분산
```

Partitioning은 optimizer와 DBMS가 투명하게 처리하는 경우가 많지만 sharding은 routing, cross-shard transaction, rebalancing이 추가된다.

