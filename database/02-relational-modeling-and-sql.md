# 02. 관계형 모델링과 SQL

## 설계의 세 단계

### 개념 모델

업무 담당자의 언어로 관리 대상과 관계를 찾는다.

```text
고객은 주문한다.
주문에는 여러 상품이 들어간다.
상품의 현재 가격과 주문 당시 가격은 다를 수 있다.
```

이 단계에서는 PostgreSQL의 `BIGINT`나 MySQL의 `AUTO_INCREMENT` 같은 제품별 구현을 정하지 않는다.

### 논리 모델

엔티티를 relation으로 바꾸고 PK, FK, cardinality, 정규화를 결정한다.

```text
Customer 1 ── N Order
Order 1 ── N OrderItem
Product 1 ── N OrderItem
```

`OrderItem`은 주문 시점의 `unit_price`와 `quantity`를 보존한다. 현재 상품 가격만 참조하면 과거 주문 금액이 바뀌는 잘못된 모델이 된다.

### 물리 모델

특정 DBMS에 맞춰 타입, 인덱스, 파티션, 저장 옵션, 이름을 정한다.

```sql
CREATE TABLE orders (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id  BIGINT NOT NULL REFERENCES customers(id),
    status       VARCHAR(20) NOT NULL,
    ordered_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_orders_status
        CHECK (status IN ('CREATED', 'PAID', 'SHIPPED', 'CANCELLED'))
);
```

## ERD를 그리는 순서

1. 요구사항 문장에서 명사 후보와 업무 사건을 찾는다.
2. 각각 독립적으로 식별할 수 있는지 확인한다.
3. 속성과 후보 키를 정한다.
4. 관계의 cardinality와 optionality를 정한다.
5. 관계를 PK, FK, UNIQUE, junction table로 구현한다.
6. 실제 업무 시나리오로 생성·수정·삭제를 검증한다.

ERD가 예쁘게 보이는 것보다 업무 규칙이 제약으로 표현되는지가 중요하다.

## Relationship and Normalization

관계 구현과 정규화는 현실 세계의 연결을 관계형 구조로 옮기고, 중복과 데이터 이상을 줄이는 과정이다.

관계형 모델에서는 현실 세계의 연결을 PK, FK, UNIQUE, junction table로 구현한다. 그다음 정규화를 통해 중복과 삽입·삭제·갱신 이상을 줄인다.

```text
업무에서 관계 발견
→ 1:1, 1:N, N:M 판단
→ FK와 UNIQUE로 구현
→ 부모 삭제·수정 정책 결정
→ 정규화로 중복과 종속 관계 정리
```

### 관계 Relationship

Relationship은 table 사이의 업무적 연관성이다. `학생이 강좌를 수강한다`, `회원이 주문한다` 같은 문장을 database 구조로 표현한다.

#### 1:1 관계

FK에 `UNIQUE`를 함께 둔다.

```sql
CREATE TABLE student_cards (
    id         BIGINT PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE REFERENCES students(id)
);
```

`UNIQUE`가 없으면 한 학생이 여러 카드를 가질 수 있으므로 실제로는 `1:N`이다.

#### 1:N 관계

N 쪽이 1 쪽의 FK를 가진다.

```sql
ALTER TABLE orders
ADD CONSTRAINT fk_orders_customer
FOREIGN KEY (customer_id) REFERENCES customers(id);
```

#### N:M 관계

junction table로 해소한다.

```sql
CREATE TABLE enrollments (
    student_id BIGINT NOT NULL REFERENCES students(id),
    course_id  BIGINT NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score NUMERIC(5, 2),
    PRIMARY KEY (student_id, course_id)
);

CREATE INDEX idx_enrollments_course_student
    ON enrollments(course_id, student_id);
```

PK가 `(student_id, course_id)`이면 학생 기준 탐색에는 유리하지만 course만으로 찾는 접근도 많다면 역순 인덱스를 검토한다.

### 외래키 제약 조건 옵션 비교

부모 row를 삭제하거나 key를 변경할 때 자식 row를 어떻게 처리할지 정한다.

```text
orders.id
← order_items.order_id
```

| 옵션 | 동작 | 적합할 수 있는 상황 |
| --- | --- | --- |
| `ON DELETE CASCADE` | 부모 삭제 시 자식도 삭제 | 주문과 주문 항목처럼 생명주기가 완전히 같음 |
| `ON DELETE SET NULL` | 부모 삭제 시 자식 FK를 `NULL`로 변경 | 담당 직원이 사라져도 고객은 유지 |
| `ON DELETE RESTRICT` | 자식이 있으면 부모 삭제 차단 | 상품이 남은 category 삭제 금지 |
| `ON DELETE NO ACTION` | constraint 검사 시점에 위반이면 실패 | 기본적으로 참조 중인 부모 삭제 차단 |
| `ON UPDATE CASCADE` | 부모 key 변경을 자식 FK에 전파 | 변경 가능한 자연 key를 참조 |

#### ON DELETE CASCADE

```sql
FOREIGN KEY (order_id)
REFERENCES orders(id)
ON DELETE CASCADE
```

편리하다는 이유로 선택하지 않는다. 부모 삭제가 자식의 삭제를 업무적으로 의미할 때 사용한다. 실수로 부모를 삭제하면 많은 자식이 함께 삭제될 수 있으므로 감사·법적 보존 대상에는 적합하지 않을 수 있다.

#### ON DELETE SET NULL

```sql
FOREIGN KEY (manager_id)
REFERENCES employees(id)
ON DELETE SET NULL
```

자식 FK가 nullable이어야 한다. 부모가 없어져도 자식 row가 독립적으로 의미를 가져야 한다.

#### ON DELETE RESTRICT와 NO ACTION

둘 다 참조 중인 부모 삭제를 막는 결과로 보일 수 있다.

```text
RESTRICT
→ 위반 작업을 즉시 제한하는 의미

NO ACTION
→ constraint 검사 시점에 위반이면 실패
```

PostgreSQL에서는 deferrable constraint의 검사 시점 때문에 차이가 생길 수 있다. MySQL InnoDB에서는 `NO ACTION`이 사실상 `RESTRICT`처럼 동작한다.

#### ON UPDATE CASCADE

```sql
FOREIGN KEY (department_code)
REFERENCES departments(code)
ON UPDATE CASCADE
```

부모 key가 바뀌면 자식 FK도 변경한다. 다만 PK는 가능한 한 변경되지 않는 surrogate key로 만드는 경우가 많다.

#### DBMS별 외래키 옵션 차이

| 옵션 | MySQL InnoDB | PostgreSQL | Oracle | SQL Server |
| --- | --- | --- | --- | --- |
| `ON DELETE CASCADE` | 지원 | 지원 | 지원 | 지원 |
| `ON DELETE SET NULL` | 지원 | 지원 | 지원 | 지원 |
| `ON DELETE RESTRICT` | 지원 | 지원 | 기본 차단 동작 | `NO ACTION` 중심 |
| `ON DELETE NO ACTION` | RESTRICT와 유사 | 지원, 지연 검사 가능 | 기본 차단 동작 | 지원 |
| `ON UPDATE CASCADE` | 지원 | 지원 | 일반적인 FK 절에서 미지원 | 지원 |
| `SET DEFAULT` | 일반적으로 미지원 | 지원 | 일반적인 FK 절에서 미지원 | 지원 |

Oracle에서 부모 key 변경 전파가 필요하다면 trigger부터 만들기보다 변경되지 않는 PK로 다시 설계할 수 있는지 먼저 검토한다.

### 정규화 Normalization

정규화는 중복을 줄이고 삽입·삭제·갱신 과정에서 data가 모순되는 문제를 줄이는 설계 과정이다.

#### 정규화가 필요한 이유

- **삽입 이상**: 다른 불필요한 정보가 없으면 새 정보를 저장할 수 없음
- **삭제 이상**: 한 row를 삭제했더니 보존해야 할 다른 정보까지 사라짐
- **갱신 이상**: 중복된 값 중 일부만 수정되어 서로 모순됨

#### 제1정규형 1NF

한 칸에 반복 그룹이나 목록을 넣지 않고 원자값으로 표현한다.

```text
나쁜 예: subjects = "DB,Java,Network"
좋은 예: enrollment 한 행이 학생-과목 한 관계
```

JSON이나 array 타입을 썼다고 무조건 1NF 위반이라고 단정할 수는 없다. DBMS가 이를 하나의 domain 값으로 다루기도 한다. 다만 내부 요소를 자주 JOIN, 제약, 집계해야 한다면 별도 relation이 보통 더 낫다.

#### 제2정규형 2NF

복합 후보 키의 일부에만 종속되는 속성을 분리한다.

```text
Enrollment(student_id, course_id, student_name, course_title, score)

student_name은 student_id에만 종속
course_title은 course_id에만 종속
```

분리하면 다음과 같다.

```text
Student(student_id, student_name)
Course(course_id, course_title)
Enrollment(student_id, course_id, score)
```

#### 제3정규형 3NF

키가 아닌 속성에 종속되는 속성을 분리한다.

```text
Employee(employee_id, department_id, department_name)

department_name은 employee_id가 아니라 department_id에 종속
```

분리하면 다음과 같다.

```text
Employee(employee_id, department_id)
Department(department_id, department_name)
```

#### BCNF와 반정규화

BCNF는 모든 결정자가 후보 키가 되도록 요구한다. 3NF보다 강한 형태다.

반정규화는 “정규화를 몰라서 중복한 것”이 아니라 측정된 읽기 병목을 줄이기 위해 의도적으로 중복을 도입하는 설계다. 다음을 함께 정해야 한다.

- 어떤 값이 원본인가
- 중복 값을 언제 갱신하는가
- 실패 시 어떻게 재동기화하는가
- 저장 공간과 쓰기 비용이 얼마인가

## 타입 선택

- 돈: 이진 부동소수점보다 `NUMERIC/DECIMAL`
- 시간: 절대 시점이면 PostgreSQL `TIMESTAMPTZ`, MySQL `TIMESTAMP/DATETIME` 특성 비교
- ID: 예상 수명과 row 수를 고려한 `BIGINT`, UUID
- 문자열: 최대 길이의 업무 의미와 인덱스 크기 고려
- 상태: 변경 가능성이 높으면 lookup table 또는 `CHECK`; enum은 migration 비용 검토
- JSON: 구조가 유동적이고 전체 문서를 함께 다룰 때 사용

시간 타입은 이름만 보고 이식하면 위험하다. PostgreSQL `TIMESTAMPTZ`는 입력 시점을 UTC 기반으로 보존하고 session timezone에 맞춰 표시하지만 원래 timezone 이름을 저장하지 않는다. MySQL의 `TIMESTAMP`와 `DATETIME`도 timezone 변환, 범위, 기본값 동작이 다르다.

## DDL, DML, DCL, TCL

- **DDL**: `CREATE`, `ALTER`, `DROP`으로 구조 정의
- **DML**: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `MERGE`로 데이터 처리
- **DCL**: `GRANT`, `REVOKE`로 권한 제어
- **TCL**: `COMMIT`, `ROLLBACK`, `SAVEPOINT`로 transaction 제어

DBMS마다 DDL의 transactional behavior가 다르다. PostgreSQL에서는 많은 DDL을 transaction으로 되돌릴 수 있지만 MySQL에는 implicit commit을 일으키는 DDL이 있다.

## JOIN을 결과 집합으로 이해하기

- **INNER JOIN**: 양쪽 조건이 맞는 행만 반환
- **LEFT JOIN**: 왼쪽 행은 모두 보존하고 불일치한 오른쪽 컬럼은 `NULL`
- **RIGHT JOIN**: 오른쪽 행을 보존
- **FULL OUTER JOIN**: 양쪽의 불일치 행까지 모두 보존
- **CROSS JOIN**: 가능한 모든 조합
- **SELF JOIN**: 같은 테이블을 서로 다른 alias로 JOIN
- **SEMI JOIN 의미**: 상대편에 존재하는지만 필요하며 보통 `EXISTS`
- **ANTI JOIN 의미**: 상대편에 존재하지 않는지만 필요하며 보통 `NOT EXISTS`

`LEFT JOIN`한 오른쪽 테이블 조건을 `WHERE`에 두면 `NULL` 행이 제거되어 사실상 INNER JOIN이 될 수 있다.

```sql
-- 오른쪽 조건을 만족하지 않아도 고객을 보존
SELECT c.id, o.id
FROM customers c
LEFT JOIN orders o
  ON o.customer_id = c.id
 AND o.status = 'PAID';
```

## 서브쿼리, CTE, View

- **Scalar Subquery**: 한 행, 한 컬럼 결과
- **Correlated Subquery**: 바깥 행을 참조하는 서브쿼리
- **CTE**: 한 statement 안에서 이름 붙인 중간 query
- **View**: query 정의를 DB 객체로 저장한 가상 테이블
- **Materialized View**: query 결과를 물리적으로 저장한 객체

CTE가 항상 성능을 높이는 것도, 항상 느린 것도 아니다. PostgreSQL 버전과 `MATERIALIZED` 지정, 참조 횟수에 따라 inline 또는 materialize될 수 있으므로 plan을 확인한다.

Materialized View는 조회를 빠르게 하지만 결과가 자동으로 항상 최신인 것은 아니다. refresh 주기, 잠금, 증분 갱신 가능성을 설계해야 한다.

## Window Function

window function은 행을 `GROUP BY`처럼 한 행으로 접지 않고 주변 행을 참고한 값을 계산한다.

```sql
SELECT
    customer_id,
    ordered_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY ordered_at
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount
FROM orders;
```

- `PARTITION BY`: 계산 그룹
- `ORDER BY`: 그룹 안의 순서
- `ROWS/RANGE`: 현재 행이 참고할 frame
- `ROW_NUMBER`: 행마다 고유 순번
- `RANK`: 동점 다음 순위를 건너뜀
- `DENSE_RANK`: 동점 다음 순위를 연속으로 부여
- `LAG/LEAD`: 이전·다음 행 값 참조

window의 `ORDER BY`는 계산 순서를 정할 뿐 최종 출력 순서를 보장하지 않는다. 결과 정렬이 필요하면 최상위 query에도 `ORDER BY`를 둔다.
