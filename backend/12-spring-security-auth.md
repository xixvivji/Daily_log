# 12. Spring Security와 인증/인가

## 인증과 인가

인증은 사용자가 누구인지 확인하는 것이다.

```text
Authentication
→ 너 누구야?
```

인가는 인증된 사용자가 특정 자원에 접근할 수 있는지 확인하는 것이다.

```text
Authorization
→ 너 이거 해도 돼?
```

예:

```text
로그인
→ 인증

관리자 페이지 접근
→ 인가
```

## Session 기반 인증

Session 방식:

```text
사용자 로그인
→ 서버가 session 생성
→ session id를 cookie로 전달
→ 이후 요청마다 cookie 전달
→ 서버가 session 저장소에서 사용자 확인
```

장점:

```text
서버에서 session 무효화 쉬움
브라우저 기반 서비스와 잘 맞음
```

단점:

```text
서버 session 저장소 필요
서버 여러 대일 때 session 공유 필요
```

## JWT 기반 인증

JWT는 token 안에 claim을 담아 서명한 방식이다.

흐름:

```text
로그인
→ access token 발급
→ 클라이언트가 Authorization header에 token 전달
→ 서버가 token 검증
```

예:

```http
Authorization: Bearer eyJ...
```

장점:

```text
서버 session 저장소 없이 검증 가능
모바일/API 환경에 자주 사용
```

주의:

```text
탈취되면 만료 전까지 위험
token에 민감 정보 넣으면 안 됨
강제 로그아웃 구현이 어려울 수 있음
refresh token 관리 필요
```

## Spring Security Filter Chain

Spring Security는 filter chain 기반으로 동작한다.

요청 흐름:

```text
Client
→ Security Filter Chain
→ DispatcherServlet
→ Controller
```

Filter에서 하는 일:

```text
인증 정보 추출
token 검증
SecurityContext 저장
권한 확인
예외 처리
```

## SecurityContext

SecurityContext는 현재 요청의 인증 정보를 담는다.

```text
Authentication
→ principal
→ authorities
```

Controller나 Service에서 현재 사용자 정보를 사용할 수 있다.

## Password Hashing

비밀번호는 절대 평문 저장하면 안 된다.

일반적으로 BCrypt 같은 단방향 해시를 사용한다.

```text
원문 비밀번호
→ hash
→ DB 저장
```

로그인 시:

```text
입력 비밀번호
→ hash 비교
```

## CSRF

CSRF는 사용자가 의도하지 않은 요청을 보내게 만드는 공격이다.

브라우저 cookie 기반 인증에서 중요하다.

JWT를 Authorization header로 쓰는 stateless API에서는 CSRF 설정을 다르게 가져가는 경우가 많다.

## CORS와 Security

CORS는 Spring Security와 함께 설정해야 하는 경우가 많다.

프론트와 백엔드 origin이 다르면 CORS 설정이 필요하다.

```text
Access-Control-Allow-Origin
Access-Control-Allow-Methods
Access-Control-Allow-Headers
Access-Control-Allow-Credentials
```

인증 cookie를 쓰는 경우 `credentials` 설정이 중요하다.

## Spring Security 인증 구성 요소

```text
SecurityContextHolder
→ 현재 실행 흐름의 SecurityContext 보관

SecurityContext
→ 현재 Authentication 보관

Authentication
→ 인증 전에는 입력 credential, 인증 후에는 principal과 authority 표현

AuthenticationManager
→ 인증 요청을 받아 적절한 provider에 위임

AuthenticationProvider
→ 비밀번호, JWT 등 특정 방식으로 실제 인증

UserDetailsService
→ username으로 사용자 정보 조회

PasswordEncoder
→ 비밀번호 hash 생성과 일치 여부 확인
```

username/password 로그인은 대략 다음 흐름이다.

```text
login request
→ authentication filter
→ AuthenticationManager
→ AuthenticationProvider
→ UserDetailsService로 회원 조회
→ PasswordEncoder.matches로 비밀번호 비교
→ 성공한 Authentication 생성
→ SecurityContext 저장
```

## Session Cookie 보안

Session ID는 로그인 상태를 가리키는 credential이므로 탈취되면 계정을 도용할 수 있다.

```text
HttpOnly
→ JavaScript에서 cookie 접근 제한, XSS 탈취 위험 감소

Secure
→ HTTPS 연결에서만 cookie 전송

SameSite
→ cross-site 요청에서 cookie 전송 범위 제한

Domain / Path
→ cookie가 전송될 host와 URL 범위 제한
```

로그인 성공 시 session ID를 교체해 session fixation을 방어하고, 로그아웃이나 비밀번호 변경 시 관련 session을 무효화할 정책을 정한다. 여러 서버가 session을 공유해야 하면 Spring Session과 Redis 같은 중앙 저장소를 사용할 수 있다.

## JWT 구조와 오해

JWT는 일반적으로 다음 세 부분으로 구성된다.

```text
header.payload.signature
```

서명은 token이 위조되거나 변경되지 않았는지 검증한다. 일반 JWT payload는 암호화된 것이 아니라 Base64URL로 표현된 것이므로 누구나 내용을 읽을 수 있다. 비밀번호, 주민번호, secret을 넣으면 안 된다.

검증 항목:

```text
허용한 서명 algorithm인가?
서명이 올바른가?
만료 시간 exp가 지나지 않았는가?
발급자 iss와 대상 aud가 기대한 값인가?
사용 시작 시간 nbf가 유효한가?
```

token key는 코드에 넣지 말고 secret 관리 시스템에서 주입하며 rotation 전략을 준비한다.

## Access Token과 Refresh Token

```text
Access Token
→ API 인증에 사용
→ 탈취 피해를 줄이기 위해 비교적 짧은 만료

Refresh Token
→ 새 access token 발급에 사용
→ 더 엄격한 저장과 폐기 정책 필요
```

Refresh Token Rotation은 재발급할 때 refresh token도 새 값으로 교체하고 이전 token을 폐기한다. 폐기된 token이 다시 사용되면 token 탈취 가능성을 감지해 해당 token family를 모두 무효화할 수 있다.

JWT를 쓴다고 모든 서버 상태가 사라지는 것은 아니다. 강제 로그아웃, refresh token 관리, key rotation, 탈취 감지를 위해 서버 저장소가 필요할 수 있다.

## Token 저장 위치

```text
Authorization header
→ API와 mobile client에서 명시적으로 전달
→ 브라우저 저장 위치에 따라 XSS 위험 고려

HttpOnly cookie
→ JavaScript가 직접 읽기 어렵지만 browser가 자동 전송
→ CSRF 방어와 SameSite 설정 필요
```

어느 방식도 자동으로 안전하지 않다. XSS와 CSRF threat model, frontend 구조, 여러 domain 사용 여부를 기준으로 선택한다.

## CSRF와 XSS

CSRF는 browser가 cookie를 자동으로 보내는 성질을 악용해 사용자가 의도하지 않은 상태 변경 요청을 보내게 한다. CSRF token, SameSite cookie, Origin 검증 등을 사용한다.

XSS는 공격자가 주입한 script가 신뢰된 origin에서 실행되는 문제다. 출력 encoding, HTML sanitization, Content Security Policy, 위험한 script 실행 방지로 대응한다. HttpOnly cookie는 token 직접 탈취를 줄이지만 XSS script가 사용자의 browser에서 요청을 보내는 것까지 모두 막지는 못한다.

Spring Security는 안전하지 않은 HTTP method에 대한 CSRF 보호를 기본 제공하므로, 이유 없이 비활성화하지 말고 인증 정보가 어떻게 전달되는지 먼저 확인한다.

## CORS 동작에서 주의할 점

CORS는 인증 기능이 아니라 browser가 다른 origin의 응답을 frontend JavaScript에 공개할지 결정하는 정책이다. 서버 간 요청이나 curl 자체를 막는 방화벽이 아니다.

credential cookie를 허용할 때는 허용 origin을 구체적으로 지정해야 한다. `Access-Control-Allow-Origin: *`와 credential 허용을 함께 사용하는 식의 느슨한 설정은 피한다.

## 인가 적용 위치

URL 기반 규칙과 method 기반 규칙을 함께 사용할 수 있다.

```java
@PreAuthorize("hasRole('ADMIN')")
public void suspendMember(Long memberId) { ... }
```

단순 role 확인 외에도 `주문 소유자 본인인가?`, `현재 상태에서 취소 가능한가?` 같은 resource 기반 규칙이 필요하다. Controller path만 막지 말고 use case 실행 지점에서도 권한과 도메인 규칙을 확인한다.

## OAuth 2.0과 OpenID Connect

```text
OAuth 2.0
→ 다른 서비스의 resource에 접근 권한을 위임하는 framework

OpenID Connect
→ OAuth 2.0 위에 사용자 인증 정보를 표준화한 identity layer
→ ID Token 사용
```

소셜 로그인은 provider token을 받는 것만으로 끝나지 않는다. `state`와 PKCE 검증, redirect URI 제한, provider 사용자와 내부 회원 연결, 탈퇴·재가입 정책을 설계해야 한다.

## 인증·인가 실패 응답

```text
AuthenticationEntryPoint
→ 인증되지 않은 요청의 401 처리

AccessDeniedHandler
→ 인증됐지만 권한이 없는 요청의 403 처리
```

보안 실패도 일반 API 오류 형식과 맞추되, 사용자가 존재하는지나 비밀번호 중 무엇이 틀렸는지 과도하게 알려 공격자에게 정보를 주지 않는다. 로그인 실패 횟수 제한과 audit log도 고려한다.

## 설명할 때 핵심 문장

```text
인증은 사용자가 누구인지 확인하는 것이고, 인가는 그 사용자가 특정 작업을 할 권한이 있는지 확인하는 것이다.
Session 방식은 서버가 로그인 상태를 저장하고, JWT 방식은 서명된 token을 클라이언트가 들고 다니며 서버가 검증한다.
Spring Security는 filter chain에서 인증/인가를 처리하고, 인증 결과를 SecurityContext에 저장한다.
비밀번호는 평문 저장하면 안 되고 BCrypt 같은 해시로 저장해야 한다.
```
