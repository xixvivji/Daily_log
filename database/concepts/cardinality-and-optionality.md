# Cardinality와 Optionality

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## 가장 쉬운 구분

```text
Cardinality
→ 최대 몇 개까지 연결되는가?

Optionality
→ 최소 몇 개가 반드시 필요한가?
```

두 개를 합치면 다음 범위를 표현할 수 있다.

| 표기 | 최소 | 최대 | 의미 |
| --- | ---: | --- | --- |
| `0..1` | 0 | 1 | 없어도 되고, 있으면 하나 |
| `1..1` | 1 | 1 | 반드시 정확히 하나 |
| `0..N` | 0 | 여러 개 | 없어도 되고, 여러 개 가능 |
| `1..N` | 1 | 여러 개 | 최소 하나, 여러 개 가능 |

## 회원과 주문 예시

업무 규칙:

```text
회원은 주문하지 않을 수도 있고 여러 주문을 할 수 있다.
주문은 반드시 한 회원에게 속한다.
```

해석:

```text
Member → Order
Optionality = 0
Cardinality = N
결과 = 0..N

Order → Member
Optionality = 1
Cardinality = 1
결과 = 1..1
```

물리 schema:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id)
);
```

`member_id NOT NULL`과 FK가 주문이 반드시 존재하는 회원 한 명을 참조하게 만든다.

## Optional Relationship

배송 정보가 아직 없을 수 있다고 가정한다.

```text
Order → Shipment
0..1
```

주문 직후에는 배송 row가 없고, 배송이 시작되면 하나가 생긴다.

```sql
CREATE TABLE shipments (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

`UNIQUE`는 주문당 배송 row가 최대 하나라는 cardinality를 구현한다. 배송 row 자체가 아직 없을 수 있으므로 주문 입장에서는 optional이다.

## Mandatory Relationship

주문 항목은 반드시 주문에 속해야 한다.

```text
OrderItem → Order
1..1
```

```sql
order_id BIGINT NOT NULL
    REFERENCES orders(id)
```

- `NOT NULL`: 관계가 반드시 있음
- FK: 실제 존재하는 주문을 참조

## 1:1 관계

```text
Student 1 ── 1 StudentCard
```

실제로는 양쪽 optionality를 추가로 확인해야 한다.

```text
학생은 아직 학생증이 없을 수 있음
Student → StudentCard = 0..1

학생증은 반드시 학생 한 명에게 속함
StudentCard → Student = 1..1
```

## 1:N 관계

```text
Department 1 ── N Employee
```

추가 질문:

- 부서에 직원이 0명이어도 되는가?
- 직원은 부서 없이 존재할 수 있는가?

답에 따라 다음처럼 달라진다.

```text
Department → Employee = 0..N 또는 1..N
Employee → Department = 0..1 또는 1..1
```

## N:M 관계

```text
Student N ── M Course
```

관계형 DB에서는 junction table로 바꾼다.

```text
Student 1 ── N Enrollment
Course  1 ── N Enrollment
```

수강 전 학생과 신청자가 없는 강좌도 존재할 수 있다면:

```text
Student → Enrollment = 0..N
Course  → Enrollment = 0..N
Enrollment → Student = 1..1
Enrollment → Course = 1..1
```

## Crow's Foot 표기법

일반적으로 다음 기호를 조합한다.

```text
○
→ 0, optional

│
→ 1

까마귀발
→ many
```

조합:

| 의미 | 기호 해석 |
| --- | --- |
| `0..1` | 원 + 선 |
| `1..1` | 선 + 선 |
| `0..N` | 원 + 까마귀발 |
| `1..N` | 선 + 까마귀발 |

ERD 도구마다 방향과 표시 모양이 조금 다를 수 있으므로 범례를 확인한다.

[IE 표기법과 Crow's Foot을 그림처럼 읽는 방법](ie-crows-foot-notation.md)

## 물리 Schema로 변환

| 논리 규칙 | 물리 구현 후보 |
| --- | --- |
| 반드시 관계가 있어야 함 | FK column `NOT NULL` |
| 관계가 없어도 됨 | FK column nullable 또는 자식 row 부재 |
| 최대 하나만 연결 | FK에 `UNIQUE` |
| 여러 개 연결 | N 쪽에 일반 FK |
| N:M 연결 | Junction table |
| 부모 삭제 제한 | `RESTRICT`·`NO ACTION` |
| 부모와 함께 삭제 | `CASCADE` |

## 자주 하는 실수

### 1:1이라고 말했지만 UNIQUE가 없음

FK만 두면 같은 부모를 여러 자식이 참조할 수 있어 1:N이 된다.

### Optionality를 NULL 하나로만 판단

관계를 별도 자식 table로 표현하면 부모 table에 nullable FK가 없어도 optional 관계가 가능하다. 자식 row가 아직 없는 상태가 `0`을 표현한다.

### 양방향을 확인하지 않음

```text
회원은 주문을 여러 개 가진다.
```

이 문장만으로 주문이 회원 없이 존재할 수 있는지는 알 수 없다. 반드시 반대 방향도 질문한다.

### 업무 규칙과 현재 data를 혼동

현재 모든 회원이 주문을 가지고 있다고 해서 관계가 반드시 `1..N`인 것은 아니다. 신규 회원이 주문 없이 존재할 수 있다면 업무 규칙은 `0..N`이다.

## 확인 문제

1. 회원은 주소를 여러 개 등록할 수 있지만 주소는 회원 한 명에게만 속한다면 양방향 범위는 무엇인가?
2. 주문에는 최소 한 개의 주문 항목이 필요하다는 규칙을 DB만으로 완전히 강제할 수 있는가?
3. 부서 없는 직원이 허용된다면 FK에 어떤 변화가 필요한가?
4. 1:1과 1:N을 물리 schema에서 구분하는 핵심 constraint는 무엇인가?
