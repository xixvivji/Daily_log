# 집계·JOIN·Subquery·CTE·Window Function

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## 학습 흐름

```text
여러 row를 요약
→ Aggregate·GROUP BY

여러 table을 연결
→ JOIN

Query 안에서 다른 Query 사용
→ Subquery

중간 결과에 이름 부여
→ CTE·View

Row를 유지하면서 순위·누적값 계산
→ Window Function
```

## Aggregate Function

여러 row를 하나의 요약값으로 만든다.

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS average_amount,
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount
FROM orders;
```

### COUNT의 차이

```sql
COUNT(*)
```

row 수를 센다.

```sql
COUNT(coupon_id)
```

`coupon_id`가 NULL이 아닌 row만 센다.

```sql
COUNT(DISTINCT member_id)
```

중복을 제거한 회원 수를 센다.

## GROUP BY

group별로 aggregate한다.

```sql
SELECT
    status,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM orders
GROUP BY status;
```

일반적으로 SELECT에 있는 비집계 column은 GROUP BY에 있어야 한다. Functional dependency를 이용한 허용 범위는 DBMS와 설정에 따라 다를 수 있으므로 이식성이 필요하면 명확히 작성한다.

## HAVING

WHERE는 group을 만들기 전 row를 거르고, HAVING은 group 결과를 거른다.

```sql
SELECT
    member_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'PAID'
GROUP BY member_id
HAVING COUNT(*) >= 5;
```

```text
WHERE
→ PAID row만 선택

GROUP BY
→ member별 그룹

HAVING
→ 주문 5건 이상 group만 선택
```

## 조건부 집계

이식성이 높은 CASE 방식:

```sql
SELECT
    COUNT(*) AS total_count,
    SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) AS paid_count,
    SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_count
FROM orders;
```

PostgreSQL FILTER:

```sql
SELECT
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE status = 'PAID') AS paid_count
FROM orders;
```

MySQL·Oracle과 공통 query가 필요하면 CASE를 우선 검토한다.

## ROLLUP

상세 group과 단계별 subtotal, grand total을 함께 계산한다.

```sql
SELECT
    region,
    category,
    SUM(amount) AS total_amount
FROM sales
GROUP BY ROLLUP (region, category);
```

결과 의미:

```text
region + category
→ category별 합계

region + NULL
→ region subtotal

NULL + NULL
→ 전체 합계
```

실제 data의 NULL과 subtotal 표시용 NULL을 구분하기 위해 `GROUPING` 함수를 사용한다.

```sql
SELECT
    CASE WHEN GROUPING(region) = 1 THEN '전체 지역' ELSE region END AS region,
    CASE WHEN GROUPING(category) = 1 THEN '전체 분류' ELSE category END AS category,
    SUM(amount) AS total_amount
FROM sales
GROUP BY ROLLUP (region, category);
```

## CUBE

모든 dimension 조합의 subtotal을 만든다.

```sql
SELECT
    region,
    category,
    SUM(amount) AS total_amount
FROM sales
GROUP BY CUBE (region, category);
```

생성 group:

```text
(region, category)
(region)
(category)
()
```

dimension이 많으면 조합 수가 빠르게 증가하므로 비용을 주의한다.

## GROUPING SETS

필요한 group 조합만 명시한다.

```sql
SELECT
    region,
    category,
    SUM(amount) AS total_amount
FROM sales
GROUP BY GROUPING SETS (
    (region, category),
    (region),
    ()
);
```

불필요한 조합을 제외할 수 있어 CUBE보다 의도를 명확히 표현할 수 있다.

## DBMS별 Group 기능

| 기능 | MySQL | PostgreSQL | Oracle |
| --- | --- | --- | --- |
| ROLLUP | 지원, 문법 version 확인 | 지원 | 지원 |
| CUBE | version·지원 범위 확인 | 지원 | 지원 |
| GROUPING SETS | version·지원 범위 확인 | 지원 | 지원 |
| FILTER | 일반적으로 CASE 사용 | 지원 | CASE 사용 중심 |

대상 version의 공식 문법을 확인한다.

## JOIN 종류

### INNER JOIN

양쪽에서 조건이 일치하는 row만 반환한다.

```sql
SELECT o.id, m.name
FROM orders o
JOIN members m ON m.id = o.member_id;
```

### LEFT JOIN

왼쪽 row는 모두 유지한다.

```sql
SELECT m.id, m.name, o.id AS order_id
FROM members m
LEFT JOIN orders o ON o.member_id = m.id;
```

오른쪽 조건을 WHERE에 두면 NULL row가 제거되어 INNER JOIN처럼 바뀔 수 있다.

```sql
-- 회원을 보존하면서 PAID 주문만 연결
LEFT JOIN orders o
  ON o.member_id = m.id
 AND o.status = 'PAID'
```

### FULL OUTER JOIN

양쪽의 불일치 row도 모두 반환한다.

- PostgreSQL: 지원
- Oracle: 지원
- MySQL: 전통적으로 직접 FULL OUTER JOIN 문법이 없어 LEFT와 RIGHT 결과를 조합하는 대안 검토

단순 `UNION` 대체는 중복과 NULL 의미를 주의한다.

### Semi Join

상대 table에 존재하는지만 필요하다.

```sql
SELECT m.*
FROM members m
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.member_id = m.id
);
```

### Anti Join

상대 table에 존재하지 않는 row를 찾는다.

```sql
SELECT m.*
FROM members m
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.member_id = m.id
);
```

`NOT IN`의 subquery 결과에 NULL이 있으면 UNKNOWN 때문에 예상과 다른 결과가 나올 수 있어 `NOT EXISTS`가 더 안전한 경우가 많다.

## JOIN Algorithm

SQL의 `JOIN`은 논리 연산이고 Nested Loop·Hash·Merge는 DBMS가 선택하는 물리 실행 방법이다.

### Nested Loop

```text
바깥 row 하나
→ 안쪽 table에서 matching row 탐색
→ 반복
```

바깥 결과가 작고 안쪽 index가 좋으면 효율적이다.

### Hash Join

한 입력으로 hash table을 만들고 다른 입력을 probe한다. 큰 equality join에 유리할 수 있다. Memory를 넘으면 disk spill이 생길 수 있다.

### Merge Join

정렬된 두 입력을 순서대로 병합한다. 이미 정렬되어 있거나 넓은 범위를 처리할 때 유리할 수 있다.

### Block Nested Loop

바깥 row를 block 단위로 모아 안쪽 table scan 횟수를 줄이는 최적화다. MySQL version에 따라 optimizer 전략이 hash join 등으로 변화했으므로 plan에서 실제 선택을 확인한다.

### Batched Key Access

MySQL 계열에서 여러 key lookup을 batch로 모아 storage engine 접근의 locality를 높이는 방식이다.

```text
논리 JOIN 종류
→ INNER·LEFT·SEMI·ANTI

물리 JOIN algorithm
→ Nested Loop·Hash·Merge·BKA
```

둘을 혼동하지 않는다.

## Scalar Subquery

한 값이 필요한 위치에서 한 row·한 column을 반환한다.

```sql
SELECT
    m.id,
    m.name,
    (
        SELECT COUNT(*)
        FROM orders o
        WHERE o.member_id = m.id
    ) AS order_count
FROM members m;
```

여러 row를 반환하면 오류가 날 수 있다. Correlated subquery가 row마다 반복 실행되는지는 optimizer와 plan을 확인한다.

## IN과 EXISTS

```sql
SELECT *
FROM members
WHERE id IN (
    SELECT member_id
    FROM orders
    WHERE status = 'PAID'
);
```

```sql
SELECT m.*
FROM members m
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.member_id = m.id
      AND o.status = 'PAID'
);
```

어느 쪽이 항상 빠르다는 규칙은 없다. Optimizer rewrite, data 분포, NULL 의미를 확인한다.

## ANY와 ALL

`ANY`는 subquery 결과 중 하나라도 비교를 만족하면 참이다.

```sql
SELECT *
FROM products
WHERE price > ANY (
    SELECT price
    FROM products
    WHERE category_id = 10
);
```

`ALL`은 모든 값과의 비교를 만족해야 한다.

```sql
SELECT *
FROM products
WHERE price > ALL (
    SELECT price
    FROM products
    WHERE category_id = 10
);
```

빈 결과와 NULL이 있을 때의 three-valued logic을 확인한다.

## 집합 연산

### UNION

두 결과를 합치고 중복을 제거한다.

```sql
SELECT email FROM customers
UNION
SELECT email FROM leads;
```

### UNION ALL

중복 제거 없이 합친다. 중복 제거 sort·hash 비용이 없으므로 의미상 가능하면 더 효율적일 수 있다.

### INTERSECT

양쪽에 공통으로 있는 row를 반환한다.

### EXCEPT와 MINUS

첫 결과에는 있고 두 번째에는 없는 row를 반환한다.

```text
PostgreSQL
→ EXCEPT

Oracle
→ MINUS, version에 따른 EXCEPT 지원도 확인

MySQL
→ version별 INTERSECT·EXCEPT 지원 범위를 확인하고 JOIN·EXISTS 대안 검토
```

집합 연산의 두 SELECT는 column 수와 호환 가능한 type을 맞춰야 한다.

## CTE

Statement 안에서 중간 query에 이름을 붙인다.

```sql
WITH paid_orders AS (
    SELECT *
    FROM orders
    WHERE status = 'PAID'
)
SELECT member_id, SUM(amount)
FROM paid_orders
GROUP BY member_id;
```

가독성을 높이지만 자동으로 빨라지는 기능은 아니다. Materialize 또는 inline 여부는 DBMS와 version, hint에 따라 다르다.

## Recursive CTE

조직도·category tree·경로처럼 계층을 순회한다.

```sql
WITH RECURSIVE category_tree AS (
    SELECT
        id,
        parent_id,
        name,
        0 AS depth
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        c.id,
        c.parent_id,
        c.name,
        t.depth + 1
    FROM categories c
    JOIN category_tree t ON c.parent_id = t.id
)
SELECT *
FROM category_tree
ORDER BY depth, id;
```

구조:

```text
Anchor Query
→ 시작 row

Recursive Query
→ 직전 결과와 다음 row 연결

종료
→ 더 이상 새 row가 없을 때
```

Cycle이 있으면 무한 반복 또는 제한 초과가 발생할 수 있다. DBMS별 recursion depth와 cycle detection 기능을 확인한다. Oracle에는 전통적인 `CONNECT BY`도 있다.

## View

Query 정의를 DB object로 저장한다.

```sql
CREATE VIEW active_members AS
SELECT id, name, email
FROM members
WHERE status = 'ACTIVE';
```

View는 일반적으로 결과를 저장하지 않는다. 보안 interface와 query 재사용에 유용하지만 복잡한 view 중첩은 plan을 이해하기 어렵게 할 수 있다.

## Materialized View

Query 결과를 물리적으로 저장한다.

```sql
CREATE MATERIALIZED VIEW daily_sales AS
SELECT
    CAST(ordered_at AS DATE) AS order_date,
    SUM(amount) AS total_amount
FROM orders
GROUP BY CAST(ordered_at AS DATE);
```

조회는 빨라질 수 있지만 data가 자동으로 항상 최신인 것은 아니다.

### PostgreSQL

```sql
REFRESH MATERIALIZED VIEW daily_sales;
```

동시 조회를 고려한 `CONCURRENTLY`에는 unique index 등 조건이 필요하다.

### Oracle

Refresh mode와 query rewrite 등 강력한 materialized view 기능이 있다. Fast refresh에는 materialized view log와 query 조건이 필요할 수 있다.

### MySQL

일반적인 native materialized view가 없으므로 summary table, event·batch, trigger, external pipeline 등으로 구현한다.

## Window Function

GROUP BY처럼 row를 하나로 접지 않고 각 row를 유지하면서 group 계산을 한다.

```sql
SELECT
    member_id,
    ordered_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY member_id
        ORDER BY ordered_at
    ) AS cumulative_amount
FROM orders;
```

## 순위 함수

```sql
SELECT
    category_id,
    name,
    price,
    ROW_NUMBER() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS row_number,
    RANK() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS rank,
    DENSE_RANK() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS dense_rank
FROM products;
```

```text
ROW_NUMBER
→ 동점이어도 고유 순번

RANK
→ 동점 다음 순위를 건너뜀

DENSE_RANK
→ 동점 다음 순위를 연속으로 부여
```

## NTILE

정렬된 row를 지정한 수의 bucket으로 나눈다.

```sql
NTILE(4) OVER (ORDER BY total_amount DESC)
```

고객을 매출 상위 25% 단위로 구분하는 용도 등에 사용할 수 있다.

## LAG와 LEAD

이전·다음 row를 참조한다.

```sql
SELECT
    order_date,
    total_amount,
    LAG(total_amount) OVER (ORDER BY order_date) AS previous_amount,
    total_amount
      - LAG(total_amount) OVER (ORDER BY order_date) AS difference
FROM daily_sales;
```

## Window Frame

`PARTITION BY` group 안에서 현재 row가 참고할 범위를 정한다.

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

현재 row와 앞의 6개 row를 포함한다.

7일 이동평균:

```sql
AVG(total_amount) OVER (
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
```

### ROWS와 RANGE

```text
ROWS
→ 물리적인 row 개수 기준

RANGE
→ ORDER BY 값의 peer·값 범위 기준
```

ORDER BY 값이 중복되면 RANGE가 같은 값을 가진 여러 row를 함께 포함할 수 있다. 기본 frame을 암묵적으로 사용하지 말고 의도가 중요하면 명시한다.

## 문자열 집계

### PostgreSQL

```sql
STRING_AGG(name, ', ' ORDER BY name)
```

### MySQL

```sql
GROUP_CONCAT(name ORDER BY name SEPARATOR ', ')
```

길이 제한 설정을 확인한다.

### Oracle

```sql
LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name)
```

결과 길이 초과 처리와 version별 option을 확인한다.

## Array와 JSON 집계

### PostgreSQL

```sql
ARRAY_AGG(name ORDER BY name)
JSON_AGG(name ORDER BY name)
JSONB_AGG(name ORDER BY name)
```

### MySQL

```sql
JSON_ARRAYAGG(name)
JSON_OBJECTAGG(id, name)
```

### Oracle

```sql
JSON_ARRAYAGG(name)
JSON_OBJECTAGG(KEY id VALUE name)
```

정렬, NULL, duplicate key, return type과 최대 크기를 DBMS별로 확인한다.

## 전환 Check

```text
FILTER
→ CASE 조건부 집계로 변환 가능성

FULL OUTER JOIN
→ MySQL 대안 필요

EXCEPT·MINUS
→ 제품별 이름과 지원 version

Recursive CTE
→ WITH RECURSIVE·Oracle CONNECT BY 차이

Materialized View
→ MySQL 대체 구조 필요

STRING_AGG
→ GROUP_CONCAT·LISTAGG

Array
→ MySQL·Oracle에서 JSON 또는 자식 table 대안

Window Frame
→ 기본값과 지원 범위 확인
```

