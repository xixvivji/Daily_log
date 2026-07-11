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

## Spring MVC 내부 구성 요소

```text
HandlerMapping
→ 요청 URL과 HTTP method에 맞는 handler 탐색

HandlerAdapter
→ 선택한 Controller method를 실제 호출

HandlerMethodArgumentResolver
→ path variable, query parameter, request body, 인증 사용자 등을 method 인자로 변환

HttpMessageConverter
→ JSON과 Java 객체를 상호 변환

HandlerExceptionResolver
→ 발생한 예외를 error response로 변환
```

Jackson은 property 이름과 JSON key를 대응시킨다. 날짜 형식, null 처리, enum 값, 생성자 접근 가능 여부에 따라 역직렬화가 실패할 수 있다. 요청 DTO와 응답 DTO는 목적이 다르므로 분리한다.

```text
MemberCreateRequest → 생성할 때 입력 가능한 값
MemberUpdateRequest → 수정할 수 있는 값
MemberResponse      → 외부에 공개하기로 한 값
```

## Filter와 Interceptor

두 기능 모두 요청 전후에 공통 로직을 실행하지만 위치가 다르다.

```text
Servlet Filter
→ DispatcherServlet 바깥에서 동작
→ security, CORS, request wrapping 등에 사용

Spring Interceptor
→ DispatcherServlet 안에서 handler 실행 전후에 동작
→ 사용자별 logging, handler 기반 검사 등에 사용
```

```text
Client
→ Filter
→ DispatcherServlet
→ Interceptor preHandle
→ Controller
→ Interceptor postHandle/afterCompletion
→ Filter
```

Filter와 Interceptor에는 기술적인 횡단 관심사를 두고 핵심 비즈니스 규칙은 Service나 Domain에 둔다.

## 일관된 오류 응답

오류 응답에는 클라이언트가 분기할 안정적인 `code`와 사람이 이해할 `message`를 구분해 둔다. validation 오류라면 어느 field가 실패했는지도 제공할 수 있다.

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청 값이 올바르지 않습니다.",
  "errors": [
    {"field": "email", "reason": "올바른 이메일 형식이어야 합니다."}
  ]
}
```

내부 exception class 이름, SQL, stack trace는 응답으로 노출하지 않는다. 상세 원인은 trace id와 함께 서버 log에 남긴다.

## HTTP 상태 코드

```text
200 OK            → 조회 또는 일반적인 성공
201 Created       → 리소스 생성 성공
204 No Content    → body 없이 성공
400 Bad Request   → JSON 형식, 타입, validation 오류
401 Unauthorized  → 인증되지 않음
403 Forbidden     → 인증됐지만 권한 없음
404 Not Found     → 리소스를 찾을 수 없음
409 Conflict      → 중복 email, 현재 상태와 충돌하는 요청
500 Internal Server Error → 예상하지 못한 서버 오류
```

```java
@PostMapping
public ResponseEntity<MemberResponse> create(
    @Valid @RequestBody MemberCreateRequest request
) {
    MemberResponse response = memberService.create(request);
    URI location = URI.create("/api/members/" + response.id());
    return ResponseEntity.created(location).body(response);
}
```

## PUT과 PATCH

```text
PUT
→ 리소스 전체 표현 교체
→ 같은 요청을 반복해도 같은 상태가 되도록 설계하기 쉬움

PATCH
→ 리소스 일부 변경
→ 누락된 값과 null로 바꾸려는 값을 구분해야 함
```

수정 DTO의 모든 필드를 nullable로 만들면 `값을 보내지 않음`과 `null로 변경`을 구분하기 어렵다. API 계약에 따라 전용 command나 명시적인 변경 필드를 사용한다.

## 목록 조회와 Pagination

```http
GET /api/members?page=0&size=20&sort=createdAt,desc
```

```text
Offset pagination
→ page 번호 사용이 간단하지만 뒤쪽 page일수록 많은 row를 건너뛸 수 있음

Cursor pagination
→ 마지막으로 본 정렬 key 이후를 조회
→ 큰 데이터와 무한 스크롤에 유리하지만 임의 page 이동은 어려움
```

정렬 값이 중복될 수 있으면 `createdAt, id`처럼 고유한 보조 정렬 key를 포함해야 결과가 흔들리지 않는다.

## API 멱등성

멱등성이란 같은 요청을 여러 번 수행해도 최종 상태가 같은 성질이다. 네트워크 timeout 뒤 재시도가 발생할 수 있으므로 결제·주문 생성에서 특히 중요하다.

```http
Idempotency-Key: 2fd2b42e-...
```

서버는 key와 처리 결과를 저장해 같은 key의 요청이 새 주문이나 결제를 다시 만들지 않게 할 수 있다. HTTP method가 의미상 멱등적이어도 구현이 매번 새로운 부수 효과를 만들면 실제 처리는 멱등하지 않다.

## 파일 업로드와 API 버전

파일은 보통 `multipart/form-data`로 받고 크기, 확장자, 실제 content type, 저장 경로를 검증한다. 운영에서는 instance 교체에 영향을 받는 로컬 디스크보다 object storage를 주로 사용한다.

호환되지 않는 변경이 필요하면 URL(`/api/v1`)이나 header 기반 version을 고려한다. version을 늘리기 전에 optional field 추가처럼 기존 클라이언트를 깨지 않는 변경인지 먼저 판단한다.

## 설명할 때 핵심 문장

```text
Spring MVC는 HTTP 요청을 Controller 메서드에 연결하고, JSON과 Java 객체를 변환해주는 웹 프레임워크다.
Controller는 HTTP 요청/응답을 담당하고, 비즈니스 로직은 Service로 위임하는 것이 좋다.
REST API는 resource 중심으로 URL을 설계하고, method로 행위를 표현한다.
검증과 예외 응답은 공통 구조로 관리해야 API 품질이 좋아진다.
```
