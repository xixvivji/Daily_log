# 26. OAuth 2.0과 OpenID Connect 로그인 실전

## OAuth 2.0과 로그인의 차이

OAuth 2.0은 resource 접근 권한을 위임하는 authorization framework다. 사용자 로그인을 위한 identity protocol 자체는 아니다.

OpenID Connect는 OAuth 2.0 위에 identity layer를 추가하고 `id_token`으로 사용자의 인증 정보를 전달한다.

```text
OAuth 2.0
→ access delegation

OpenID Connect
→ authentication
→ openid scope와 id_token
```

Google처럼 OIDC를 지원하는 provider는 `id_token`을 검증해 로그인한다. GitHub처럼 일반 OAuth 2.0 provider를 로그인에 사용할 때는 access token으로 UserInfo API를 호출해 사용자 정보를 가져오는 방식이 사용된다.

## 참여자

```text
Resource Owner
→ 사용자

Client
→ 우리 Spring application

Authorization Server
→ Google, GitHub 등의 인증 server

Resource Server
→ 사용자 정보 API
```

우리 application이 provider의 access token을 발급한다고 생각하면 안 된다. application은 등록된 Client로서 authorization code를 받고 token endpoint에 교환한다.

## Authorization Code 흐름

```text
1. 사용자가 /oauth2/authorization/google 접근
2. Spring Security가 provider authorization endpoint로 redirect
3. 사용자가 provider에서 로그인하고 동의
4. provider가 redirect URI로 authorization code 전달
5. backend가 code를 provider token endpoint에 전달
6. access token과 OIDC라면 id_token 수신
7. 사용자 식별 정보 검증
8. local Member 조회 또는 생성
9. 우리 서비스 session 또는 token 발급
```

authorization code는 browser를 통해 전달되지만 token 교환은 backend와 provider 사이에서 수행한다. `client-secret`을 frontend에 보내면 안 된다.

## Spring Security 설정

Gradle:

```groovy
implementation 'org.springframework.boot:spring-boot-starter-oauth2-client'
```

```java
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/login/**", "/oauth2/**").permitAll()
            .anyRequest().authenticated()
        )
        .oauth2Login(oauth -> oauth
            .userInfoEndpoint(userInfo -> userInfo
                .oidcUserService(oidcUserService())
            )
        )
        .build();
}
```

설정 값은 환경 변수나 secret manager에서 주입한다.

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope:
              - openid
              - profile
              - email
```

대표 endpoint:

```text
로그인 시작
/oauth2/authorization/{registrationId}

redirect callback
/login/oauth2/code/{registrationId}
```

reverse proxy나 ALB 뒤에서는 application이 인식하는 scheme과 host가 외부 URL과 다를 수 있다. `Forwarded` 또는 `X-Forwarded-*` 신뢰 설정이 틀리면 redirect URI가 HTTP나 내부 host로 생성될 수 있다.

## Local Member 연결

provider email만으로 사용자를 식별하면 위험할 수 있다. provider가 보장하는 subject와 provider ID를 조합한다.

```text
oauth_account
────────────────────
id
member_id
provider
provider_subject
email_at_link_time
```

unique constraint:

```text
(provider, provider_subject)
```

```java
@Table(
    name = "oauth_account",
    uniqueConstraints = @UniqueConstraint(
        name = "uk_oauth_provider_subject",
        columnNames = {"provider", "provider_subject"}
    )
)
```

한 Member가 Google과 GitHub 계정을 모두 연결할 수 있으므로 관계는 일반적으로 다음과 같다.

```text
Member 1:N OAuthAccount
```

## 최초 가입과 계정 연결

```text
OAuthAccount 존재
→ 연결된 Member로 로그인

OAuthAccount 없음
→ 신규 Member 생성 또는 기존 계정 연결 절차
```

같은 email의 기존 Member를 자동 연결하면 account takeover 위험이 생길 수 있다. email verification 상태, provider 신뢰 수준, 기존 계정 재인증을 고려해야 한다.

안전한 계정 연결 예:

```text
기존 계정 로그인
→ 비밀번호 또는 현재 인증 재확인
→ OAuth provider 인증
→ 두 계정 연결
```

## OAuth Token과 우리 서비스 Token

provider access token은 provider API를 호출하기 위한 token이다. 우리 API 접근용 token과 목적이 다르다.

```text
Provider access token
→ Google Calendar, GitHub API 등 provider resource 접근

Service access token 또는 session
→ 우리 backend API 접근
```

provider token을 저장해야 한다면 암호화, 최소 scope, 만료와 refresh, revoke 정책이 필요하다. 로그인만 필요하고 provider API를 호출하지 않는다면 불필요하게 장기 보관하지 않는다.

## State, Nonce, PKCE

```text
state
→ authorization response가 시작한 요청과 연결되는지 확인

nonce
→ OIDC id_token replay 방어에 사용

PKCE
→ code interception 위험 완화
```

Spring Security가 기본 흐름을 처리하도록 두고 직접 protocol을 조립하지 않는 편이 안전하다.

## 실패 처리

구분할 실패:

```text
사용자가 동의를 거부함
authorization code가 만료됨
redirect URI가 일치하지 않음
client credential이 잘못됨
id_token issuer, audience, signature 검증 실패
필수 email claim이 없음
정지된 local Member와 연결됨
```

provider 오류 세부값이나 token을 frontend URL query에 그대로 노출하지 않는다. 내부 log에는 correlation ID를 남기고 사용자에게는 제한된 오류 code를 전달한다.

## Test

```text
기존 OAuthAccount 로그인
최초 로그인 시 Member와 OAuthAccount 생성
동일 provider subject 중복 방지
정지 회원 로그인 거부
provider email 변경 후에도 subject로 동일 계정 식별
redirect 성공과 실패 handler
계정 연결 시 기존 사용자 재인증
```

외부 provider 전체를 단위 테스트에서 호출하지 않는다. 사용자 정보 mapping과 local account 연결 Service를 분리해 테스트하고, 실제 provider 연동은 제한된 통합 테스트로 검증한다.

## 공식 참고 자료

- [Spring Security OAuth2](https://docs.spring.io/spring-security/reference/servlet/oauth2/index.html)
- [Spring Security OAuth 2.0 Login](https://docs.spring.io/spring-security/reference/servlet/oauth2/login/)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

## 설명할 때 핵심 문장

OAuth 2.0은 권한 위임이고 OpenID Connect가 인증 정보를 표준화한다. Social login은 provider 사용자를 local Member에 연결하는 과정까지 설계해야 하며, email만이 아니라 provider와 subject 조합을 외부 identity의 안정적인 식별자로 사용한다.
