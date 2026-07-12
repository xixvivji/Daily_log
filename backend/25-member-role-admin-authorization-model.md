# 25. 회원, 역할, 관리자 권한 모델링

## 핵심 질문

회원과 관리자를 구분할 때 먼저 다음 질문에 답해야 한다.

```text
회원 한 명이 역할 하나만 가지는가?
한 명이 여러 운영 역할을 동시에 가질 수 있는가?
역할과 세부 권한을 runtime에 변경해야 하는가?
관리자에게만 존재하는 업무 정보가 있는가?
관리자 인증 정책이 일반 회원과 완전히 다른가?
권한 부여자, 시각, 만료일을 기록해야 하는가?
```

회원 수보다 역할의 복잡도, 관리자 정보, 보안 경계가 구조 선택에 더 큰 영향을 준다.

## 역할과 관리자 정보는 다르다

```text
Role 또는 Authority
→ 무엇을 할 수 있는가?

AdminProfile
→ 사번, 부서, 승인 상태 등 관리자가 어떤 사람인가?

독립 Admin 계정
→ 일반 회원과 다른 인증 주체인가?
```

`AdminProfile`이 존재한다고 자동으로 관리자 권한이 생기는 것으로 처리하면 데이터 불일치가 보안 문제로 이어질 수 있다. 인가는 Role 또는 Authority를 기준으로 하고, profile은 관리자 업무 정보를 표현한다.

## 1. Member에 Role 컬럼 추가

가장 단순한 구조다.

```text
member
──────────────────
id
email
password
role
```

```java
public enum MemberRole {
    USER,
    ADMIN
}
```

```java
@Entity
@Table(name = "member")
public class Member {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String password;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private MemberRole role;
}
```

`EnumType.ORDINAL`은 enum 선언 순서가 DB 의미가 되므로 피한다. 문자열 저장은 공간을 조금 더 사용하지만 데이터 의미와 migration이 명확하다.

### 단일 컬럼 방식의 장점

```text
schema와 code가 단순함
권한 조회 JOIN이 없음
USER와 ADMIN만 있으면 충분함
role 값에 NOT NULL과 CHECK 제약 적용 가능
```

### 단일 컬럼 방식의 한계

```text
한 회원에게 역할 하나만 부여 가능
새 역할 추가에 code 변경과 배포가 필요할 수 있음
부여 시각, 부여자, 만료일 기록이 어려움
Permission 단위의 세밀한 권한 관리에 부적합
```

### 적합한 상황

```text
USER와 ADMIN만 존재
모든 관리자가 같은 기능 사용
역할이 자주 바뀌지 않음
한 계정이 여러 역할을 가질 필요 없음
```

회원이 많다는 이유만으로 Role table이 필요한 것은 아니다. 회원이 천만 명이어도 역할이 두 개이고 단일 역할 규칙이 유지되면 컬럼 방식은 유효하다.

## 2. Role과 MemberRole 분리

역할을 독립 데이터로 관리하고 회원과 연결한다.

회원이 역할 하나만 가진다면 `member.role_id` 외래 키로도 구성할 수 있다.

```text
member N:1 role
```

한 회원이 여러 역할을 가질 수 있다면 연결 table이 필요하다.

```text
member 1:N member_role N:1 role
```

```sql
CREATE TABLE role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE member_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    member_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    granted_at TIMESTAMP NOT NULL,
    granted_by BIGINT NULL,
    expires_at TIMESTAMP NULL,
    CONSTRAINT fk_member_role_member
        FOREIGN KEY (member_id) REFERENCES member(id),
    CONSTRAINT fk_member_role_role
        FOREIGN KEY (role_id) REFERENCES role(id),
    CONSTRAINT uk_member_role UNIQUE (member_id, role_id)
);
```

### 직접 ManyToMany를 피하는 이유

```java
@ManyToMany
private Set<Role> roles;
```

단순 연결만 필요하면 동작하지만, 실제 운영에서는 다음 정보가 필요해질 수 있다.

```text
누가 권한을 부여했는가?
언제 부여했는가?
언제 만료되는가?
왜 부여했는가?
회수 상태와 이력은 무엇인가?
```

따라서 `MemberRole`을 연결 Entity로 만드는 편이 변경에 강하다.

```java
@Entity
@Table(
    name = "member_role",
    uniqueConstraints = @UniqueConstraint(
        name = "uk_member_role",
        columnNames = {"member_id", "role_id"}
    )
)
public class MemberRoleAssignment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "member_id", nullable = false)
    private Member member;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "role_id", nullable = false)
    private Role role;

    @Column(nullable = false)
    private LocalDateTime grantedAt;

    private LocalDateTime expiresAt;
}
```

```java
@Entity
@Table(name = "role")
public class Role {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 50)
    private String name;
}
```

### Role 분리의 장점

```text
한 회원에게 여러 역할 부여 가능
역할 부여 metadata와 감사 이력 관리 가능
운영 화면에서 역할 부여와 회수 가능
Role-Permission 기반 RBAC로 확장 가능
```

### Role 분리의 비용

```text
table과 JOIN 증가
권한 조회 query와 cache 전략 필요
JPA N+1과 LazyInitialization 주의
role 이름 변경이 application 정책과 어긋날 수 있음
```

역할을 로그인할 때 한 번 조회하여 `Authentication`에 넣는 구조라면 매 API마다 Role table을 다시 조회할 필요는 없다. 반대로 권한 회수를 즉시 반영해야 하면 session 또는 token 무효화 정책까지 설계해야 한다.

## 3. Admin 또는 AdminProfile 분리

두 가지 형태를 구분해야 한다.

### 독립 Admin 계정

```text
member
admin
```

일반 회원과 관리자가 별개의 인증 주체다.

적합한 예:

```text
관리자 계정은 회사가 발급
MFA 필수
사내 VPN 또는 IP 제한
관리자 session 만료 시간이 더 짧음
퇴사와 계정 폐기 절차가 회원과 다름
```

장점:

```text
보안 경계와 계정 생명주기 분리
관리자 인증 정책을 독립적으로 적용
관리자 endpoint와 audit 정책을 명확히 분리
```

단점:

```text
email, password, status 같은 공통 정보 중복
인증과 계정 잠금 code 중복 가능
한 사람이 회원과 관리자 계정을 각각 관리해야 할 수 있음
```

### AdminProfile 확장 정보

인증 주체는 Member 하나로 유지하고 관리자 전용 정보만 분리한다.

```text
Member 1 : 0..1 AdminProfile
```

```java
@Entity
@Table(name = "admin_profile")
public class AdminProfile {

    @Id
    private Long memberId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "member_id")
    private Member member;

    @Column(nullable = false, unique = true)
    private String employeeNumber;

    @Column(nullable = false)
    private String department;

    private LocalDateTime approvedAt;
}
```

이 구조는 다음처럼 함께 사용할 수 있다.

```text
Member + MemberRole + Role
→ 인가

Member + AdminProfile
→ 관리자 업무 정보
```

관리자 등록 시 Role과 AdminProfile을 같은 transaction에서 만들고, 둘의 불일치를 탐지하는 운영 검증도 두는 것이 좋다.

## 4. RBAC와 Permission

RBAC는 사용자에게 Permission을 하나씩 직접 주기보다 Role을 통해 권한 묶음을 부여한다.

```text
Member
→ MemberRole
→ Role
→ RolePermission
→ Permission
```

예:

```text
ORDER_MANAGER
→ ORDER_READ
→ ORDER_CANCEL

CS_MANAGER
→ MEMBER_READ
→ REFUND_REQUEST
```

Role은 업무 책임의 묶음이고 Permission은 실제 행위다.

```text
Role: ORDER_MANAGER
Permission: ORDER_CANCEL
```

모든 endpoint를 DB Permission 문자열과 동적으로 연결하면 운영 유연성은 높지만, 오타와 과도한 복잡성이 생길 수 있다. 역할이 몇 개뿐이면 code 기반 policy가 더 명확할 수 있다.

## 5. Spring Security 연결

Spring Security의 `GrantedAuthority`는 인증된 principal이 가진 고수준 권한을 표현한다. Role과 scope도 authority로 변환된다.

```java
List<GrantedAuthority> authorities = member.getRoleAssignments().stream()
    .filter(MemberRoleAssignment::isActive)
    .map(MemberRoleAssignment::getRole)
    .map(Role::getName)
    .map(name -> new SimpleGrantedAuthority("ROLE_" + name))
    .toList();
```

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteMember(Long memberId) {
}
```

```java
@PreAuthorize("hasAuthority('ORDER_CANCEL')")
public void cancelOrder(Long orderId) {
}
```

`hasRole("ADMIN")`은 일반적으로 `ROLE_ADMIN` authority를 확인한다. prefix를 중복해서 `hasRole("ROLE_ADMIN")`로 작성하지 않도록 팀 규칙을 통일한다.

인가를 Controller에만 두면 내부 Service 호출이나 다른 진입점에서 우회될 수 있다. URL 규칙과 Service method authorization을 방어적으로 함께 사용할 수 있다.

## 6. 단일 컬럼에서 Role Table로 Migration

운영 중에는 한 번에 column을 제거하지 않고 Expand-Migrate-Contract 순서로 변경한다.

### Expand 단계

```text
member.role 유지
role table 추가
member_role table 추가
새 application이 두 schema를 이해하도록 배포
```

### Migrate 단계

```sql
INSERT INTO role (name) VALUES ('USER'), ('ADMIN');

INSERT INTO member_role (member_id, role_id, granted_at)
SELECT m.id, r.id, CURRENT_TIMESTAMP
FROM member m
JOIN role r ON r.name = m.role;
```

검증 예:

```sql
SELECT COUNT(*) FROM member;
SELECT COUNT(DISTINCT member_id) FROM member_role;
```

일정 기간 기존 column과 새 table에 같은 transaction으로 기록한 뒤 새 table read로 전환할 수 있다. dual write는 한쪽만 성공하지 않도록 transaction 경계를 명확히 해야 한다.

### Contract 단계

새 구조가 안정적으로 동작하고 이전 application version으로 rollback할 필요가 없어진 뒤 기존 column을 제거한다.

```sql
ALTER TABLE member DROP COLUMN role;
```

DB migration은 Flyway 또는 Liquibase로 version 관리한다.

## 7. API 계약의 확장성

DB가 단일 role column이어도 외부 계약을 배열로 설계할 수 있다.

```json
{
  "memberId": 10,
  "roles": ["ADMIN"]
}
```

나중에 다중 역할로 바뀌어도 response 형태를 유지할 수 있다. 하지만 실제 요구도 없는데 모든 내부 code를 collection으로 만들 필요는 없다. 변경 가능성이 큰 외부 계약과 내부 구현 복잡도를 따로 판단한다.

## 8. 권한 변경과 Token

Session 방식은 server의 SecurityContext 또는 session을 무효화해 권한 변경을 반영할 수 있다.

JWT에 Role을 넣으면 token 만료 전까지 이전 권한이 남을 수 있다.

```text
짧은 access token 만료
refresh 시 최신 Role 조회
권한 version claim 확인
중요한 작업은 DB에서 현재 권한 재검증
```

권한을 DB table로 분리했다고 자동으로 즉시 반영되는 것은 아니다. 인증 상태를 어디에 cache하는지도 함께 설계해야 한다.

## 9. Test해야 할 내용

```text
일반 회원은 관리자 API에 접근할 수 없음
ADMIN은 필요한 API에 접근 가능
만료된 MemberRole은 authority로 변환되지 않음
중복 역할 부여는 unique constraint로 차단
권한 회수 후 session/token 정책대로 반영
AdminProfile만 있고 ADMIN Role이 없는 불일치 탐지
마이그레이션 전후 회원별 역할 수 일치
```

보안 테스트는 정상 접근뿐 아니라 거부되는 경로를 반드시 포함한다.

## 10. 선택 기준

| 상황 | 권장 구조 |
| --- | --- |
| USER와 ADMIN만 있고 역할 하나만 가짐 | `Member.role` enum column |
| 역할 하나지만 DB에서 관리해야 함 | `Member N:1 Role` |
| 한 회원이 여러 역할을 가짐 | `Member + MemberRole + Role` |
| 세부 행위 권한이 필요함 | `Role + RolePermission + Permission` |
| 관리자 전용 정보가 많음 | `AdminProfile` 추가 |
| 관리자 인증 경계가 완전히 다름 | 독립 `Admin` 계정 검토 |

처음부터 가장 복잡한 모델을 선택하는 것이 정답은 아니다. 가까운 요구가 분명하면 미리 분리하고, 불확실하면 단일 column으로 시작하되 권한 판단을 여러 Service에 흩뿌리지 않는다.

## 흔한 실수

```text
MemberRole enum 이름과 JPA 연결 Entity 이름을 구분하지 않음
AdminProfile 존재 여부만으로 관리자 권한 판단
Entity 여러 곳에서 role을 직접 비교
권한 변경 후 기존 JWT가 계속 유효한 문제를 무시
ManyToMany로 시작한 뒤 부여 metadata를 넣지 못함
role column을 즉시 삭제해 rollback 경로를 없앰
```

## 공식 참고 자료

- [Spring Security Authentication Architecture](https://docs.spring.io/spring-security/reference/servlet/authentication/architecture.html)
- [Spring Security Authorization Architecture](https://docs.spring.io/spring-security/reference/servlet/authorization/architecture.html)
- [Spring Security Method Security](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)

## 설명할 때 핵심 문장

회원 수가 아니라 역할 조합, 관리자 정보, 보안 경계가 권한 schema를 결정한다. Role은 할 수 있는 일을 나타내고 AdminProfile은 관리자 정보를 나타내므로 목적이 다르다. 단일 role column에서 분리 table로 바꿀 때는 Expand-Migrate-Contract로 데이터와 code를 단계적으로 전환한다.
