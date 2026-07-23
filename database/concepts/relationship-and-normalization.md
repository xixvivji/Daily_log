# 관계 구현과 정규화

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## 전체 흐름

```text
업무에서 관계 발견
→ 1:1, 1:N, N:M 판단
→ PK·FK·UNIQUE로 구현
→ 부모 삭제·변경 정책 결정
→ 정규화로 중복과 데이터 이상 제거
```

## 관계 Relationship

Relationship은 table 사이의 업무적인 연결이다.

```text
학생이 학생증을 가진다.
회원이 주문한다.
학생이 강좌를 수강한다.
```

이 문장을 각각 1:1, 1:N, N:M 관계로 표현한다.

### 1:1 관계

한 row가 상대 table의 최대 한 row와 연결된다.

```text
학생 1명
↔ 학생증 최대 1개
```

```sql
CREATE TABLE student_cards (
    card_id BIGINT PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
);
```

FK에 `UNIQUE`가 없으면 같은 학생 번호를 가진 카드 row를 여러 개 만들 수 있으므로 실제로는 1:N이 된다.

### 1:N 관계

한 부모 row가 여러 자식 row와 연결된다.

```text
회원 1명
→ 주문 여러 개
```

N 쪽인 주문 table에 회원 FK를 둔다.

```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    FOREIGN KEY (member_id)
        REFERENCES members(member_id)
);
```

### N:M 관계

양쪽의 여러 row가 서로 연결된다.

```text
학생 여러 명
↔ 강좌 여러 개
```

관계형 DB에서는 junction table로 두 개의 1:N 관계로 바꾼다.

```sql
CREATE TABLE enrollments (
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    enrolled_at TIMESTAMP NOT NULL,
    score DECIMAL(5, 2),
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
```

`score`와 `enrolled_at`은 학생이나 강좌 하나의 속성이 아니라 수강 관계의 속성이다.

## 외래키 제약 조건 옵션 비교

부모 row를 삭제하거나 key를 변경할 때 자식 row를 어떻게 처리할지 정한다.

| 옵션 | 동작 | 예시 |
| --- | --- | --- |
| `ON DELETE CASCADE` | 부모 삭제 시 자식도 삭제 | 주문 삭제 시 주문 항목 삭제 |
| `ON DELETE SET NULL` | 자식 FK를 `NULL`로 변경 | 담당 직원 삭제 후 고객은 유지 |
| `ON DELETE RESTRICT` | 자식이 있으면 부모 삭제 차단 | 상품이 남은 category 삭제 금지 |
| `ON DELETE NO ACTION` | Constraint 검사 시점에 위반이면 실패 | 참조 중인 부모 삭제 차단 |
| `ON UPDATE CASCADE` | 부모 key 변경을 자식에게 전파 | 변경 가능한 자연 key |

### ON DELETE CASCADE

```sql
FOREIGN KEY (order_id)
REFERENCES orders(order_id)
ON DELETE CASCADE
```

부모와 자식의 생명주기가 완전히 같을 때 사용한다. 실수로 부모를 삭제하면 많은 자식도 삭제되므로 감사·법적 보존이 필요한 data에는 주의한다.

### ON DELETE SET NULL

```sql
FOREIGN KEY (manager_id)
REFERENCES employees(employee_id)
ON DELETE SET NULL
```

FK column이 nullable이어야 한다. 부모가 없어져도 자식이 독립적으로 의미를 가져야 한다.

### RESTRICT와 NO ACTION

둘 다 자식이 있는 부모 삭제를 차단하는 결과로 보일 수 있다.

```text
RESTRICT
→ 위반 작업을 즉시 제한

NO ACTION
→ Constraint 검사 시점에 위반이면 실패
```

PostgreSQL에서는 deferrable constraint 때문에 검사 시점 차이가 생길 수 있다. MySQL InnoDB에서는 `NO ACTION`이 사실상 `RESTRICT`처럼 동작한다.

### DBMS별 지원 차이

| 옵션 | MySQL InnoDB | PostgreSQL | Oracle | SQL Server |
| --- | --- | --- | --- | --- |
| `ON DELETE CASCADE` | 지원 | 지원 | 지원 | 지원 |
| `ON DELETE SET NULL` | 지원 | 지원 | 지원 | 지원 |
| `ON DELETE RESTRICT` | 지원 | 지원 | 기본 차단 동작 | `NO ACTION` 중심 |
| `ON DELETE NO ACTION` | RESTRICT와 유사 | 지연 검사 가능 | 기본 차단 동작 | 지원 |
| `ON UPDATE CASCADE` | 지원 | 지원 | 일반적인 FK 절에서 미지원 | 지원 |
| `SET DEFAULT` | 일반적으로 미지원 | 지원 | 일반적인 FK 절에서 미지원 | 지원 |

## 정규화 Normalization

정규화는 data 중복을 줄이고 삽입·삭제·수정 과정에서 모순이 생기는 문제를 줄이는 설계 과정이다.

### 삽입 이상

저장하고 싶은 정보 외의 불필요한 정보가 없으면 새 row를 저장할 수 없는 문제다.

### 삭제 이상

한 정보를 삭제했더니 보존해야 할 다른 정보까지 함께 사라지는 문제다.

### 갱신 이상

같은 값이 여러 row에 중복되어 일부만 수정되고 서로 다른 값이 남는 문제다.

## 제1정규형 1NF

한 column에 반복 목록을 넣지 않고 table이 다루는 하나의 값으로 표현한다.

```text
나쁜 예
subjects = "DB, Network, OS"

분리
Enrollment(student_id, course_id)
```

JSON과 array가 항상 1NF 위반인 것은 아니다. 내부 요소를 관계형 검색·JOIN·Constraint 대상으로 자주 사용한다면 별도 table이 더 적합할 수 있다.

## 제2정규형 2NF

복합 key 일부에만 의존하는 column을 분리한다.

```text
Enrollment(
    student_id,
    course_id,
    student_name,
    course_title,
    score
)

PK = (student_id, course_id)
```

```text
student_id → student_name
course_id → course_title
(student_id, course_id) → score
```

분리:

```text
Student(student_id, student_name)
Course(course_id, course_title)
Enrollment(student_id, course_id, score)
```

## 제3정규형 3NF

PK가 아닌 column이 다른 일반 column을 결정하는 이행 종속을 분리한다.

```text
Employee(
    employee_id,
    department_id,
    department_name
)
```

```text
employee_id → department_id
department_id → department_name
```

분리:

```text
Employee(employee_id, department_id)
Department(department_id, department_name)
```

## BCNF와 반정규화

BCNF는 모든 결정자가 후보 key가 되도록 요구하는 정규형이다.

반정규화는 정규화를 몰라서 중복한 것이 아니라, 측정된 읽기 병목을 줄이기 위해 의도적으로 중복을 도입하는 것이다.

반정규화할 때 결정할 내용:

- 어떤 table이 원본인가
- 중복 값을 언제 갱신하는가
- 갱신 실패 시 어떻게 복구하는가
- 쓰기 비용과 저장 공간이 얼마나 증가하는가

## 최종 확인

1. 1:1 관계에서 FK에 `UNIQUE`가 필요한 이유는 무엇인가?
2. N:M 관계를 junction table로 바꾸는 이유는 무엇인가?
3. `CASCADE`와 `SET NULL`은 자식의 생명주기가 어떻게 다른가?
4. 2NF가 주로 복합 key에서 문제가 되는 이유는 무엇인가?
5. 3NF의 이행 종속을 직접 설명할 수 있는가?
6. Oracle에서 `ON UPDATE CASCADE`가 필요하다면 schema를 어떻게 다시 설계할 수 있는가?

