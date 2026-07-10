# 2026-07-10 HTTP와 HTTPS 심화: 요청, 응답, Cache, CORS, TLS

## 핵심 관점

백엔드 개발자는 HTTP를 단순히 API 호출 방식으로만 보면 부족하다.

운영에서는 아래 질문을 계속 만나게 된다.

```text
왜 404가 나는가?
왜 502가 나는가?
왜 HTTPS 리다이렉트가 반복되는가?
왜 CORS 오류가 나는가?
왜 배포했는데 브라우저가 예전 JS를 쓰는가?
왜 쿠키가 안 붙는가?
왜 OAuth callback URL이 틀어지는가?
```

이 문제들은 HTTP, HTTPS, 프록시 헤더, TLS 종료 위치와 연결된다.

## 1. HTTP 요청 구조

HTTP 요청은 크게 세 부분이다.

```text
Start Line
Headers
Body
```

예:

```http
POST /api/users HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer token

{"name":"kim"}
```

Start Line:

```text
POST /api/users HTTP/1.1
```

의미:

```text
POST
→ method

/api/users
→ path

HTTP/1.1
→ version
```

Headers:

```text
Host
Content-Type
Authorization
Cookie
User-Agent
Accept
```

Body:

```text
JSON
Form data
파일 업로드
```

## 2. HTTP 응답 구조

HTTP 응답도 세 부분이다.

```text
Status Line
Headers
Body
```

예:

```http
HTTP/1.1 201 Created
Content-Type: application/json
Set-Cookie: session=abc; Secure; HttpOnly

{"id":1}
```

Status Line:

```text
HTTP/1.1 201 Created
```

Headers:

```text
Content-Type
Cache-Control
Set-Cookie
Location
```

Body:

```text
응답 데이터
```

## 3. HTTP Method

자주 쓰는 method:

```text
GET
→ 조회

POST
→ 생성, 처리 요청

PUT
→ 전체 수정

PATCH
→ 일부 수정

DELETE
→ 삭제

OPTIONS
→ 사전 확인, CORS preflight에 자주 사용
```

GET은 보통 body를 사용하지 않는다.

POST는 body에 데이터를 담아 보낸다.

PUT과 PATCH 차이:

```text
PUT
→ 리소스 전체를 교체하는 의미

PATCH
→ 리소스 일부를 변경하는 의미
```

## 4. Status Code

상태 코드는 장애 분석의 첫 단서다.

```text
2xx 성공
3xx 리다이렉트
4xx 클라이언트 요청 문제
5xx 서버 또는 프록시 문제
```

자주 보는 코드:

```text
200 OK
201 Created
204 No Content

301 Moved Permanently
302 Found
304 Not Modified

400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
405 Method Not Allowed
413 Payload Too Large
429 Too Many Requests

500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

프록시 구조에서 특히 중요한 코드:

```text
502
→ Nginx나 ALB가 upstream에서 정상 응답을 못 받음

503
→ 사용 가능한 target이 없음

504
→ upstream 응답 timeout
```

## 5. Host Header

Host 헤더는 어떤 도메인으로 요청했는지 나타낸다.

```http
Host: api.example.com
```

하나의 IP나 ALB에서 여러 도메인을 처리할 수 있는 이유가 Host 헤더다.

Nginx 예:

```nginx
server {
    server_name api.example.com;
}

server {
    server_name admin.example.com;
}
```

같은 IP로 들어와도 Host가 다르면 다른 server block이 선택될 수 있다.

## 6. Content-Type과 Accept

`Content-Type`은 내가 보내는 body의 형식을 말한다.

```http
Content-Type: application/json
```

`Accept`는 내가 받고 싶은 응답 형식을 말한다.

```http
Accept: application/json
```

API에서 자주 보는 문제:

```text
Content-Type이 없어서 body parsing 실패
multipart/form-data 설정 오류
JSON이 아닌데 JSON으로 파싱
```

## 7. Cookie

쿠키는 브라우저가 서버와 주고받는 작은 데이터다.

서버가 쿠키를 내려준다.

```http
Set-Cookie: session=abc; HttpOnly; Secure; SameSite=Lax
```

브라우저는 이후 요청에 쿠키를 붙인다.

```http
Cookie: session=abc
```

중요 속성:

```text
HttpOnly
→ JavaScript에서 접근 불가

Secure
→ HTTPS에서만 전송

SameSite
→ cross-site 요청에서 쿠키 전송 정책

Domain
→ 쿠키가 적용될 도메인

Path
→ 쿠키가 적용될 path
```

HTTPS 뒤에서 쿠키가 안 붙으면 `Secure`, `SameSite`, `X-Forwarded-Proto`를 같이 확인해야 한다.

## 8. CORS

CORS는 브라우저 보안 정책이다.

서버와 다른 origin에서 API를 호출할 때 브라우저가 제한한다.

Origin은 세 가지 조합이다.

```text
scheme
host
port
```

예:

```text
https://app.example.com
https://api.example.com
```

host가 다르므로 다른 origin이다.

CORS에서 중요한 헤더:

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET,POST,PUT,DELETE
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Credentials: true
```

인증 쿠키를 쓰는 경우:

```text
Access-Control-Allow-Origin에 * 사용 불가
Access-Control-Allow-Credentials: true 필요
프론트 요청에도 credentials 설정 필요
```

Preflight:

```text
브라우저가 실제 요청 전에 OPTIONS 요청으로 허용 여부 확인
```

## 9. HTTP Cache

HTTP Cache는 응답을 저장해서 재사용하는 기능이다.

대표 헤더:

```text
Cache-Control
ETag
Last-Modified
Expires
```

정적 파일:

```http
Cache-Control: public, max-age=31536000, immutable
```

API 응답:

```http
Cache-Control: no-store
```

배포 후 문제가 되는 경우:

```text
새 버전을 배포했는데 브라우저가 예전 JS/CSS를 계속 사용
CDN 캐시가 예전 응답을 들고 있음
API 응답이 잘못 캐시됨
```

해결 방향:

```text
정적 파일명에 hash 포함
HTML은 짧게 캐시
API는 명확한 Cache-Control 설정
CDN invalidation
```

## 10. HTTP/1.1, HTTP/2, HTTP/3

HTTP/1.1:

```text
텍스트 기반
keep-alive 지원
요청 처리 효율에 한계
```

HTTP/2:

```text
바이너리 프레이밍
하나의 TCP 연결에서 여러 요청 multiplexing
헤더 압축
```

HTTP/3:

```text
QUIC 사용
QUIC은 UDP 위에서 동작
연결 설정 지연 감소
TCP 레벨 head-of-line blocking 완화
```

백엔드 입장에서는 처음에 HTTP/1.1 요청/응답 구조와 status code를 먼저 정확히 잡는 것이 중요하다.

## 11. HTTPS와 TLS

HTTPS는 HTTP에 TLS가 붙은 것이다.

```text
HTTPS = HTTP + TLS
```

흐름:

```text
DNS 조회
→ TCP 연결
→ TLS handshake
→ HTTP 요청
```

TLS가 제공하는 것:

```text
암호화
무결성
서버 인증
```

인증서 검증:

```text
인증서 만료 여부
도메인 일치 여부
신뢰 가능한 CA
인증서 체인
```

## 12. SNI

SNI는 Server Name Indication이다.

TLS handshake 중 클라이언트가 어떤 도메인에 접속하려는지 알려준다.

필요한 이유:

```text
하나의 IP 또는 ALB에서 여러 HTTPS 도메인을 처리할 수 있게 함
서버가 도메인에 맞는 인증서를 선택할 수 있게 함
```

예:

```text
api.example.com
admin.example.com
```

같은 ALB로 들어와도 SNI를 보고 인증서를 고를 수 있다.

## 13. TLS Termination

TLS termination은 HTTPS 연결을 특정 지점에서 끝내는 것이다.

ALB에서 종료:

```text
Client
→ HTTPS
→ ALB
→ HTTP
→ EC2 / Nginx / Backend
```

Nginx에서 종료:

```text
Client
→ HTTPS
→ Nginx
→ HTTP
→ Backend
```

ALB에서 종료하면 ACM 인증서 관리가 편하다.

Nginx에서 종료하면 서버에서 인증서를 직접 관리한다.

## 14. X-Forwarded Headers

프록시 뒤의 백엔드는 원래 클라이언트 정보를 직접 알기 어렵다.

그래서 프록시가 헤더로 전달한다.

```http
X-Forwarded-For: 203.0.113.10
X-Forwarded-Proto: https
X-Forwarded-Host: api.example.com
```

중요한 문제:

```text
X-Forwarded-Proto가 없으면 백엔드가 HTTP 요청으로 오해
HTTPS 리다이렉트 반복
Secure Cookie 문제
OAuth callback URL 문제
```

## 15. 장애 분석에서 HTTP/HTTPS 보기

확인 순서:

```text
DNS가 정상인가?
TCP 80/443 연결이 되는가?
TLS 인증서가 정상인가?
HTTP status code가 무엇인가?
Nginx access.log에 찍히는가?
Nginx error.log에 upstream 오류가 있는가?
Backend log에 요청이 찍히는가?
```

명령어:

```bash
curl -v https://api.example.com/health
curl -I https://api.example.com
openssl s_client -connect api.example.com:443 -servername api.example.com
```

## 최종 정리

```text
HTTP 요청은 method, path, version, headers, body로 구성된다.
HTTP 응답은 status code, headers, body로 구성된다.
Host 헤더는 도메인 기반 라우팅의 기준이다.
CORS는 브라우저가 강제하는 cross-origin 보안 정책이다.
HTTP Cache는 성능을 높이지만 배포와 사용자별 응답에서 주의해야 한다.
HTTPS는 HTTP 전에 TLS handshake와 인증서 검증이 필요하다.
SNI는 하나의 IP에서 여러 HTTPS 도메인을 처리하는 데 필요하다.
TLS termination 위치에 따라 X-Forwarded-Proto 처리가 중요해진다.
```
