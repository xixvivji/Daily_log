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

## 설명할 때 핵심 문장

```text
인증은 사용자가 누구인지 확인하는 것이고, 인가는 그 사용자가 특정 작업을 할 권한이 있는지 확인하는 것이다.
Session 방식은 서버가 로그인 상태를 저장하고, JWT 방식은 서명된 token을 클라이언트가 들고 다니며 서버가 검증한다.
Spring Security는 filter chain에서 인증/인가를 처리하고, 인증 결과를 SecurityContext에 저장한다.
비밀번호는 평문 저장하면 안 되고 BCrypt 같은 해시로 저장해야 한다.
```
