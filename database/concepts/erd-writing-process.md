# ERD 작성 순서

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## ERD란?

ERD(Entity Relationship Diagram)는 어떤 데이터를 저장하고, 데이터들이 어떻게 연결되는지 나타낸 그림이다.

```text
회원이 주문한다.
주문에는 상품이 들어간다.

ERD
Member 1 ── N Order
Order 1 ── N OrderItem
Product 1 ── N OrderItem
```

ERD는 table을 예쁘게 그리는 도구가 아니다. 업무 규칙을 table, key, relationship으로 바꾸고 개발자·기획자·DB 담당자가 함께 검토하기 위한 설계도다.

## 1. 요구사항 수집

먼저 사용자가 어떤 일을 하는지 문장으로 적는다.

```text
회원은 여러 주문을 할 수 있다.
주문에는 한 개 이상의 상품이 들어간다.
상품은 여러 주문에 포함될 수 있다.
주문 당시 가격을 보존해야 한다.
회원은 주문하지 않을 수도 있다.
```

좋지 않은 시작:

```text
일단 users table부터 만든다.
필요해 보이는 column을 계속 추가한다.
```

좋은 시작:

```text
업무에서 반드시 지켜야 하는 규칙을 문장으로 작성한다.
```

## 2. Entity 찾기

요구사항의 명사와 업무 사건에서 관리 대상을 찾는다.

```text
명사 후보
→ 회원, 주문, 상품

업무 사건
→ 주문 항목, 결제, 배송
```

모든 명사가 entity가 되는 것은 아니다.

Entity 후보 판단 질문:

- 독립적으로 식별해야 하는가?
- 여러 instance가 존재하는가?
- 별도의 속성을 가지는가?
- 생성·변경·삭제 이력이 필요한가?
- 다른 대상과 관계를 가지는가?

## 3. Entity와 Table을 구분하기

Entity는 업무 개념이고 table은 이를 DBMS에 구현한 결과다.

```text
업무 Entity
→ 회원

논리 모델
→ Member

물리 Table
→ members
```

ERD 도구에서 box로 그렸다고 바로 실제 table이 되는 것은 아니다. 논리 모델 이후 DBMS에 맞는 type과 constraint를 정해야 한다.

## 4. Attribute 정의

Entity가 가져야 할 속성을 찾는다.

```text
Member
├── member_id
├── name
├── email
└── joined_at
```

Attribute를 정할 때 확인한다.

- 하나의 값인가?
- 필수인가 선택인가?
- 다른 값으로 계산 가능한가?
- 자주 변경되는가?
- 개인 정보인가?
- 값의 범위와 길이는 무엇인가?

### Attribute 종류

- **Simple Attribute**: 더 나누지 않고 사용하는 값
- **Composite Attribute**: 여러 부분으로 나눌 수 있는 값
- **Single-valued Attribute**: 한 entity가 한 값을 가짐
- **Multi-valued Attribute**: 한 entity가 여러 값을 가짐
- **Derived Attribute**: 다른 값으로 계산 가능
- **Stored Attribute**: 실제로 저장하는 값

예를 들어 나이는 생년월일에서 계산할 수 있으므로 저장할 경우 시간이 지나면서 틀릴 수 있다.

## 5. Identifier와 Key 결정

각 entity instance를 구분할 수 있는 key를 정한다.

```text
Member
→ member_id

Order
→ order_id

Product
→ product_id
```

자연 key와 surrogate key를 비교한다.

```text
자연 Key
→ 이메일, 사업자번호처럼 업무 의미가 있음

대체 Key
→ BIGINT ID, UUID처럼 식별을 위해 생성
```

이메일은 변경될 수 있으므로 PK보다 `UNIQUE` 업무 key로 두는 설계가 흔하다.

## 6. Relationship 찾기

요구사항의 동사를 확인한다.

```text
회원이 주문한다.
주문이 상품을 포함한다.
상품이 category에 속한다.
```

각 관계에 대해 두 방향으로 질문한다.

```text
회원 한 명은 주문을 몇 개까지 가질 수 있는가?
주문 하나는 회원 몇 명에게 속하는가?
```

이 답으로 1:1, 1:N, N:M을 결정한다.

## 7. Cardinality 결정

Cardinality는 상대 entity와 연결될 수 있는 최대 개수를 나타낸다.

```text
1:1
학생 ↔ 학생증

1:N
회원 → 주문

N:M
학생 ↔ 강좌
```

N:M은 실제 관계형 schema에서 junction table로 구현한다.

## 8. Optionality 결정

Optionality는 관계 참여의 최소 개수를 나타낸다.

```text
0
→ 없어도 됨

1
→ 반드시 있어야 함
```

예:

```text
회원은 주문이 없어도 된다.
Member → Order: 0..N

주문은 반드시 한 회원에게 속한다.
Order → Member: 1
```

Optionality는 물리 schema에서 `NULL`, `NOT NULL`, FK 등의 결정으로 연결된다.

## 9. N:M 관계 해소

```text
Student N ── M Course
```

중간 entity를 만든다.

```text
Student 1 ── N Enrollment N ── 1 Course
```

```sql
CREATE TABLE enrollments (
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    enrolled_at TIMESTAMP NOT NULL,
    score DECIMAL(5, 2),
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

## 10. 정규화 검토

다음 문제가 있는지 확인한다.

- 한 column에 여러 값이 들어가는가?
- 복합 PK 일부에만 의존하는 속성이 있는가?
- 일반 column이 다른 일반 column을 결정하는가?
- 같은 정보가 많은 row에 반복되는가?

[관계 구현과 정규화 상세 문서](relationship-and-normalization.md)

## 11. 삭제와 변경 규칙 결정

부모를 삭제할 때 자식을 어떻게 할지 정한다.

- `CASCADE`
- `SET NULL`
- `RESTRICT`
- `NO ACTION`
- Soft Delete

이 결정은 DBMS 문법보다 업무 생명주기를 먼저 본다.

## 12. 물리 모델로 변환

논리 ERD가 끝나면 DBMS에 맞춰 다음을 정한다.

- 실제 table·column 이름
- data type
- PK·FK·UNIQUE·CHECK
- index
- partition
- ID 생성 방식
- schema와 권한

MySQL, PostgreSQL, Oracle에서는 type과 ID 생성, schema 계층이 다를 수 있다.

## 13. 실제 업무 시나리오로 검증

ERD를 다음 작업에 대입한다.

```text
신규 회원 가입
이메일 변경
주문 생성
상품 가격 변경
주문 취소
회원 탈퇴
상품 삭제
```

확인할 질문:

- 주문 후 상품 가격이 바뀌면 과거 주문 금액이 달라지는가?
- 회원을 삭제하면 주문 이력도 사라지는가?
- 같은 이메일로 동시에 가입하면 중복을 막는가?
- 주문 항목 없이 주문을 생성할 수 있는가?

## ERD 작성 최종 순서

```text
1. 요구사항 문장 작성
2. Entity 후보 추출
3. Attribute 정의
4. Identifier와 Key 결정
5. Relationship 발견
6. Cardinality 결정
7. Optionality 결정
8. N:M 관계 해소
9. 정규화 검토
10. 삭제·변경 정책 결정
11. 물리 type·constraint·index 결정
12. 업무 시나리오로 검증
```

