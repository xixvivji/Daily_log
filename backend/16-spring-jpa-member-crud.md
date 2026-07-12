# 16. Spring Data JPA 회원 CRUD 실전 구조

## 이 예제로 연결할 개념

회원 CRUD는 Spring 백엔드의 기본 구성 요소가 실제로 어떻게 협력하는지 확인하기 좋은 예제다.

```text
HTTP와 JSON
→ Controller와 DTO

비즈니스 규칙과 작업 단위
→ Service와 Transaction

데이터 조회와 저장
→ Repository

도메인 상태와 DB mapping
→ Entity

실제 schema
→ Migration SQL
```

단순히 파일을 계층별로 나누는 것이 목적은 아니다. 각 파일이 왜 존재하고 어떤 변경 이유를 담당하는지를 이해해야 한다.

## 전체 요청 흐름

```text
Frontend
→ POST /api/members + JSON
→ MemberController
→ MemberCreateRequest
→ MemberService
→ PasswordEncoder
→ Member Entity 생성
→ MemberRepository.save
→ JPA / Hibernate
→ INSERT SQL
→ Database
→ MemberResponse
→ JSON response
```

조회 응답은 반대 방향으로 돌아온다.

```text
Database row
→ JPA가 Member Entity로 mapping
→ Service가 MemberResponse로 변환
→ Jackson이 JSON으로 직렬화
→ Frontend
```

## 권장 Package 구조

```text
src/main/java/com/example/app/
├─ AppApplication.java
├─ member/
│  ├─ controller/
│  │  └─ MemberController.java
│  ├─ service/
│  │  └─ MemberService.java
│  ├─ repository/
│  │  └─ MemberRepository.java
│  ├─ domain/
│  │  ├─ Member.java
│  │  └─ MemberStatus.java
│  ├─ dto/
│  │  ├─ MemberCreateRequest.java
│  │  ├─ MemberUpdateRequest.java
│  │  └─ MemberResponse.java
│  └─ exception/
│     ├─ DuplicateEmailException.java
│     └─ MemberNotFoundException.java
└─ global/
   └─ error/
      ├─ ErrorResponse.java
      └─ GlobalExceptionHandler.java

src/main/resources/
├─ application.yml
└─ db/migration/
   └─ V1__create_members.sql

src/test/java/com/example/app/
├─ member/service/MemberServiceTest.java
├─ member/repository/MemberRepositoryTest.java
└─ member/controller/MemberControllerTest.java
```

최상위 package를 `controller`, `service`, `repository`로만 나누기보다 `member`, `order`, `payment` 같은 기능을 먼저 나누면 회원 기능 변경에 필요한 파일을 찾기 쉽다.

## API 계약

```text
POST   /api/members       → 회원 생성
GET    /api/members/{id}  → 회원 한 명 조회
GET    /api/members       → 회원 목록 조회
PATCH  /api/members/{id}  → 회원 일부 수정
DELETE /api/members/{id}  → 회원 삭제
```

예상 상태 코드:

```text
생성 성공          → 201 Created
조회·수정 성공     → 200 OK
삭제 성공          → 204 No Content
입력 형식 오류     → 400 Bad Request
회원을 찾지 못함   → 404 Not Found
email 중복         → 409 Conflict
예상하지 못한 오류 → 500 Internal Server Error
```

## MemberStatus

```java
package com.example.app.member.domain;

public enum MemberStatus {
    ACTIVE,
    INACTIVE
}
```

상태를 문자열로 두면 `ACTVE` 같은 잘못된 값이 들어갈 수 있다. enum은 허용되는 상태를 코드에 명확히 표현한다.

## Member Entity

```java
package com.example.app.member.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import java.time.LocalDateTime;

@Entity
@Table(name = "members")
public class Member {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(name = "password_hash", nullable = false, length = 100)
    private String passwordHash;

    @Column(nullable = false, length = 30)
    private String nickname;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MemberStatus status;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Version
    private Long version;

    protected Member() {
    }

    private Member(String email, String passwordHash, String nickname) {
        validateNickname(nickname);
        this.email = email;
        this.passwordHash = passwordHash;
        this.nickname = nickname;
        this.status = MemberStatus.ACTIVE;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = this.createdAt;
    }

    public static Member create(
        String email,
        String passwordHash,
        String nickname
    ) {
        return new Member(email, passwordHash, nickname);
    }

    public void changeNickname(String nickname) {
        validateNickname(nickname);
        this.nickname = nickname;
        this.updatedAt = LocalDateTime.now();
    }

    public void deactivate() {
        if (this.status == MemberStatus.INACTIVE) {
            return;
        }
        this.status = MemberStatus.INACTIVE;
        this.updatedAt = LocalDateTime.now();
    }

    private static void validateNickname(String nickname) {
        if (nickname == null || nickname.isBlank()) {
            throw new IllegalArgumentException("nickname is required");
        }
    }

    public Long getId() {
        return id;
    }

    public String getEmail() {
        return email;
    }

    public String getNickname() {
        return nickname;
    }

    public MemberStatus getStatus() {
        return status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
```

Entity의 역할:

```text
DB table과 field mapping
도메인 상태 보관
유효한 상태 변경 method 제공
JPA persistence context의 관리 대상
```

`Member`가 DB 자체를 만드는 것은 아니다. Entity는 table과의 mapping 정보를 제공하고, 설정에 따라 Hibernate가 이 정보를 이용해 DDL을 만들 수 있다. 운영 schema는 별도 migration으로 관리하는 것이 좋다.

비밀번호 원문은 Entity와 DB에 저장하지 않는다. Service에서 `PasswordEncoder`로 hash한 값만 전달한다.

## DTO는 Entity가 아니다

DTO는 API가 외부와 주고받을 데이터 계약이다.

```java
package com.example.app.member.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record MemberCreateRequest(
    @NotBlank
    @Email
    String email,

    @NotBlank
    @Size(min = 8, max = 64)
    String password,

    @NotBlank
    @Size(max = 30)
    String nickname
) {
}
```

```java
package com.example.app.member.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record MemberUpdateRequest(
    @NotBlank
    @Size(max = 30)
    String nickname
) {
}
```

```java
package com.example.app.member.dto;

import com.example.app.member.domain.Member;
import com.example.app.member.domain.MemberStatus;
import java.time.LocalDateTime;

public record MemberResponse(
    Long id,
    String email,
    String nickname,
    MemberStatus status,
    LocalDateTime createdAt
) {
    public static MemberResponse from(Member member) {
        return new MemberResponse(
            member.getId(),
            member.getEmail(),
            member.getNickname(),
            member.getStatus(),
            member.getCreatedAt()
        );
    }
}
```

Entity와 DTO 차이:

```text
Entity
→ 내부 DB·domain model
→ JPA가 관리
→ transaction 안에서 변경 감지
→ relation과 persistence 규칙 포함 가능

DTO
→ 외부 API contract
→ JSON 직렬화·역직렬화 대상
→ 필요한 값만 노출
→ JPA가 관리하지 않음
```

DTO가 frontend 내부 객체와 완전히 같아야 하는 것은 아니다. 백엔드가 제공하는 안정적인 API 계약이고 frontend는 그 계약을 사용한다.

## MemberRepository

```java
package com.example.app.member.repository;

import com.example.app.member.domain.Member;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MemberRepository extends JpaRepository<Member, Long> {
    boolean existsByEmail(String email);
    Optional<Member> findByEmail(String email);
}
```

`JpaRepository<Member, Long>`에서 첫 번째 타입은 관리할 Entity, 두 번째는 ID 타입이다.

기본 제공 method:

```text
save
findById
findAll
delete
deleteById
existsById
count
```

Repository는 DB 접근 책임을 가진다. 비밀번호 정책이나 회원 상태 변경 같은 비즈니스 규칙을 Repository에 넣지 않는다.

## MemberService

```java
package com.example.app.member.service;

import com.example.app.member.domain.Member;
import com.example.app.member.dto.MemberCreateRequest;
import com.example.app.member.dto.MemberResponse;
import com.example.app.member.dto.MemberUpdateRequest;
import com.example.app.member.exception.DuplicateEmailException;
import com.example.app.member.exception.MemberNotFoundException;
import com.example.app.member.repository.MemberRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class MemberService {

    private final MemberRepository memberRepository;
    private final PasswordEncoder passwordEncoder;

    public MemberService(
        MemberRepository memberRepository,
        PasswordEncoder passwordEncoder
    ) {
        this.memberRepository = memberRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public MemberResponse create(MemberCreateRequest request) {
        if (memberRepository.existsByEmail(request.email())) {
            throw new DuplicateEmailException(request.email());
        }

        String passwordHash = passwordEncoder.encode(request.password());
        Member member = Member.create(
            request.email(),
            passwordHash,
            request.nickname()
        );

        Member savedMember = memberRepository.save(member);
        return MemberResponse.from(savedMember);
    }

    public MemberResponse findById(Long id) {
        return MemberResponse.from(getMember(id));
    }

    public Page<MemberResponse> findAll(Pageable pageable) {
        return memberRepository.findAll(pageable)
            .map(MemberResponse::from);
    }

    @Transactional
    public MemberResponse update(Long id, MemberUpdateRequest request) {
        Member member = getMember(id);
        member.changeNickname(request.nickname());
        return MemberResponse.from(member);
    }

    @Transactional
    public void delete(Long id) {
        Member member = getMember(id);
        memberRepository.delete(member);
    }

    private Member getMember(Long id) {
        return memberRepository.findById(id)
            .orElseThrow(() -> new MemberNotFoundException(id));
    }
}
```

Service의 역할:

```text
하나의 use case 순서 조율
중복 email 같은 비즈니스 조건 확인
비밀번호 hash 처리
transaction 경계 설정
Entity와 DTO 변환
```

`update()`에서 `save()`를 다시 호출하지 않아도 transaction 안의 영속 Entity 변경을 JPA가 감지해 `UPDATE` SQL을 실행한다. 새 Entity를 저장하는 `create()`에서는 `save()`가 필요하다.

사전 중복 조회만으로 동시 요청을 완전히 막을 수는 없다. DB에도 email unique constraint를 두고 constraint 위반 예외를 변환해야 한다.

## MemberController

```java
package com.example.app.member.controller;

import com.example.app.member.dto.MemberCreateRequest;
import com.example.app.member.dto.MemberResponse;
import com.example.app.member.dto.MemberUpdateRequest;
import com.example.app.member.service.MemberService;
import jakarta.validation.Valid;
import java.net.URI;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/members")
public class MemberController {

    private final MemberService memberService;

    public MemberController(MemberService memberService) {
        this.memberService = memberService;
    }

    @PostMapping
    public ResponseEntity<MemberResponse> create(
        @Valid @RequestBody MemberCreateRequest request
    ) {
        MemberResponse response = memberService.create(request);
        URI location = URI.create("/api/members/" + response.id());
        return ResponseEntity.created(location).body(response);
    }

    @GetMapping("/{id}")
    public MemberResponse findById(@PathVariable Long id) {
        return memberService.findById(id);
    }

    @GetMapping
    public Page<MemberResponse> findAll(Pageable pageable) {
        return memberService.findAll(pageable);
    }

    @PatchMapping("/{id}")
    public MemberResponse update(
        @PathVariable Long id,
        @Valid @RequestBody MemberUpdateRequest request
    ) {
        return memberService.update(id, request);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        memberService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

Controller는 HTTP adapter다.

```text
URL과 HTTP method mapping
JSON body를 DTO로 변환
형식 validation 실행
Service 호출
상태 코드와 response body 구성
```

Controller가 `MemberRepository`를 직접 호출하거나 비밀번호를 hash하기 시작하면 HTTP 책임과 비즈니스 작업이 섞인다.

## Exception

```java
package com.example.app.member.exception;

public class MemberNotFoundException extends RuntimeException {
    public MemberNotFoundException(Long id) {
        super("member not found: " + id);
    }
}
```

```java
package com.example.app.member.exception;

public class DuplicateEmailException extends RuntimeException {
    public DuplicateEmailException(String email) {
        super("email already exists: " + email);
    }
}
```

실제 운영 log에 email을 남겨도 되는지는 개인정보 logging 정책을 확인해야 한다.

## 공통 Error Response

```java
package com.example.app.global.error;

import java.util.List;

public record ErrorResponse(
    String code,
    String message,
    List<FieldError> errors
) {
    public record FieldError(String field, String reason) {
    }

    public static ErrorResponse of(String code, String message) {
        return new ErrorResponse(code, message, List.of());
    }
}
```

```java
package com.example.app.global.error;

import com.example.app.member.exception.DuplicateEmailException;
import com.example.app.member.exception.MemberNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MemberNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(
        MemberNotFoundException exception
    ) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ErrorResponse.of("MEMBER_NOT_FOUND", exception.getMessage()));
    }

    @ExceptionHandler(DuplicateEmailException.class)
    public ResponseEntity<ErrorResponse> handleDuplicateEmail(
        DuplicateEmailException exception
    ) {
        return ResponseEntity.status(HttpStatus.CONFLICT)
            .body(ErrorResponse.of("DUPLICATE_EMAIL", exception.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(
        MethodArgumentNotValidException exception
    ) {
        var errors = exception.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> new ErrorResponse.FieldError(
                error.getField(),
                error.getDefaultMessage()
            ))
            .toList();

        return ResponseEntity.badRequest().body(
            new ErrorResponse(
                "INVALID_REQUEST",
                "요청 값이 올바르지 않습니다.",
                errors
            )
        );
    }
}
```

처리하지 않은 예외는 공통 `500` handler에서 내부 원인을 log로 남기고, 클라이언트에는 일반화된 메시지만 반환한다.

## PasswordEncoder Bean

```java
@Configuration
public class SecurityConfig {

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

같은 비밀번호를 BCrypt로 여러 번 encode하면 salt 때문에 서로 다른 hash가 나오는 것이 정상이다. 로그인에서는 문자열끼리 직접 비교하지 않고 `passwordEncoder.matches(rawPassword, passwordHash)`를 사용한다.

## Migration SQL

```sql
CREATE TABLE members (
    id BIGINT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    nickname VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    version BIGINT NOT NULL DEFAULT 0,
    CONSTRAINT pk_members PRIMARY KEY (id),
    CONSTRAINT uk_members_email UNIQUE (email)
);
```

Entity annotation과 migration SQL은 서로 일치해야 한다.

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate
```

`validate`는 Entity를 기준으로 table을 생성하지 않고 mapping과 schema가 맞는지 확인한다. local 실습에서는 `create`나 `create-drop`을 사용할 수 있지만 운영 변경 이력은 Flyway나 Liquibase로 관리한다.

## Service Test 핵심 예시

```java
@Test
void createMember() {
    when(memberRepository.existsByEmail("a@test.com")).thenReturn(false);
    when(passwordEncoder.encode("password123")).thenReturn("encoded");
    when(memberRepository.save(any(Member.class)))
        .thenAnswer(invocation -> invocation.getArgument(0));

    MemberResponse response = memberService.create(
        new MemberCreateRequest("a@test.com", "password123", "jiwon")
    );

    assertThat(response.email()).isEqualTo("a@test.com");
    verify(passwordEncoder).encode("password123");
    verify(memberRepository).save(any(Member.class));
}
```

ID는 JPA가 실제 저장할 때 생성되므로 순수 mock test에서 ID까지 검증하려면 fixture나 별도 test helper가 필요하다. Entity mapping과 식별자 생성은 Repository integration test에서 검증하는 편이 자연스럽다.

## Repository Test 핵심 예시

```java
@DataJpaTest
class MemberRepositoryTest {

    @Autowired MemberRepository memberRepository;

    @Test
    void findByEmail() {
        Member member = Member.create("a@test.com", "hash", "jiwon");
        memberRepository.saveAndFlush(member);

        Member found = memberRepository.findByEmail("a@test.com")
            .orElseThrow();

        assertThat(found.getNickname()).isEqualTo("jiwon");
    }
}
```

실제 운영 DB와 같은 DB를 Testcontainers로 실행하면 H2와의 SQL·constraint 차이 때문에 놓치는 문제를 줄일 수 있다.

## Controller Test 핵심 예시

```java
mockMvc.perform(post("/api/members")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
            {
              "email": "invalid-email",
              "password": "short",
              "nickname": ""
            }
            """))
    .andExpect(status().isBadRequest())
    .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));
```

Controller test는 JSON binding, validation, 상태 코드와 오류 형식을 확인한다. Service의 내부 저장 로직은 Service와 Repository test에서 확인한다.

## 물리 삭제와 논리 삭제

예제의 `delete()`는 DB row를 실제로 삭제한다.

```text
물리 삭제
→ row 제거
→ 단순하지만 복구와 감사가 어려움

논리 삭제
→ status 또는 deletedAt 변경
→ 기록 유지 가능
→ 모든 조회에서 삭제된 데이터 제외 필요
```

회원은 주문, 결제, 감사 기록과 연결될 수 있어 실제 서비스에서는 탈퇴 상태로 바꾸고 개인정보를 별도 정책에 따라 파기하는 경우가 많다. 법적 보존 의무와 개인정보 삭제 의무를 함께 검토해야 한다.

회원에게 `USER`, `ADMIN` 같은 역할을 추가할 때 단일 column으로 시작할지 Role과 연결 table을 만들지는 요구사항에 따라 달라진다. 세 가지 구현과 migration 방법은 [회원, 역할, 관리자 권한 모델링](25-member-role-admin-authorization-model.md)에서 다룬다.

## 흔한 실수

```text
Entity를 @RequestBody로 직접 받음
Entity를 그대로 JSON 응답으로 반환
Controller가 Repository를 직접 호출
비밀번호 원문 저장 또는 응답 노출
수정할 때마다 의미 없이 save 호출
DB unique constraint 없이 사전 중복 조회만 사용
모든 Entity relation을 EAGER로 설정
transaction 밖에서 lazy relation 접근
ddl-auto=update를 운영 schema 관리 수단으로 사용
예외별 HTTP 상태를 구분하지 않고 모두 500 반환
목록 API에 pagination을 적용하지 않음
```

## 직접 설명할 때 핵심 문장

```text
Controller는 HTTP 요청과 JSON을 DTO로 받아 Service에 전달한다.
Service는 하나의 회원 use case와 transaction을 조율하고 Entity를 생성하거나 변경한다.
Repository는 JPA를 통해 Entity를 DB에 저장하고 조회한다.
Entity는 DB table과 mapping되는 내부 domain 객체이고 DTO는 외부 API의 요청·응답 계약이므로 서로 다르다.
JPA Entity가 DB 자체는 아니며, 운영 table은 migration으로 관리하고 Entity와 schema의 일치 여부를 검증한다.
```
