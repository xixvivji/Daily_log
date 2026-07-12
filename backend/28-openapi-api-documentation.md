# 28. OpenAPI와 API 문서화

## API 문서가 필요한 이유

API 문서는 endpoint 목록이 아니라 frontend, mobile, 외부 client와 backend 사이의 계약이다.

```text
요청 method와 path
인증 방식
path, query, header parameter
request body schema
response body schema
status code
오류 code
pagination과 정렬 규칙
```

OpenAPI는 HTTP API를 machine-readable document로 표현하는 specification이고 Swagger UI는 OpenAPI 문서를 사람이 탐색하고 호출할 수 있게 보여주는 도구 중 하나다.

```text
OpenAPI
→ API 명세 형식

Swagger UI
→ OpenAPI를 표시하는 UI

springdoc-openapi
→ Spring application에서 OpenAPI document 생성 지원
```

## Code First와 Contract First

### Code First

Controller와 DTO에서 OpenAPI를 생성한다.

장점:

```text
Spring code와 문서를 가깝게 유지
기존 project에 적용하기 쉬움
```

단점:

```text
구현이 먼저 굳어 API 설계 검토가 늦어질 수 있음
annotation이 과도해질 수 있음
runtime code만으로 business rule을 모두 표현하기 어려움
```

### Contract First

OpenAPI YAML을 먼저 작성하고 server stub이나 client를 생성한다.

장점:

```text
구현 전에 API 계약 합의
여러 팀과 병렬 개발에 유리
client generation과 변경 검증 용이
```

단점:

```text
명세와 구현을 동기화하는 절차 필요
작은 project에서는 관리 비용 증가
```

## springdoc-openapi 기본 구성

사용하는 Spring Boot major version과 호환되는 springdoc starter version은 공식 문서에서 확인한다.

```groovy
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:{version}'
```

기본적으로 다음 endpoint가 제공될 수 있다.

```text
/v3/api-docs
/swagger-ui.html
```

운영 환경에서 Swagger UI와 API docs를 공개할지는 보안 정책으로 결정한다. 문서 endpoint를 숨긴다고 API 보안이 생기는 것은 아니지만, 내부 endpoint와 schema 노출 범위는 제한할 수 있다.

## DTO Schema

Entity를 API schema로 직접 노출하지 않는다.

```java
public record MemberCreateRequest(
    @NotBlank
    @Email
    @Schema(example = "user@example.com")
    String email,

    @NotBlank
    @Size(min = 8, max = 72)
    @Schema(accessMode = Schema.AccessMode.WRITE_ONLY)
    String password
) {
}
```

validation annotation은 runtime 검증 규칙이고 OpenAPI schema는 client 계약이다. 둘이 자동으로 완전히 일치한다고 가정하지 말고 생성 결과를 검사한다.

비밀번호와 token은 example이나 response schema에 노출하지 않는다.

## Response와 오류 계약

성공 응답만 문서화하면 client가 실패를 처리할 수 없다.

```json
{
  "code": "MEMBER_NOT_FOUND",
  "message": "회원을 찾을 수 없습니다.",
  "traceId": "01J..."
}
```

문서화할 항목:

```text
400 validation 실패
401 인증되지 않음
403 권한 없음
404 resource 없음
409 상태 충돌 또는 중복
429 요청 제한
500 예상하지 못한 server 오류
```

HTTP status와 application error code의 역할을 구분한다.

```text
HTTP status
→ 오류의 큰 분류

application error code
→ client가 분기할 안정적인 식별자
```

## Pagination과 Collection

단순 array만 문서화하지 말고 pagination metadata와 parameter 제한을 명시한다.

```json
{
  "items": [],
  "page": 0,
  "size": 20,
  "totalElements": 135,
  "hasNext": true
}
```

```text
기본 page와 size
최대 size
허용 sort field
cursor 형식과 만료 여부
빈 결과의 표현
```

## 인증 Scheme

Bearer token 예:

```java
@SecurityScheme(
    name = "bearerAuth",
    type = SecuritySchemeType.HTTP,
    scheme = "bearer",
    bearerFormat = "JWT"
)
```

cookie session, OAuth 2.0 scope, API key를 사용한다면 실제 방식과 일치하는 security scheme을 작성한다. Swagger UI의 호출 편의를 위해 production 보안을 약화하면 안 된다.

## API 변경과 호환성

호환 가능한 변경 예:

```text
optional response field 추가
새 endpoint 추가
새 optional query parameter 추가
```

호환성을 깨기 쉬운 변경:

```text
field 제거 또는 이름 변경
type 변경
required field 추가
enum 값 처리 방식 변경
status code 의미 변경
```

client가 unknown field와 enum을 어떻게 처리하는지 확인해야 한다. 문서 diff를 CI에서 검토하면 의도하지 않은 API 변경을 발견할 수 있다.

## 문서와 구현의 일치 검증

```text
application context에서 /v3/api-docs 생성 확인
중요 endpoint와 schema 존재 검사
OpenAPI schema validation
이전 version과 breaking change 비교
생성 client compile test
```

문서 example을 수동으로만 관리하면 쉽게 오래된다. Controller test 결과나 REST Docs snippet과 OpenAPI를 연결하는 방법도 선택할 수 있다.

## 문서에 넣지 말아야 할 것

```text
실제 access token
실제 사용자 개인정보
내부 server 주소와 credential
운영 DB identifier
공격에 직접 유용한 내부 구현 정보
```

그러나 보안을 이유로 정상적인 request와 error 계약까지 숨기면 client가 추측해서 구현하게 된다.

## 공식 참고 자료

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [springdoc-openapi Documentation](https://springdoc.org/)
- [Spring REST Docs](https://docs.spring.io/spring-restdocs/docs/current/reference/htmlsingle/)

## 설명할 때 핵심 문장

OpenAPI는 client와 server가 공유하는 실행 가능한 API 계약이다. endpoint뿐 아니라 인증, validation, 오류, pagination과 호환성까지 표현하고, CI에서 실제 구현과의 불일치를 검사해야 한다.
