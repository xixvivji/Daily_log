# 18. Spring Security 로그인 실전

## 목표 구조

```text
회원가입
→ 비밀번호 BCrypt hash 저장

로그인
→ credential 검증
→ Session 또는 Token 발급

인증된 요청
→ Security Filter Chain
→ Authentication 생성
→ SecurityContext 저장
→ Authorization 확인
→ Controller
```

인증 구현은 token을 만드는 코드보다 credential 저장, 만료, 폐기, 오류 처리, 권한 검사와 탈취 대응이 중요하다.

## 의존성

```gradle
implementation("org.springframework.boot:spring-boot-starter-security")
testImplementation("org.springframework.security:spring-security-test")
```

Spring Security는 Servlet Filter를 통해 Spring MVC 앞에서 요청을 처리한다.

## Password 저장

```java
@Bean
PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

```java
String hash = passwordEncoder.encode(request.password());
memberRepository.save(Member.create(request.email(), hash));
```

로그인 비교:

```java
if (!passwordEncoder.matches(request.password(), member.getPasswordHash())) {
    throw new InvalidCredentialsException();
}
```

같은 password도 BCrypt salt 때문에 encode 결과가 달라질 수 있으므로 hash 문자열을 직접 비교하지 않는다. 응답, log, event에 원문 password나 hash를 포함하지 않는다.

## SecurityFilterChain

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .build();
    }
}
```

Path 규칙은 바깥 방어선이다. `주문 소유자가 맞는가?` 같은 resource 권한은 Service/use case에서도 검사한다.

## Session 로그인 흐름

```text
POST /api/auth/login
→ email/password 검증
→ Authentication 생성
→ SecurityContext 설정
→ SecurityContextRepository에 저장
→ session id cookie 응답
```

직접 login endpoint를 만들 경우 현재 Spring Security 버전의 명시적 SecurityContext 저장 요구사항을 확인한다.

```java
Authentication authentication = authenticationManager.authenticate(
    UsernamePasswordAuthenticationToken.unauthenticated(
        request.email(), request.password()
    )
);

SecurityContext context = SecurityContextHolder.createEmptyContext();
context.setAuthentication(authentication);
securityContextRepository.saveContext(context, httpRequest, httpResponse);
```

## Session Cookie 설정

```text
HttpOnly → JavaScript 직접 접근 제한
Secure   → HTTPS에서만 전송
SameSite → cross-site 전송 범위
Path     → 필요한 경로 범위
```

로그인 성공 시 session fixation 방어를 위해 session ID를 교체하고, logout·password 변경·계정 정지 시 session 무효화 정책을 둔다.

서버가 여러 대면 다음 선택이 있다.

```text
Load Balancer sticky session
→ 단순하지만 instance 장애와 scale-out 제약

Spring Session + Redis
→ 여러 instance가 session 공유

Stateless Token
→ session lookup 감소, 폐기와 탈취 대응은 별도 설계
```

## JWT Access Token

JWT는 header, payload, signature로 구성된다. 서명은 위변조를 검증하지만 payload를 암호화하지 않는다.

검증 항목:

```text
허용한 algorithm
signature
exp 만료
nbf 사용 가능 시점
iss 발급자
aud 대상 API
scope 또는 authority
```

Spring Security Resource Server를 사용하면 검증 filter와 `JwtDecoder`를 직접 처음부터 구현하는 일을 줄일 수 있다.

```java
http.oauth2ResourceServer(resource -> resource.jwt(Customizer.withDefaults()));
```

## Access Token과 Refresh Token

```text
Access Token
→ API 요청에 사용, 짧은 만료

Refresh Token
→ access token 재발급, 더 긴 만료와 서버 저장 고려
```

Rotation 흐름:

```text
refresh 요청
→ 현재 refresh token hash와 상태 확인
→ 이전 token 폐기
→ 새 access/refresh token 발급
→ 폐기된 token 재사용 감지 시 token family 전체 무효화
```

Refresh token 원문 대신 hash를 저장하면 DB 유출 피해를 줄일 수 있다.

## Token 전달 위치

```text
Authorization: Bearer
→ mobile, server-to-server, API client에 명확

HttpOnly Cookie
→ browser JavaScript가 token을 직접 읽지 않음
→ 자동 전송되므로 CSRF 고려
```

`localStorage`는 XSS가 발생하면 token을 읽을 수 있다. HttpOnly cookie도 XSS script의 인증 요청 실행 자체를 막지는 못한다. 저장 위치 하나로 보안을 완성할 수 없다.

## CSRF 설정

Cookie 기반 인증은 browser가 cookie를 자동 전송하므로 CSRF 보호가 중요하다. Spring Security의 CSRF 보호를 이유 없이 끄지 않는다.

```text
Session/Cookie 인증
→ CSRF token과 SameSite, Origin 검증 고려

Authorization header만 사용하는 API
→ browser 자동 credential 전송 여부를 확인한 뒤 정책 결정
```

## 현재 사용자 주입

```java
@GetMapping("/me")
public MemberResponse me(@AuthenticationPrincipal LoginMember principal) {
    return memberService.findById(principal.id());
}
```

Controller가 email 문자열을 다시 조회하는 것보다 안정적인 내부 member ID를 principal에 포함하는 방식이 편리하다. 민감한 Entity 전체를 principal에 장기 저장하지 않는다.

## Method Authorization

```java
@PreAuthorize("hasRole('ADMIN')")
public void suspendMember(Long memberId) { }
```

단순 role과 resource ownership을 구분한다.

```java
if (!order.isOwnedBy(currentMemberId)) {
    throw new AccessDeniedException("order access denied");
}
```

## 401과 403

```text
401 Unauthorized
→ 인증 credential이 없거나 유효하지 않음
→ AuthenticationEntryPoint

403 Forbidden
→ 인증됐지만 권한 없음
→ AccessDeniedHandler
```

일관된 JSON error response를 반환하고 내부 token parsing 오류나 사용자 존재 여부를 과도하게 공개하지 않는다.

## Logout

```text
Session
→ session invalidation, cookie 만료

Access Token
→ 짧은 만료까지 기다리거나 denylist 사용

Refresh Token
→ 서버 저장 상태 폐기
```

JWT logout은 client 저장소에서 token을 지우는 것만으로 이미 탈취된 token을 폐기하지 못한다.

## 공격 대응

```text
Credential Stuffing → login rate limit, MFA, 유출 password 차단
Brute Force         → 계정/IP/device 기준 제한과 지연
Session Fixation    → 인증 성공 시 session ID 교체
Token Theft         → HTTPS, 짧은 만료, rotation, 재사용 감지
User Enumeration    → login 실패 메시지 일반화
Privilege Escalation → server-side 권한 검사와 audit log
```

## Test

```java
mockMvc.perform(get("/api/members/me").with(jwt()
        .jwt(jwt -> jwt.subject("member-1"))
        .authorities(new SimpleGrantedAuthority("ROLE_USER"))))
    .andExpect(status().isOk());
```

반드시 확인할 것:

```text
인증 없음 401
권한 부족 403
정상 사용자 성공
다른 사용자 resource 접근 거부
만료·잘못된 서명 token 거부
logout과 refresh token 폐기
CSRF와 CORS 조합
```

## 공식 참고 자료

- [Spring Security Servlet Applications](https://docs.spring.io/spring-security/reference/servlet/index.html)
- [Spring Security OAuth2 Test](https://docs.spring.io/spring-security/reference/servlet/test/mockmvc/oauth2.html)

## 설명할 때 핵심 문장

```text
Spring Security는 Filter Chain에서 Authentication을 만들고 SecurityContext에 저장한 뒤 권한을 검사한다.
Session은 서버가 상태를 관리하고 JWT는 자체 검증이 가능하지만, JWT도 폐기와 refresh token 때문에 서버 상태가 필요할 수 있다.
인증 방식보다 credential 저장, 만료, 폐기, CSRF, 권한 검사가 더 중요하다.
```
