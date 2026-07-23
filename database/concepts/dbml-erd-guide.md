# DBML로 ERD 작성하기

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## DBML이란?

DBML(Database Markup Language)은 text로 table, column, key, relationship을 작성하는 모델링 언어다. `dbdiagram.io` 같은 도구에서 DBML을 입력하면 ERD를 자동으로 그릴 수 있다.

```text
SQL DDL
→ 실제 DBMS에 table을 생성하기 위한 언어

DBML
→ ERD와 schema 구조를 문서화하기 위한 모델링 언어
```

DBML 자체가 MySQL이나 PostgreSQL에서 실행되는 SQL은 아니다. 도구가 DBML을 읽어 ERD를 만들고 DBMS별 DDL로 변환할 수 있다.

## 가장 작은 예제

```dbml
Table members {
  id bigint [pk]
  name varchar(100) [not null]
  email varchar(255) [not null, unique]
  created_at timestamp [not null]
}
```

의미:

- `Table members`: members table
- `id bigint`: bigint type의 id column
- `[pk]`: Primary Key
- `[not null]`: 필수 값
- `[unique]`: 중복 금지

## 회원과 주문 ERD

```dbml
Table members {
  id bigint [pk, increment]
  name varchar(100) [not null]
  email varchar(255) [not null, unique]
  created_at timestamp [not null]
}

Table orders {
  id bigint [pk, increment]
  member_id bigint [not null]
  status varchar(20) [not null]
  total_amount decimal(12, 2) [not null]
  ordered_at timestamp [not null]
}

Ref fk_orders_member: orders.member_id > members.id
```

`orders.member_id > members.id`는 orders의 FK가 members의 PK를 참조한다는 뜻이다.

```text
Member 1
→ Order N
```

## Relationship 기호

DBML의 대표 관계 표현:

| DBML | 의미 |
| --- | --- |
| `A.id < B.a_id` | A 1 : N B |
| `A.id > B.id` | A N : 1 B |
| `A.id - B.id` | 1 : 1 |
| `A.id <> B.id` | N : M 개념 관계 |

실제 관계형 schema에서는 N:M을 junction table로 풀어내는 것이 일반적이다.

## N:M 관계 구현

학생과 강좌:

```dbml
Table students {
  id bigint [pk, increment]
  name varchar(100) [not null]
}

Table courses {
  id bigint [pk, increment]
  title varchar(200) [not null]
}

Table enrollments {
  student_id bigint [not null]
  course_id bigint [not null]
  enrolled_at timestamp [not null]
  score decimal(5, 2)

  indexes {
    (student_id, course_id) [pk]
    (course_id, student_id)
  }
}

Ref: enrollments.student_id > students.id
Ref: enrollments.course_id > courses.id
```

`enrollments`는 관계 자체의 `enrolled_at`, `score`를 저장한다.

## Composite Key와 Index

```dbml
Table order_items {
  order_id bigint [not null]
  item_no int [not null]
  product_id bigint [not null]
  quantity int [not null]
  unit_price decimal(12, 2) [not null]

  indexes {
    (order_id, item_no) [pk]
    product_id
  }
}
```

`indexes` block에서 복합 PK와 일반 index를 표현할 수 있다.

## Enum 표현

```dbml
Enum order_status {
  CREATED
  PAID
  SHIPPED
  CANCELLED
}

Table orders {
  id bigint [pk]
  status order_status [not null]
}
```

주의:

- PostgreSQL에는 native enum이 있다.
- MySQL에도 enum type이 있지만 변경과 migration trade-off가 있다.
- Oracle에서는 version과 설계에 따라 `CHECK`, lookup table 등을 사용할 수 있다.

DBML enum을 실제 DDL로 변환할 때 대상 DBMS의 전략을 다시 선택한다.

## Note로 업무 규칙 기록

```dbml
Table orders [note: '고객 주문. 물리 삭제 대신 상태 변경을 기본으로 한다.'] {
  id bigint [pk]
  status varchar(20) [not null, note: 'CREATED, PAID, SHIPPED, CANCELLED']
}
```

ERD에 보이지 않는 업무 규칙을 note로 남길 수 있다.

## Schema 구분

```dbml
Table sales.orders {
  id bigint [pk]
}

Table inventory.products {
  id bigint [pk]
}
```

PostgreSQL의 schema namespace를 모델링할 때 자연스럽다. MySQL에서는 `sales.orders`를 database와 table의 조합으로 해석할 수 있으므로 DDL export 결과를 검토한다.

## DBML에서 SQL DDL로 갈 때 확인할 것

자동 생성 DDL을 그대로 production에 적용하지 않는다.

```text
자동 ID 문법
MySQL AUTO_INCREMENT
PostgreSQL IDENTITY
Oracle IDENTITY·SEQUENCE

날짜·시간 Type
MySQL DATETIME·TIMESTAMP
PostgreSQL timestamp·timestamptz
Oracle DATE·TIMESTAMP

Boolean
MySQL TINYINT 계열
PostgreSQL boolean
Oracle version·Y/N 전략

Enum
Native enum·CHECK·lookup table

Index
Partial·Expression·Function-based 지원 차이
```

## ERD 작성 순서에 DBML 적용

```text
1. 요구사항을 문장으로 작성
2. Entity와 Relationship 결정
3. Cardinality·Optionality 결정
4. DBML로 Table·Ref 작성
5. 생성된 ERD를 업무 담당자와 검토
6. 정규화와 삭제 정책 검토
7. 대상 DBMS에 맞춰 물리 Type·Index 결정
8. DDL export 후 사람이 검토
```

DBML부터 작성해서 업무 규칙을 끼워 맞추지 않는다.

## 전체 E-commerce 예제

```dbml
Table members {
  id bigint [pk, increment]
  email varchar(255) [not null, unique]
  name varchar(100) [not null]
  created_at timestamp [not null]
}

Table products {
  id bigint [pk, increment]
  name varchar(200) [not null]
  price decimal(12, 2) [not null]
  stock int [not null]
}

Table orders {
  id bigint [pk, increment]
  member_id bigint [not null]
  status varchar(20) [not null]
  total_amount decimal(12, 2) [not null]
  ordered_at timestamp [not null]

  indexes {
    (member_id, ordered_at)
  }
}

Table order_items {
  order_id bigint [not null]
  item_no int [not null]
  product_id bigint [not null]
  quantity int [not null]
  unit_price decimal(12, 2) [not null]

  indexes {
    (order_id, item_no) [pk]
    product_id
  }
}

Ref: orders.member_id > members.id
Ref: order_items.order_id > orders.id [delete: cascade]
Ref: order_items.product_id > products.id
```

`unit_price`는 현재 상품 가격이 아니라 주문 당시 가격을 보존한다.

## 자주 하는 실수

- DBML에서 관계선을 그렸지만 실제 DDL의 FK를 확인하지 않음
- 1:1에 UNIQUE를 빠뜨림
- N:M을 junction table 없이 그대로 둠
- 모든 column을 nullable로 둠
- 삭제 정책을 무조건 CASCADE로 설정
- 자동 생성 DDL의 type을 검토하지 않음
- 논리 ERD와 물리 ERD를 구분하지 않음

