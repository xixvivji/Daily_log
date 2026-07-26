# View·Materialized View·JOIN 알고리즘·Bitmap Scan 상세

이 문서는 이름이 비슷하지만 서로 다른 개념을 실행 계획 관점에서 연결한다.

```text
View 계열: SQL 또는 조회 결과를 재사용하는 방법
JOIN 알고리즘: 두 입력을 실제로 결합하는 방법
Scan 방식: 필요한 행을 실제 저장소에서 찾는 방법
```

## 1. View, Materialized View, Indexed View

### 일반 View

View는 `SELECT` 결과 자체가 아니라 **SELECT 정의를 저장한 논리적 창구**다.

```sql
CREATE VIEW active_members AS
SELECT member_id, name
FROM members
WHERE status = 'ACTIVE';
```

`SELECT * FROM active_members`를 실행하면 DBMS는 저장된 SQL을 원래 질의와 합치거나 변형해 실행한다. 따라서 원본 테이블의 변경은 다음 조회에 반영된다. 다만 현재 트랜잭션에서 어떤 버전이 보이는지는 격리 수준과 MVCC 규칙을 따른다.

- 장점: 복잡한 SQL 재사용, 권한을 제한한 인터페이스, 애플리케이션과 테이블 구조의 결합 완화
- 주의: 결과를 미리 저장하지 않으므로 View를 만들었다는 이유만으로 빨라지지 않는다.
- 주의: View가 여러 겹 중첩되면 최종 SQL과 실행 계획을 이해하기 어려울 수 있다.

### Materialized View

Materialized View(MV)는 **조회 결과를 물리적으로 저장한 객체**다. 매번 큰 집계나 JOIN을 다시 하지 않아도 되므로 읽기는 빨라질 수 있지만, 원본과 저장 결과 사이에 시차가 생긴다.

```text
원본 데이터 변경 → MV에는 아직 이전 결과 → Refresh → 최신 결과로 교체
```

```sql
-- PostgreSQL 예시
CREATE MATERIALIZED VIEW daily_sales AS
SELECT ordered_at::date AS order_date, SUM(amount) AS total_amount
FROM orders
GROUP BY ordered_at::date;

CREATE UNIQUE INDEX daily_sales_pk ON daily_sales(order_date);
REFRESH MATERIALIZED VIEW daily_sales;
```

설계할 때는 다음을 먼저 결정한다.

1. 얼마나 오래된 결과까지 허용할 것인가: 실시간, 5분, 하루
2. 전체를 다시 계산할 것인가, 변경분만 반영할 것인가
3. Refresh 중 조회 또는 쓰기 차단을 얼마나 허용할 것인가
4. MV 자체에 어떤 인덱스가 필요한가
5. Refresh 실패 시 이전 결과를 유지할지, 재시도할지

DBMS별로 같은 이름이라도 기능이 다르다.

| DBMS | 대표 방식 | 알아둘 점 |
|---|---|---|
| PostgreSQL | `CREATE/REFRESH MATERIALIZED VIEW` | 일반 Refresh와 동시 Refresh의 잠금·선행 조건이 다르다. `CONCURRENTLY` 사용에는 적절한 unique index 등이 필요하다. |
| Oracle | Materialized View, query rewrite, refresh 옵션 | `COMPLETE`, `FAST`, `FORCE`, `ON DEMAND`, `ON COMMIT` 등 선택지가 있으며 Fast Refresh 가능 여부는 MV 정의와 log 구성에 달려 있다. |
| SQL Server | Indexed View | 별도의 MV 문법 대신 schema-bound View에 실제 index를 만들어 결과를 물리화한다. |
| MySQL | 보통 summary table로 직접 구현 | 일반적으로 native MV가 없으므로 batch/event, trigger, CDC pipeline 등으로 갱신한다. |

### SQL Server의 Indexed View

Indexed View는 단순히 “View 조회에 원본 테이블 인덱스를 사용했다”는 뜻이 아니다. SQL Server에서 `WITH SCHEMABINDING`으로 만든 View에 먼저 unique clustered index를 생성해 View 결과를 물리적으로 유지하는 기능을 가리킨다.

```sql
-- SQL Server 개념 예시: 실제 적용 전 edition·version과 제한 조건 확인
CREATE VIEW dbo.sales_summary
WITH SCHEMABINDING
AS
SELECT product_id, COUNT_BIG(*) AS order_count, SUM(amount) AS total_amount
FROM dbo.orders
GROUP BY product_id;

CREATE UNIQUE CLUSTERED INDEX ix_sales_summary
ON dbo.sales_summary(product_id);
```

읽기는 빨라질 수 있지만 원본 `INSERT/UPDATE/DELETE` 때 Indexed View의 index도 유지해야 하므로 쓰기 비용이 증가한다. schema binding, 필수 `SET` option, 허용되지 않는 SQL 표현, edition·optimizer의 자동 사용 여부를 적용 환경에서 확인해야 한다.

> PPT의 핵심 범위는 View와 Materialized View다. `Indexed View`는 다른 DBMS로 전환할 때 필요한 SQL Server 대응 개념으로 추가한 것이다.

## 2. 논리 JOIN과 물리 JOIN 알고리즘

SQL의 `INNER JOIN`, `LEFT JOIN`은 **원하는 결과**를 표현한다. Nested Loop, Hash Join, Merge Join은 optimizer가 그 결과를 **어떻게 계산할지** 선택한 물리 알고리즘이다. 같은 SQL도 통계, 데이터 양, 인덱스, 메모리, parameter 값에 따라 다른 알고리즘을 사용할 수 있다.

### Nested Loop

바깥쪽(outer) 입력의 행을 하나씩 읽고, 각 행마다 안쪽(inner) 입력에서 일치하는 행을 찾는다.

```text
outer 1행 ─→ inner 탐색
outer 2행 ─→ inner 탐색
outer 3행 ─→ inner 탐색
```

바깥 결과가 10행이고 안쪽 join key에 index가 있다면 빠른 index lookup 10번으로 끝날 수 있다. 반대로 optimizer는 10행으로 예상했는데 실제로 100만 행이라면 안쪽 탐색도 100만 번 반복될 수 있다.

잘 맞는 경우:

- outer 입력이 작거나 조건이 매우 선택적일 때
- inner join key에 효율적인 index가 있을 때
- 일부 결과를 빨리 반환해야 할 때

실행 계획에서는 `actual rows`만 보지 말고 `loops`를 함께 본다. 안쪽 node의 작업량은 대략 `한 번의 rows × loops`로 이해해야 한다.

### Hash Join

보통 더 작은 입력(build side)을 읽어 join key 기반 hash table을 만들고, 다른 입력(probe side)의 key로 hash table을 탐색한다.

```text
작은 입력 → hash table 생성
큰 입력   → key를 hash → 같은 bucket의 후보 비교
```

대량의 **동등 조건**(`a.id = b.id`) JOIN에 유리하며, 안쪽 테이블에 lookup index가 없어도 사용할 수 있다. 그러나 index가 무의미한 것은 아니다. JOIN 전에 각 입력을 줄이는 filter에는 index가 도움이 될 수 있다.

hash table이 작업 메모리를 넘으면 여러 batch로 나뉘고 임시 디스크 I/O가 발생할 수 있다. PostgreSQL에서는 `Buckets`, `Batches`, memory usage를, SQL Server에서는 memory grant와 spill 경고를 확인한다. 부등호나 범위 조건만 있는 JOIN에는 일반적인 Hash Join을 적용할 수 없다.

### Merge Join

두 입력을 join key 순서로 정렬한 뒤 양쪽 포인터를 앞으로 이동하며 같은 key를 묶는다.

```text
왼쪽:  1 2 2 5  ──▶
오른쪽: 2 2 3 5  ──▶
```

이미 index 순서로 읽을 수 있거나 앞 단계 결과가 정렬되어 있고, 넓은 범위를 결합할 때 유리할 수 있다. 입력이 정렬되어 있지 않으면 Sort 비용이 추가되며, 정렬이 memory를 넘으면 disk spill이 날 수 있다. 중복 key가 많으면 동일 key 그룹을 모두 조합해야 한다.

### 빠른 비교

| 알고리즘 | 잘 맞는 상황 | 주요 위험 신호 |
|---|---|---|
| Nested Loop | 작은 outer + 빠른 inner index lookup | inner의 매우 큰 `loops`, 잘못된 row 추정 |
| Hash Join | 큰 equi-join, 정렬되지 않은 입력 | hash batches 증가, memory 부족과 spill |
| Merge Join | 이미 정렬된 입력, 넓은 범위 처리 | 큰 Sort, disk spill, 중복 key 폭증 |

알고리즘 이름과 노출 방식은 DBMS마다 다르다. PostgreSQL과 Oracle, SQL Server는 실행 계획에서 이들을 비교적 명시적으로 보여준다. MySQL도 버전과 실행 조건에 따라 nested-loop 계열, hash join 등을 선택하지만 다른 DBMS 계획 node와 이름만으로 일대일 대응시키면 안 된다.

## 3. PostgreSQL Bitmap Index Scan → Bitmap Heap Scan

PostgreSQL의 이 두 node는 보통 한 쌍으로 동작한다.

```text
Bitmap Index Scan
  조건에 맞을 가능성이 있는 tuple/page 위치를 bitmap으로 표시
                    ↓
Bitmap Heap Scan
  bitmap을 보고 heap page를 효율적인 순서로 읽어 실제 row 확인
```

### 왜 바로 일반 Index Scan을 하지 않는가

일반 Index Scan은 index에서 위치 하나를 찾을 때마다 heap으로 이동할 수 있다. 일치 행이 아주 적으면 좋지만 수천·수만 행이 여러 page에 흩어져 있으면 page를 반복해서 오가는 비용이 커진다.

Bitmap 방식은 위치를 먼저 모은 뒤 같은 heap page에 있는 행들을 묶어서 읽는다. 그래서 대략 다음 중간 영역에서 유리할 수 있다.

```text
아주 적은 행       → Index Scan 후보
중간 정도의 행     → Bitmap Index Scan + Bitmap Heap Scan 후보
테이블의 많은 행   → Sequential Scan 후보
```

경계는 고정 비율이 아니다. table 크기, clustering, cache, random/sequential I/O 비용, 통계에 따라 달라진다.

### 여러 인덱스 조건 결합

```sql
CREATE INDEX orders_status_idx ON orders(status);
CREATE INDEX orders_date_idx ON orders(ordered_at);

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE status = 'PAID'
  AND ordered_at >= DATE '2026-07-01';
```

optimizer는 두 `Bitmap Index Scan` 결과를 `BitmapAnd`로 합치거나, OR 조건이면 `BitmapOr`로 합칠 수 있다. 복합 index 하나가 항상 필요하다는 뜻도, bitmap 결합이 항상 더 좋다는 뜻도 아니다. 실제 workload와 계획을 비교한다.

### Exact와 Lossy bitmap

메모리가 충분하면 exact bitmap이 정확한 tuple 위치를 기억한다. 메모리가 부족하면 lossy bitmap이 page 단위로만 “이 page 안에 후보가 있다”고 기억할 수 있다. 이 경우 heap page를 읽은 뒤 조건을 다시 검사한다.

계획에서 확인할 항목:

- `Recheck Cond`: heap에서 다시 확인할 조건
- `Heap Blocks: exact=... lossy=...`: 정확한 page와 손실 압축된 page 수
- `Rows Removed by Index Recheck`: 재검사 후 탈락한 행
- `Buffers`: 실제 cache hit/read page 수

`Recheck Cond`가 표시됐다고 항상 lossy였다는 뜻은 아니므로 actual 실행 통계의 `lossy`와 제거 행 수를 같이 본다. `work_mem`을 무조건 올리는 대신 query 동시 실행 수와 전체 memory 사용량도 함께 계산해야 한다.

### Oracle Bitmap Index와 혼동 금지

PostgreSQL의 `Bitmap Index Scan`은 실행 중 여러 index 결과를 memory bitmap으로 모으는 **실행 방식**이다. Oracle의 Bitmap Index는 각 key의 row 집합을 bitmap 형태로 저장하는 **영구 index 구조**다. 이름에 Bitmap이 들어가지만 같은 개념이 아니다.

Oracle Bitmap Index는 값 종류가 적고 읽기 중심인 분석 환경에 유용할 수 있지만, 동시 변경이 잦은 OLTP에서는 잠금·유지 비용을 신중히 검토한다. MySQL 실행 계획도 PostgreSQL의 `Bitmap Heap Scan` node를 그대로 사용하지 않으므로 DB 전환 시 이름을 치환하지 말고 목적과 실제 계획을 다시 검증한다.

## 4. 실행 계획을 읽는 순서

1. 실제 실행이 허용되는 환경에서 `EXPLAIN ANALYZE` 계열을 사용했는지 확인한다. 실제 SQL을 실행할 수 있으므로 운영 변경문에는 주의한다.
2. 가장 오래 걸리거나 가장 많은 buffer를 읽은 node를 찾는다.
3. 예상 rows와 실제 rows 차이를 찾는다. 차이가 크면 통계, data skew, 상관관계를 의심한다.
4. Nested Loop 안쪽 node는 `loops`까지 곱해 본다.
5. Hash와 Sort의 batch, memory, disk spill을 확인한다.
6. Bitmap Heap Scan은 exact/lossy block과 recheck 탈락 행을 확인한다.
7. index 하나를 강제로 추가하기 전에 SQL 결과, 전체 쓰기 비용, 다른 query 영향까지 비교한다.

핵심은 “Hash Join이 무조건 빠르다”처럼 알고리즘을 서열화하는 것이 아니다. **현재 데이터 양과 분포에서 optimizer의 추정이 실제와 맞았는지**, 선택한 접근 방식이 실제 I/O와 반복량을 얼마나 만들었는지를 확인하는 것이다.
