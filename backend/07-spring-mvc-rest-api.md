# 07. Spring MVC와 REST API

## Spring MVC가 하는 일

Spring MVC는 HTTP 요청을 Java 메서드로 연결하고, Java 객체를 HTTP 응답으로 변환해준다.

흐름:

```text
Client
→ DispatcherServlet
→ HandlerMapping
→ Controller
→ Service
→ Repository
→ Response
```

핵심은 HTTP 세계와 Java 객체 세계를 연결하는 것이다.

## DispatcherServlet

DispatcherServlet은 Spring MVC의 front controller다.

모든 요청이 먼저 DispatcherServlet으로 들어온다.

역할:

```text
요청 받을 Controller 찾기
Controller 메서드 호출
요청 파라미터 바인딩
응답 변환
예외 처리 흐름 연결
```

## Controller

Controller는 HTTP 요청과 응답을 담당한다.

```java
@RestController
@RequestMapping("/api/members")
public class MemberController {
    private final MemberService memberService;

    public MemberController(MemberService memberService) {
        this.memberService = memberService;
    }

    @GetMapping("/{id}")
    public MemberResponse findById(@PathVariable Long id) {
        return memberService.findById(id);
    }
}
```

Controller에서 하지 말아야 할 것:

```text
복잡한 비즈니스 로직
DB 직접 접근
트랜잭션 세부 처리
외부 API 호출 로직 직접 구현
```

Controller는 HTTP adapter 역할에 집중한다.

## Request Mapping

자주 쓰는 매핑:

```text
@GetMapping
@PostMapping
@PutMapping
@PatchMapping
@DeleteMapping
```

HTTP method와 URL path를 Java 메서드에 연결한다.

```java
@PostMapping
public MemberResponse create(@RequestBody MemberCreateRequest request) {
    return memberService.create(request);
}
```

## Request Body와 Response Body

`@RequestBody`는 HTTP request body를 Java 객체로 변환한다.

```java
public MemberResponse create(@RequestBody MemberCreateRequest request)
```

Spring은 Jackson 같은 메시지 컨버터를 사용해 JSON을 객체로 변환한다.

응답 객체는 다시 JSON으로 변환된다.

```text
JSON request
→ Java DTO
→ Service 처리
→ Java DTO
→ JSON response
```

## DTO

DTO는 Data Transfer Object다.

요청/응답 데이터를 전달하기 위한 객체다.

Entity를 그대로 API 응답으로 노출하지 않는 것이 좋다.

이유:

```text
Entity 내부 구조가 API에 노출됨
API 변경과 DB 모델 변경이 강하게 묶임
불필요한 필드 노출 가능
순환 참조 문제 가능
```

## Validation

요청 값 검증은 `@Valid`와 Bean Validation을 사용한다.

```java
public record MemberCreateRequest(
    @NotBlank String email,
    @NotBlank String password
) {
}
```

```java
@PostMapping
public MemberResponse create(@Valid @RequestBody MemberCreateRequest request) {
    return memberService.create(request);
}
```

검증은 Controller 경계에서 1차로 처리하고, 비즈니스 규칙은 Service나 Domain에서 처리한다.

## Error Response

API는 실패 응답도 일관되어야 한다.

예:

```json
{
  "code": "MEMBER_NOT_FOUND",
  "message": "회원을 찾을 수 없습니다."
}
```

Spring에서는 `@RestControllerAdvice`를 사용해 예외를 공통 처리한다.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
}
```

## REST API 설계

REST API는 resource 중심으로 설계한다.

예:

```text
GET    /api/members
GET    /api/members/{id}
POST   /api/members
PATCH  /api/members/{id}
DELETE /api/members/{id}
```

동사보다 명사를 URL에 둔다.

나쁜 예:

```text
POST /api/createMember
```

좋은 예:

```text
POST /api/members
```

## 설명할 때 핵심 문장

```text
Spring MVC는 HTTP 요청을 Controller 메서드에 연결하고, JSON과 Java 객체를 변환해주는 웹 프레임워크다.
Controller는 HTTP 요청/응답을 담당하고, 비즈니스 로직은 Service로 위임하는 것이 좋다.
REST API는 resource 중심으로 URL을 설계하고, method로 행위를 표현한다.
검증과 예외 응답은 공통 구조로 관리해야 API 품질이 좋아진다.
```
