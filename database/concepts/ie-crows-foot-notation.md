# IE 표기법과 Crow's Foot

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## IE 표기법이란?

IE(Information Engineering) 표기법은 ERD에서 Entity와 Relationship을 표현하는 대표적인 방법이다. 관계 끝을 새 발 모양으로 표시하기 때문에 Crow's Foot, 즉 까마귀발 표기법이라고도 부른다.

```text
Entity
→ 사각형

Relationship
→ Entity 사이의 선

최소·최대 개수
→ 관계선 양 끝의 ○, │, 까마귀발
```

## 기본 기호

| 기호 | 의미 | 읽는 방법 |
| --- | --- | --- |
| `○` | Zero | 없어도 된다 |
| `│` | One | 하나다 |
| 까마귀발 | Many | 여러 개다 |

최소 개수 기호와 최대 개수 기호를 조합한다.

## 조합 기호

텍스트에서는 까마귀발을 `<`로 단순화해서 표현한다.

| 조합 | 범위 | 의미 |
| --- | --- | --- |
| `○│` | `0..1` | 없거나 하나 |
| `││` | `1..1` | 반드시 정확히 하나 |
| `○<` | `0..N` | 없거나 여러 개 |
| `│<` | `1..N` | 최소 하나, 여러 개 |

실제 ERD 도구에서는 `<` 대신 세 갈래로 벌어진 까마귀발이 표시된다.

## 관계선을 읽는 방법

다음 업무 규칙을 보자.

```text
회원은 주문을 하지 않을 수도 있고 여러 주문을 할 수 있다.
주문은 반드시 회원 한 명에게 속한다.
```

관계:

```text
Member ││────────○< Order
```

양방향으로 읽는다.

```text
Member에서 Order 방향
→ 한 회원은 주문을 0개 이상 가질 수 있다.

Order에서 Member 방향
→ 한 주문은 반드시 회원 한 명에게 속한다.
```

기호가 관계선의 어느 쪽에 붙었는지 보지 않고 외우면 방향을 반대로 읽기 쉽다.

## 1:1 관계

학생은 학생증이 아직 없을 수 있지만, 학생증은 반드시 학생 한 명에게 속한다고 가정한다.

```text
Student ││────────○│ StudentCard
```

```text
Student → StudentCard
→ 0..1

StudentCard → Student
→ 1..1
```

물리 schema:

```sql
CREATE TABLE student_cards (
    card_id BIGINT PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
);
```

`UNIQUE`가 최대 하나를 구현한다.

## 1:N 관계

부서는 직원이 없을 수도 있고 여러 명일 수도 있으며, 직원은 반드시 한 부서에 속한다고 가정한다.

```text
Department ││────────○< Employee
```

```text
Department → Employee
→ 0..N

Employee → Department
→ 1..1
```

물리 schema에서는 N 쪽인 Employee가 FK를 가진다.

```sql
department_id BIGINT NOT NULL
    REFERENCES departments(department_id)
```

## N:M 관계

학생은 여러 강좌를 수강할 수 있고 강좌에도 여러 학생이 참여할 수 있다.

개념 ERD:

```text
Student ○<────────○< Course
```

관계형 DB의 논리·물리 모델에서는 중간 Entity를 추가한다.

```text
Student ││────○< Enrollment >○────││ Course
```

```sql
CREATE TABLE enrollments (
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

## Entity Box 읽기

IE 계열 ERD에서는 Entity를 사각형으로 표현하고 이름과 Attribute를 적는다.

```text
┌──────────────────────┐
│ MEMBER               │
├──────────────────────┤
│ PK member_id         │
│ UK email             │
│    name              │
│    joined_at         │
└──────────────────────┘
```

- `PK`: Primary Key
- `FK`: Foreign Key
- `UK`: Unique Key
- `PK, FK`: 두 역할을 동시에 수행하는 column

도구에 따라 열쇠 icon, 밑줄, 별도 영역으로 key를 표시할 수 있다.

## 식별 관계 Identifying Relationship

자식의 PK에 부모의 PK가 포함되는 관계다.

```text
Order
→ OrderItem

OrderItem PK = (order_id, item_no)
order_id는 Order의 PK를 참조하는 FK
```

```sql
CREATE TABLE order_items (
    order_id BIGINT NOT NULL,
    item_no INT NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (order_id, item_no),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

많은 ERD 도구에서 실선으로 표현하지만 도구별 표기 규칙을 확인한다.

## 비식별 관계 Non-identifying Relationship

부모 FK가 자식 table에 있지만 자식 PK에는 포함되지 않는 관계다.

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id)
);
```

`member_id`는 FK지만 `orders.id`와 별개의 PK다. 많은 도구에서 점선으로 표현하지만 이 역시 도구 설정을 확인한다.

## Mandatory와 Optional을 물리 Schema로 변환

### 자식에서 부모가 필수

```text
Order → Member = 1..1
```

```sql
member_id BIGINT NOT NULL
    REFERENCES members(id)
```

### 자식에서 부모가 선택

```text
Customer → Manager = 0..1
```

```sql
manager_id BIGINT NULL
    REFERENCES employees(id)
```

### 부모에서 자식이 최대 하나

```text
Student → StudentCard = 0..1
```

자식 FK에 `UNIQUE`를 둔다.

## IE 표기법과 Chen 표기법

ERD 표기법은 IE만 있는 것이 아니다.

| 구분 | IE·Crow's Foot | Chen |
| --- | --- | --- |
| Entity | 사각형 | 사각형 |
| Attribute | Entity box 내부에 주로 표시 | 타원으로 분리 |
| Relationship | 선과 Crow's Foot | 마름모 |
| 실무 물리 ERD | 자주 사용 | 개념 모델 교육에서 자주 사용 |

표기법이 달라도 표현하려는 핵심은 Entity, Attribute, Relationship, Cardinality, Optionality다.

## DBMS와 IE 표기법의 관계

IE 표기법은 MySQL이나 PostgreSQL만의 기능이 아니다. DBMS에 독립적인 모델링 표현이다.

```text
IE ERD
→ 논리 관계 정의

MySQL·PostgreSQL·Oracle
→ PK, FK, UNIQUE, NOT NULL로 물리 구현
```

DBMS마다 DDL 문법과 FK option은 다를 수 있지만 1:1, 1:N, N:M이라는 논리 관계는 동일하다.

## 자주 하는 실수

### `│` 하나만 보고 방향을 판단

양쪽 끝 기호를 각각 읽어야 한다.

### 현재 data 개수로 Cardinality 결정

현재 주문이 하나뿐이어도 업무상 여러 주문이 가능하면 `N`이다.

### Optionality를 생략

`1:N`만 적으면 최소가 0인지 1인지 알 수 없다. `0..N`과 `1..N`은 다른 규칙이다.

### 1:1인데 UNIQUE를 생략

ERD에는 1:1이라고 그렸지만 물리 schema에 `UNIQUE`가 없으면 DB는 여러 자식 row를 허용한다.

### N:M을 그대로 Table 두 개만으로 구현

Junction table이 없으면 관계별 속성과 FK 무결성을 제대로 표현하기 어렵다.

## 확인 문제

다음 관계를 IE 표기법으로 생각해 본다.

```text
1. 회원은 주소를 등록하지 않거나 여러 개 등록할 수 있다.
2. 주소는 반드시 회원 한 명에게 속한다.
3. 주문은 쿠폰을 사용하지 않거나 하나만 사용할 수 있다.
4. 쿠폰은 여러 주문에 사용될 수 있다.
```

답:

```text
Member → Address = 0..N
Address → Member = 1..1

Order → Coupon = 0..1
Coupon → Order = 0..N
```

