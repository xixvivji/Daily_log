# 2026-07-11 현대 HTTP 완성: 의미론, Cache, Cookie, TLS, HTTP/2·3, 인코딩

## 이 문서의 범위

이 문서는 HTTP 학습 범위 중 우선순위가 높은 내용을 현대 백엔드와 클라우드 운영 관점에서 다시 정리한다.

```text
웹의 기초
HTTP 의미론과 연결 관리
Cache
HTTP/2와 HTTP/3
Cookie와 인증
HTTPS와 TLS
Entity, Representation, Encoding
국제화와 내용 협상
Proxy, Gateway, Tunnel의 현대적 의미
콘텐츠 배포와 CDN
```

과거 기술이라고 해서 장 전체를 무조건 버리지는 않는다. 현재 기술을 이해하는 데 필요한 개념은 남기고, 현대 서비스에서 거의 사용하지 않는 세부 구현은 역사적 맥락만 설명한다.

## 장별 반영 기준

| 기존 학습 범위 | 반영 방식 |
|---|---|
| I. HTTP 웹의 기초 | 전체 핵심 반영 |
| 5장 웹 서버 | 제품별 세부는 제외, Web Server·WAS·Origin 역할은 반영 |
| 6장 프락시 | 옛 용어는 줄이고 Forward·Reverse Proxy와 신뢰 경계 반영 |
| 7장 Cache | 현대 Cache-Control과 재검증 중심으로 반영 |
| 8장 Gateway·Tunnel·Relay | API Gateway, CONNECT, TLS passthrough, Upgrade만 반영 |
| 9장 웹 로봇 | robots.txt, crawler 부하와 보안 오해만 반영 |
| 10장 HTTP/2 | Frame, Stream, HPACK, Flow Control까지 반영 |
| 11장 클라이언트 식별 | 개인정보 추적 세부는 제외, 식별 수단의 한계와 Cookie 반영 |
| 12장 기본 인증 | 동작과 위험, 제한된 사용처만 반영 |
| 13장 다이제스트 인증 | 역사적 의미와 현재 잘 쓰지 않는 이유만 반영 |
| 14장 보안 HTTP | TLS 1.3, 인증서, HSTS까지 반영 |
| 15장 Entity와 Encoding | Representation, 길이, 압축, Range, Multipart 반영 |
| 16장 국제화 | UTF-8, charset, 언어 tag와 협상에 필요한 부분 반영 |
| 17장 내용 협상 | Accept 계열, q 값, Vary 중심으로 반영 |
| 17.4 투명 협상 | 현재 구조와 거리가 있어 개념만 반영 |
| 17.5 Transcoding | CDN 압축·이미지 변환 관점으로 반영 |
| V. 콘텐츠 발행·배포 | 옛 도구는 제외, CDN·Origin·무효화·서명 URL 반영 |

## 1. HTTP의 본질

HTTP는 분산된 시스템에서 resource를 요청하고 representation을 주고받기 위한 stateless application protocol이다.

```text
Resource
→ 서버가 제공하는 논리적인 대상
→ 회원, 주문, 이미지, 문서 등

Representation
→ 특정 시점의 resource를 표현한 byte 데이터와 metadata
→ JSON, HTML, JPEG 등
```

`/members/1`은 resource의 식별자이고 JSON 응답은 그 resource의 representation 중 하나다.

```http
GET /members/1 HTTP/1.1
Host: api.example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"id":1,"name":"jiwon"}
```

## 2. URI, URL, Origin

예시 URL:

```text
https://api.example.com:443/members/1?details=true#profile
```

```text
scheme   → https
host     → api.example.com
port     → 443
path     → /members/1
query    → details=true
fragment → profile
```

Fragment는 일반적인 HTTP 요청에 포함되지 않고 browser 내부에서 사용한다.

Origin은 다음 세 값의 조합이다.

```text
scheme + host + port
```

따라서 아래 둘은 서로 다른 origin이다.

```text
https://app.example.com
https://api.example.com
```

host가 다르기 때문에 browser의 Same-Origin Policy와 CORS 영향을 받는다.

## 3. HTTP Message

HTTP/1.1 message는 시작 줄, header, 빈 줄, 선택적인 body로 구성된다.

```http
POST /orders HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Length: 28

{"productId":10,"count":2}
```

Header는 message와 representation에 대한 metadata다.

```text
Host          → 요청 대상 host
Authorization → 인증 credential
Content-Type  → body의 media type
Accept        → 원하는 응답 media type
Cache-Control → cache 정책
Cookie        → 저장된 cookie 전달
Traceparent   → 분산 추적 정보
```

Header 이름은 대소문자를 구분하지 않지만 값의 의미는 header 정의에 따라 다르다.

## 4. Method 의미론

### Safe Method

Safe method는 서버 상태를 변경하려는 의미를 갖지 않는다.

```text
GET
HEAD
OPTIONS
TRACE
```

조회 log나 통계가 남는 부수 효과까지 금지한다는 뜻은 아니다. 사용자가 의도한 resource 상태 변경이 없어야 한다는 의미다.

### Idempotent Method

같은 요청을 여러 번 보내도 최종 의도된 상태가 같은 성질이다.

```text
GET     → idempotent
PUT     → idempotent
DELETE  → idempotent
POST    → 일반적으로 idempotent가 아님
PATCH   → 정의와 구현에 따라 다름
```

`DELETE /members/1`을 두 번 실행했을 때 두 번째 응답이 `404`여도 최종 상태는 회원이 없다는 점에서 method 의미는 idempotent할 수 있다.

### POST, PUT, PATCH

```text
POST
→ collection에 새 resource 생성 또는 명령 처리

PUT
→ 요청 URI의 resource 전체 상태를 생성하거나 교체

PATCH
→ resource 일부 변경
```

결제와 주문 생성처럼 POST 요청을 재시도해야 한다면 idempotency key를 사용할 수 있다.

```http
POST /payments HTTP/1.1
Idempotency-Key: 0ca25d7c-9fd9-4cf5-a4aa-dcd4db465880
```

서버는 key와 요청 fingerprint, 처리 결과를 저장해 같은 요청이 중복 결제되지 않도록 한다.

## 5. Status Code와 Redirect

```text
2xx → 성공
3xx → redirect 또는 cache 재검증
4xx → client 요청 문제
5xx → server 또는 upstream 처리 실패
```

### 자주 쓰는 성공 코드

```text
200 OK         → 일반 성공
201 Created    → resource 생성
202 Accepted   → 비동기 처리 접수
204 No Content → body 없이 성공
206 Partial Content → 범위 응답
```

### Redirect 차이

```text
301 Moved Permanently
→ 영구 이동, cache될 수 있음

302 Found
→ 임시 이동, 역사적으로 method 변경 동작이 혼재

303 See Other
→ POST 처리 후 GET으로 결과 페이지 조회할 때 유용

307 Temporary Redirect
→ 임시 이동, method와 body 유지

308 Permanent Redirect
→ 영구 이동, method와 body 유지
```

API의 POST body를 유지해야 한다면 302보다 307 또는 308의 의미가 명확하다.

## 6. HTTP 연결 관리

HTTP message는 application 의미이고 실제 전송은 TCP 또는 QUIC 연결 위에서 이루어진다.

### Persistent Connection

매 요청마다 TCP와 TLS 연결을 새로 만들면 handshake 비용이 반복된다. HTTP/1.1은 기본적으로 연결을 재사용할 수 있다.

```text
TCP 연결
→ TLS handshake
→ HTTP request 1 / response 1
→ HTTP request 2 / response 2
→ idle timeout 또는 close
```

```http
Connection: close
```

이 header는 해당 연결을 응답 후 닫겠다는 hop-by-hop 의미를 가진다.

### Keep-Alive와 Connection Pool

```text
HTTP keep-alive
→ 한 network connection을 여러 HTTP 요청에 재사용

Connection Pool
→ client가 미리 연결을 관리하고 요청에 빌려줌
```

외부 API client의 pool이 너무 작으면 요청이 연결을 기다리고, 너무 크면 상대 서버와 NAT, file descriptor에 부담을 줄 수 있다.

관찰할 항목:

```text
active connection
idle connection
pending acquire
connection lifetime
idle timeout
connect timeout
response timeout
```

### Timeout 종류

```text
DNS timeout
→ 이름 해석 대기

Connect timeout
→ TCP 또는 QUIC 연결 수립 대기

TLS handshake timeout
→ TLS 협상 대기

Response header timeout
→ 응답 시작 대기

Read timeout
→ 응답 데이터를 읽는 동안 대기

Idle timeout
→ 사용하지 않는 연결 유지 시간
```

Nginx, application, HTTP client, load balancer의 timeout이 서로 다르면 어느 계층이 먼저 연결을 끊는지에 따라 499, 502, 504 같은 증상이 달라질 수 있다.

### HTTP/1.1 Pipelining과 HOL Blocking

Pipelining은 응답을 기다리지 않고 같은 연결에 여러 요청을 연속 전송하는 방식이다. 응답은 요청 순서대로 와야 하므로 앞 응답이 느리면 뒤 응답도 막힌다.

이 문제와 구현 복잡성 때문에 browser에서는 널리 활용되지 않았고 HTTP/2 multiplexing이 등장했다.

## 7. Message Framing

HTTP/1.1에서는 body가 어디서 끝나는지 정확히 판단해야 한다.

### Content-Length

```http
Content-Length: 128
```

body의 길이를 byte 단위로 나타낸다. 문자 개수가 아니므로 UTF-8 한글 문자열의 글자 수와 다를 수 있다.

### Transfer-Encoding: chunked

전체 크기를 미리 모를 때 body를 chunk 단위로 보낼 수 있다.

```http
Transfer-Encoding: chunked
```

```text
4\r\n
Wiki\r\n
5\r\n
pedia\r\n
0\r\n
\r\n
```

각 chunk 앞에는 16진수 길이가 오고 길이 0인 chunk가 끝을 나타낸다.

`Transfer-Encoding`은 hop-by-hop header다. HTTP/2와 HTTP/3는 자체 frame 경계가 있으므로 HTTP/1.1의 chunked encoding을 사용하지 않는다.

### Content-Length와 Transfer-Encoding 충돌

Proxy와 backend가 message 길이를 서로 다르게 해석하면 한쪽은 남은 byte를 다음 요청으로 보고 다른 쪽은 현재 요청 body로 볼 수 있다. 이것이 HTTP Request Smuggling의 기반이 될 수 있다.

대응 원칙:

```text
모호한 framing을 가진 요청 거부
Proxy와 backend의 HTTP parser 최신 상태 유지
서로 다른 Content-Length 값이 여러 개면 거부
지원하지 않는 Transfer-Encoding 거부
edge에서 정규화한 뒤 backend와 일관되게 전달
```

## 8. Entity, Representation, Media Type

옛 문서에서는 message body를 entity라고 자주 표현했지만 현대 HTTP 의미론에서는 resource의 현재 표현을 representation이라고 설명한다.

Representation은 다음으로 구성된다.

```text
Representation Data
→ 실제 body byte

Representation Metadata
→ Content-Type, Content-Encoding, Content-Language 등
```

### Content-Type

```http
Content-Type: application/json; charset=utf-8
```

`Content-Type`은 현재 message body의 media type이다.

```text
application/json
text/html
text/plain
image/jpeg
application/octet-stream
multipart/form-data
```

Request의 `Content-Type`과 client가 원하는 응답을 나타내는 `Accept`를 혼동하면 안 된다.

```text
Content-Type → 내가 보내는 body 형식
Accept       → 내가 받고 싶은 응답 형식
```

### MIME Sniffing 주의

Browser가 서버의 `Content-Type`과 다르게 내용을 추측하면 예상하지 않은 script 실행 같은 문제가 생길 수 있다.

```http
X-Content-Type-Options: nosniff
```

정확한 `Content-Type`을 설정하고 browser의 임의 추측을 제한한다.

## 9. Content Encoding과 Transfer Encoding

### Content-Encoding

Representation data에 적용된 압축 방식을 나타낸다.

```http
Content-Encoding: br
```

```text
gzip → 널리 지원되는 압축
br   → Brotli 압축, text asset에서 효율적인 경우가 많음
```

Client는 지원하는 압축을 요청한다.

```http
Accept-Encoding: br, gzip
```

Server 또는 CDN은 하나를 선택한다.

```http
Content-Encoding: br
Vary: Accept-Encoding
```

이미 압축된 JPEG, PNG, ZIP을 다시 압축하면 CPU 비용만 늘고 크기가 거의 줄지 않을 수 있다.

### 두 Encoding의 차이

```text
Content-Encoding
→ representation 자체를 압축하거나 변환
→ end-to-end metadata

Transfer-Encoding
→ 특정 HTTP hop에서 message를 전송하는 방식
→ hop-by-hop metadata
```

`gzip`과 `chunked`는 동시에 적용될 수 있다. 먼저 representation을 gzip으로 압축하고, 전송할 때 chunk로 나눌 수 있다.

## 10. Multipart와 File Upload

파일과 일반 field를 함께 전송할 때 `multipart/form-data`를 사용한다.

```http
Content-Type: multipart/form-data; boundary=----boundary123
```

```text
------boundary123
Content-Disposition: form-data; name="description"

profile image
------boundary123
Content-Disposition: form-data; name="file"; filename="profile.png"
Content-Type: image/png

...binary data...
------boundary123--
```

`boundary`를 기준으로 각 part를 구분하고 part마다 별도 header와 body가 있다.

파일 업로드 보안:

```text
전체 요청과 개별 파일 크기 제한
확장자만 믿지 않고 실제 media type 확인
사용자 filename을 저장 경로로 직접 사용하지 않음
path traversal 차단
악성 파일 검사
실행 가능한 위치에 저장하지 않음
object storage에 저장할 때 권한 최소화
```

## 11. Range Request와 Download

큰 파일의 일부만 요청할 수 있다.

```http
Range: bytes=1000-1999
```

```http
HTTP/1.1 206 Partial Content
Content-Range: bytes 1000-1999/5000
Content-Length: 1000
```

사용처:

```text
동영상 seek
중단된 download 재개
대용량 object 일부 조회
```

요청 범위를 처리할 수 없으면 `416 Range Not Satisfiable`을 반환할 수 있다. Range를 지원한다고 무조건 빠른 것은 아니며 storage와 CDN이 범위 조회를 효율적으로 지원하는지 확인한다.

## 12. Streaming Response

전체 결과를 메모리에 만든 뒤 보내지 않고 준비되는 데이터부터 전송할 수 있다.

```text
대용량 file download
실시간 event
AI 생성 결과
대량 query 결과
```

주의점:

```text
중간에 실패했을 때 이미 status와 일부 body가 전송됐을 수 있음
Proxy buffering 때문에 client에 즉시 전달되지 않을 수 있음
긴 연결이 thread와 connection을 점유할 수 있음
idle timeout과 heartbeat 설정 필요
client 취소 감지와 resource 정리 필요
```

## 13. HTTP Cache 구조

Cache는 이전 응답을 저장하고 조건이 맞으면 origin에 다시 요청하지 않거나 더 적은 데이터만 주고받게 한다.

```text
Private Cache
→ 한 사용자 agent가 사용
→ Browser cache

Shared Cache
→ 여러 사용자가 공유
→ CDN, Forward Proxy, Reverse Proxy cache
```

Cache key는 기본적으로 method와 target URI를 바탕으로 한다. 내용 협상을 사용하면 `Vary`에 지정된 request header도 key 선택에 영향을 준다.

### Fresh와 Stale

```text
Fresh
→ 유효 기간 안이어서 origin 확인 없이 재사용 가능

Stale
→ 유효 기간이 지나 재검증 또는 새 응답이 필요
```

```http
Cache-Control: public, max-age=3600
```

한 시간 동안 fresh한 shared cache 가능한 응답을 의미한다.

### 주요 Cache-Control Directive

```text
max-age=60
→ client가 응답을 fresh하게 볼 시간

s-maxage=300
→ shared cache에 적용할 freshness, max-age보다 우선 가능

public
→ shared cache에 저장할 수 있음을 명시

private
→ private cache만 저장 가능

no-store
→ 응답을 저장하지 않도록 요구

no-cache
→ 저장은 가능하지만 재사용 전에 origin 재검증 필요

must-revalidate
→ stale 상태에서 임의로 재사용하지 말고 재검증

immutable
→ freshness 동안 내용이 바뀌지 않음을 알림

stale-while-revalidate
→ stale 응답을 잠시 제공하면서 background 재검증 허용
```

`no-cache`는 저장 금지가 아니다. 민감 정보처럼 저장 자체를 막고 싶으면 `no-store`를 사용한다.

### Cache 대상별 일반 전략

```text
hash가 포함된 JS/CSS/image
→ public, max-age가 길고 immutable

HTML entry document
→ 짧은 max-age 또는 no-cache

개인정보 API
→ private 또는 no-store

공개 조회 API
→ 명시적인 max-age, ETag, Vary 검토
```

## 14. Conditional Request와 재검증

### ETag

Server가 representation version을 식별하는 validator를 내려준다.

```http
ETag: "member-1-v7"
```

Client가 재검증한다.

```http
If-None-Match: "member-1-v7"
```

변경되지 않았으면 body 없이 응답할 수 있다.

```http
HTTP/1.1 304 Not Modified
ETag: "member-1-v7"
```

### Last-Modified

```http
Last-Modified: Fri, 11 Jul 2026 01:00:00 GMT
```

```http
If-Modified-Since: Fri, 11 Jul 2026 01:00:00 GMT
```

시각 정밀도와 여러 번 변경 후 원래 내용으로 돌아오는 문제 때문에 일반적으로 ETag가 더 정밀한 validator가 될 수 있다.

### Lost Update 방지

조건부 요청은 cache뿐 아니라 동시 수정에도 사용할 수 있다.

```http
PUT /documents/1 HTTP/1.1
If-Match: "document-v3"
```

현재 ETag가 다르면 `412 Precondition Failed`로 다른 사용자의 변경을 덮어쓰지 않게 할 수 있다.

## 15. Vary와 Cache Key

같은 URI라도 압축, 언어, media type에 따라 응답이 달라질 수 있다.

```http
Vary: Accept-Encoding, Accept-Language
```

Cache는 관련 request header 값이 맞는 저장 응답을 선택해야 한다.

`Vary`를 빠뜨리면 gzip을 지원하지 않는 client에 압축 응답을 주거나 한국어 사용자에게 영어 cache를 줄 수 있다. 반대로 너무 많은 header를 `Vary`에 넣으면 cache key가 지나치게 분산되어 hit rate가 떨어진다.

개인화 응답을 `Cookie` 전체로 vary하면 사용자마다 cache가 갈라질 수 있다. 공개 콘텐츠와 개인화 데이터를 분리하는 API 설계가 cache 효율에 더 좋을 수 있다.

## 16. 내용 협상

하나의 resource에 여러 representation이 있을 때 client와 server가 적절한 표현을 선택하는 과정이다.

### Media Type 협상

```http
Accept: application/json, application/xml;q=0.8
```

`q` 값은 선호도를 나타내며 기본값은 1이다.

```text
application/json       → q=1.0
application/xml;q=0.8  → q=0.8
```

Server가 허용 가능한 representation을 만들 수 없으면 `406 Not Acceptable`을 사용할 수 있다.

요청 body의 `Content-Type`을 server가 지원하지 않으면 `415 Unsupported Media Type`이 적절하다.

### 압축 협상

```http
Accept-Encoding: br;q=1.0, gzip;q=0.8, identity;q=0.1
```

Server는 가능한 encoding을 선택해 `Content-Encoding`으로 응답한다.

### 언어 협상

```http
Accept-Language: ko-KR, ko;q=0.9, en;q=0.7
```

```http
Content-Language: ko-KR
Vary: Accept-Language
```

언어 협상은 사용자 설정을 자동 추정하는 보조 수단이다. 사용자가 직접 선택한 언어 설정이 있다면 그것을 우선하는 것이 예측 가능하다.

### Server-Driven과 Agent-Driven

```text
Server-Driven Negotiation
→ request의 Accept 계열 header를 보고 server가 representation 선택

Agent-Driven Negotiation
→ server가 선택지를 제공하고 client가 다시 선택
```

투명 협상은 intermediary cache가 server 대신 variant를 선택하는 개념이지만 현대 애플리케이션에서는 일반적인 API 설계로 자주 직접 구현하지 않는다. `Vary`와 CDN cache key가 그와 연결되는 실무 요소다.

## 17. 국제화와 Charset

### UTF-8을 기본으로 두는 이유

UTF-8은 Unicode code point를 byte sequence로 표현하는 문자 encoding이다. ASCII와 호환되며 여러 언어를 하나의 encoding으로 다룰 수 있어 웹의 사실상 기본 선택이다.

```http
Content-Type: text/html; charset=utf-8
```

```text
문자 집합
→ 어떤 문자를 어떤 code point로 표현하는가?

문자 Encoding
→ code point를 실제 byte로 어떻게 변환하는가?
```

같은 byte를 서로 다른 charset으로 해석하면 글자가 깨진다.

JSON은 Unicode를 사용하며 현대 시스템에서는 UTF-8로 통일하는 것이 일반적이다. DB, application, connection, HTTP response의 encoding을 일관되게 맞춘다.

### Header의 비 ASCII 값

HTTP field는 일반적으로 제한된 문자 범위를 전제로 한다. 국제화된 filename처럼 non-ASCII가 필요한 field는 해당 header가 정의한 encoding 방식을 사용해야 한다.

```http
Content-Disposition: attachment; filename="report.pdf"; filename*=UTF-8''%EB%B3%B4%EA%B3%A0%EC%84%9C.pdf
```

문자열을 임의로 header에 넣으면 parsing 오류, header injection, client별 깨짐이 발생할 수 있다.

## 18. Cookie 전체 흐름

Cookie는 browser가 origin 관련 상태를 저장하고 조건이 맞는 요청에 자동으로 첨부하는 HTTP state management mechanism이다.

```http
Set-Cookie: session=abc123; Path=/; HttpOnly; Secure; SameSite=Lax
```

이후 browser 요청:

```http
Cookie: session=abc123
```

HTTP 자체는 stateless지만 Cookie와 server-side session을 조합해 로그인 상태를 이어갈 수 있다.

### Session Cookie와 Persistent Cookie

```text
Session Cookie
→ Expires와 Max-Age가 없음
→ browser session 기준으로 관리

Persistent Cookie
→ Expires 또는 Max-Age로 만료 시점 지정
```

```http
Set-Cookie: theme=dark; Max-Age=2592000
```

`Max-Age=0`은 cookie 삭제에 사용할 수 있다. 삭제할 때도 생성할 때 사용한 Domain과 Path 범위를 맞춰야 한다.

### Domain과 Host-Only

```text
Domain 없음
→ cookie를 설정한 host에만 전송되는 host-only cookie

Domain=example.com
→ 조건을 만족하면 example.com과 하위 domain에 전송 가능
```

필요 이상으로 넓은 Domain은 다른 subdomain의 취약점 영향을 키울 수 있으므로 host-only를 우선한다.

### Path

```http
Set-Cookie: adminSession=xyz; Path=/admin
```

Path는 cookie 전송 범위를 줄이지만 강력한 보안 경계로 보면 안 된다. 같은 origin의 client-side code와 server 구조를 함께 고려한다.

### Secure와 HttpOnly

```text
Secure
→ HTTPS 요청에서만 cookie 전송

HttpOnly
→ JavaScript의 document.cookie 접근 제한
```

HttpOnly는 XSS script가 cookie 값을 직접 읽는 위험을 줄이지만, XSS가 사용자의 browser에서 인증 요청을 보내는 것까지 막지는 않는다.

### SameSite

```text
Strict
→ cross-site 상황에서 가장 강하게 제한

Lax
→ 일부 top-level navigation 등 제한된 상황에서 전송

None
→ cross-site 요청에도 전송 가능
→ Secure가 함께 필요
```

Frontend와 API의 site 관계, OAuth redirect, embedded content 여부에 따라 설정한다. SameSite와 CORS는 서로 다른 정책이다.

### Cookie Prefix

```text
__Secure-
→ Secure 필요

__Host-
→ Secure, Path=/ 필요
→ Domain을 지정하지 않아 host 범위를 강제
```

지원하는 browser에서는 cookie 설정 실수를 줄이는 데 도움이 된다.

### Cookie와 CSRF

Browser는 요청한 JavaScript가 cookie 값을 몰라도 조건이 맞으면 cookie를 자동 전송한다. 공격 site가 사용자의 browser로 상태 변경 요청을 보내게 하는 것이 CSRF의 핵심이다.

대응:

```text
CSRF token
SameSite cookie
Origin 또는 Referer 검증
GET으로 상태를 변경하지 않음
중요 작업 재인증
```

## 19. 클라이언트 식별 수단과 한계

```text
IP Address
→ NAT, mobile network, proxy 때문에 여러 사용자가 공유하거나 자주 변경

User-Agent
→ client가 보내는 문자열이며 변경 가능

Cookie
→ browser profile 단위 상태, 삭제·차단 가능

Session ID
→ server-side 로그인 상태 식별자, 탈취되면 위험

Access Token
→ 인증과 권한 정보를 전달하는 credential

TLS Client Certificate
→ 강한 client 인증에 사용할 수 있지만 운영 복잡도가 큼
```

IP와 User-Agent만으로 사용자를 인증하면 안 된다. 기기 fingerprinting은 정확하지 않고 개인정보와 규제 문제도 있으므로 목적과 동의를 명확히 해야 한다.

## 20. Authorization Header와 인증 방식

### Basic Authentication

```http
Authorization: Basic dXNlcjpwYXNzd29yZA==
```

`username:password`를 Base64로 표현할 뿐 암호화가 아니다. TLS 없이 사용하면 credential이 노출된다.

특징:

```text
매 요청에 credential 전달
구현이 단순
세밀한 logout과 token 폐기 기능이 부족
browser 기본 login UI와 제한적인 내부 도구에 사용 가능
반드시 HTTPS와 함께 사용
```

일반 사용자 서비스의 주 인증 방식으로는 session, OAuth/OIDC, 짧은 access token 같은 방식을 더 많이 사용한다.

### Digest Authentication

Digest 인증은 password 자체 대신 nonce와 request 정보로 계산한 digest를 보내 replay와 평문 password 전송 문제를 줄이려 했다.

하지만 현대 password hashing, MFA, OAuth/OIDC, TLS 기반 인증 흐름과 잘 맞지 않고 algorithm과 상호운용 제약이 있어 일반적인 웹 서비스에서는 거의 선택하지 않는다.

학습할 핵심만 남긴다.

```text
Basic보다 password 원문 노출을 줄이려던 역사적 방식
nonce를 사용해 단순 replay를 완화
TLS를 대체하지 못함
새 시스템의 기본 인증 방식으로 선택하지 않음
```

### Bearer Token

```http
Authorization: Bearer eyJ...
```

Bearer는 token을 가진 주체가 사용할 수 있다는 의미이므로 탈취 방지가 중요하다.

```text
HTTPS 필수
짧은 access token 만료
scope와 audience 최소화
log와 URL에 token을 남기지 않음
refresh token 별도 보호
```

## 21. HTTPS와 TLS 기본 원리

HTTPS는 HTTP 의미를 TLS로 보호해 전송하는 구조다.

```text
HTTP Semantics
→ TLS가 암호화·무결성·상대 인증 제공
→ TCP 또는 QUIC으로 전송
```

TLS의 주요 목표:

```text
Confidentiality
→ 중간에서 내용을 읽기 어렵게 암호화

Integrity
→ 전송 중 변경을 탐지

Authentication
→ 일반적으로 client가 server 인증서를 검증
```

### 대칭키와 비대칭키

```text
대칭키 암호
→ 같은 secret으로 암호화와 복호화
→ 빠르므로 실제 application data 보호에 사용

비대칭키 암호와 서명
→ public key와 private key 사용
→ server 신원 증명과 key establishment에 활용
```

TLS는 handshake에서 상대를 인증하고 안전하게 shared secret을 만든 뒤, 그 secret에서 파생한 대칭키로 application data를 효율적으로 보호한다.

## 22. TLS 1.3 Handshake

단순화한 흐름:

```text
ClientHello
→ 지원 TLS version
→ cipher suite
→ key share
→ SNI
→ ALPN

ServerHello
→ 선택한 version과 cipher suite
→ server key share

EncryptedExtensions
Certificate
CertificateVerify
Finished

Client Finished
→ Application Data
```

실제 handshake 세부는 구현과 session resumption 여부에 따라 달라질 수 있다.

### SNI

ClientHello에서 접속하려는 server name을 전달해 하나의 IP나 load balancer가 도메인에 맞는 인증서를 선택하도록 한다.

### ALPN

TLS handshake에서 application protocol을 협상한다.

```text
h2     → HTTP/2
http/1.1 → HTTP/1.1
h3     → HTTP/3 관련 협상과 discovery에 연결
```

### 인증서 검증

Client는 일반적으로 다음을 확인한다.

```text
요청 host와 인증서 이름이 일치하는가?
인증서 유효 기간 안인가?
신뢰한 root CA까지 chain이 연결되는가?
인증서 서명이 올바른가?
허용한 key usage와 algorithm인가?
```

인증서 경고를 무시하면 암호화 연결은 생기더라도 공격자 server와 연결됐을 가능성을 배제할 수 없다.

## 23. TLS Session Resumption과 0-RTT

이전에 연결한 정보를 이용해 full handshake 비용을 줄일 수 있다.

```text
Session Resumption
→ 이전 session에서 얻은 ticket과 PSK를 이용해 협상 비용 감소

0-RTT Early Data
→ 조건이 맞으면 handshake 완료 전에 application data 전송
```

TLS 1.3의 0-RTT data는 connection 사이 replay 방지가 자동으로 보장되지 않는다. 결제, 주문 생성처럼 replay에 민감한 non-idempotent 요청에는 신중해야 한다.

## 24. HSTS와 Mixed Content

### HSTS

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Browser가 일정 기간 해당 host를 HTTPS로만 접속하도록 기억한다. HTTP 접속 후 redirect하기 전에 HTTPS를 선택하므로 downgrade와 cookie 탈취 위험을 줄일 수 있다.

주의:

```text
HTTPS 응답에서 설정
includeSubDomains 적용 전 모든 subdomain의 HTTPS 준비 확인
긴 max-age와 preload는 되돌리기 어려우므로 단계적으로 적용
인증서 오류를 우회하게 만드는 기능이 아님
```

### Mixed Content

HTTPS page가 HTTP script, image, API를 불러오는 상황이다. 능동 콘텐츠는 차단될 수 있고 보안도 약해진다.

Frontend asset, API URL, WebSocket URL까지 모두 안전한 scheme을 사용해야 한다.

## 25. TLS Termination과 End-to-End Encryption

```text
Client
→ HTTPS
→ ALB에서 TLS termination
→ HTTP 또는 HTTPS
→ Nginx / Application
```

TLS를 ALB에서 종료하면 인증서 중앙 관리와 offloading이 쉽다. 내부 구간의 위협 모델이나 규정상 암호화가 필요하면 backend까지 HTTPS를 유지하거나 service mesh mTLS를 적용할 수 있다.

TLS termination 뒤 application이 원래 요청 scheme을 알아야 한다면 신뢰한 proxy가 전달한 정보를 사용한다.

```http
X-Forwarded-Proto: https
```

모든 외부 client가 보낸 forwarded header를 그대로 신뢰하면 scheme과 client IP를 위조할 수 있다.

## 26. HTTP/2 구조

HTTP/2는 HTTP method, status, header의 의미를 바꾸는 것이 아니라 전송 표현을 binary framing으로 바꾼다.

```text
HTTP Semantics
→ Message
→ Stream
→ Frame
→ 하나의 TCP Connection
```

### Frame

HTTP/2 통신의 작은 protocol 단위다.

```text
HEADERS
→ request 또는 response header block

DATA
→ body data

SETTINGS
→ connection parameter 교환

WINDOW_UPDATE
→ flow-control window 증가

RST_STREAM
→ 특정 stream 취소

GOAWAY
→ connection 종료 예고
```

각 frame에는 type, flag, stream ID와 payload가 있다.

### Stream

하나의 request/response 교환을 구성하는 독립적인 양방향 frame 흐름이다.

```text
TCP Connection 1개
├─ Stream 1: GET /members
├─ Stream 3: GET /orders
└─ Stream 5: POST /logs
```

frame이 섞여 전송돼도 stream ID로 다시 조립할 수 있다.

### Multiplexing

HTTP/1.1처럼 응답 순서를 connection 전체에서 강제하지 않고 여러 stream을 동시에 진행한다. 하나의 느린 HTTP response 때문에 다른 response가 application layer에서 순서대로 기다리는 문제를 줄인다.

## 27. HPACK과 Header Compression

HTTP request마다 Cookie, User-Agent 같은 큰 header가 반복될 수 있다. HTTP/2는 HPACK으로 header field를 압축한다.

```text
Static Table
→ 자주 쓰는 header name과 값을 미리 정의

Dynamic Table
→ connection에서 반복되는 field를 index로 재사용

Huffman Coding
→ 문자열 표현 크기 감소
```

Header compression state는 connection 단위로 관리되므로 intermediary가 HTTP/2 connection을 새로 만들면 별도 상태를 가진다.

## 28. HTTP/2 Flow Control과 HOL

### Flow Control

빠른 sender가 느린 receiver의 memory를 압도하지 않도록 전송량을 제한한다.

```text
Stream-Level Window
→ 특정 stream의 DATA 전송량 제어

Connection-Level Window
→ connection 전체 DATA 전송량 제어

WINDOW_UPDATE
→ receiver가 추가로 받을 수 있는 byte 수 알림
```

### TCP Head-of-Line Blocking

HTTP/2 stream은 논리적으로 독립적이지만 모두 하나의 순서 있는 TCP byte stream을 공유한다. TCP packet 하나가 손실되면 재전송될 때까지 뒤 byte를 application에 전달하지 못해 다른 HTTP/2 stream도 함께 지연될 수 있다.

HTTP/2가 해결한 것과 남은 것:

```text
해결 또는 완화
→ HTTP/1.1 application-level 응답 순서 대기

남음
→ TCP packet loss로 인한 transport-level HOL blocking
```

## 29. HTTP/2 운영 관점

```text
Client ↔ CDN/ALB는 HTTP/2
ALB ↔ Backend는 HTTP/1.1
```

이런 protocol 변환은 흔하다. 외부가 HTTP/2라고 backend application까지 반드시 HTTP/2인 것은 아니다.

확인할 항목:

```text
TLS ALPN으로 h2가 협상됐는가?
Proxy와 upstream 사이 protocol은 무엇인가?
동시 stream 제한은 얼마인가?
긴 stream 하나가 connection flow control을 압박하는가?
GOAWAY 이후 안전하게 재연결하는가?
```

Server Push는 server가 client 요청 전에 resource를 미리 보내는 기능이지만 cache와 browser preload 동작이 복잡하고 실제 효율이 제한적이어서 현대 browser 환경에서 핵심 최적화 수단으로 보지 않는다.

## 30. HTTP/3와 QUIC

HTTP/3는 HTTP 의미론을 QUIC transport 위에서 전달한다.

```text
HTTP/1.1 → TCP, 일반적으로 TLS
HTTP/2   → TCP, browser에서는 일반적으로 TLS
HTTP/3   → QUIC, UDP 기반, TLS 1.3 통합
```

QUIC은 connection 안에 여러 독립 stream을 제공한다. 한 stream의 packet 손실이 다른 stream의 순서 있는 전달까지 모두 막지 않도록 설계되어 HTTP/2의 TCP-level HOL 문제를 줄인다.

### QPACK

HTTP/3는 header compression에 QPACK을 사용한다. QUIC stream은 서로 독립적으로 전달될 수 있어 HTTP/2의 HPACK을 그대로 사용하면 압축 table update 순서 때문에 blocking이 생길 수 있으므로 구조가 조정됐다.

### Alt-Svc와 HTTP/3 발견

HTTP/3는 TCP가 아닌 QUIC endpoint를 사용하므로 client가 해당 origin의 HTTP/3 지원 여부를 알아야 한다. Server가 HTTP/1.1 또는 HTTP/2 응답에서 Alternative Services를 알릴 수 있다.

```http
Alt-Svc: h3=":443"; ma=86400
```

Client는 지원 여부와 network 상태에 따라 QUIC 연결을 시도하고 실패하면 HTTP/2나 HTTP/1.1로 fallback할 수 있다. DNS의 HTTPS resource record나 client가 이전에 기억한 정보도 protocol 선택에 활용될 수 있다.

### Connection Migration

QUIC connection은 IP와 port 조합만이 아니라 connection ID를 사용해 Wi-Fi에서 mobile network로 전환되는 상황에서도 연결을 이어갈 수 있다.

### HTTP/3 주의점

```text
UDP 443이 network 또는 firewall에서 차단될 수 있음
지원하지 않으면 HTTP/2나 HTTP/1.1로 fallback 필요
QUIC 자체가 application 처리 시간을 줄여주지는 않음
0-RTT를 non-idempotent 요청에 사용할 때 replay 위험 고려
```

## 31. Web Server, WAS, Origin Server

웹 서버 장 전체를 외울 필요는 없지만 역할은 구분해야 한다.

```text
Web Server
→ HTTP connection, 정적 file, TLS, proxy 기능
→ Nginx, Apache HTTP Server

WAS / Application Server
→ application code 실행과 동적 응답
→ Tomcat을 포함한 Spring Boot application 등

Origin Server
→ 최종 콘텐츠의 원본 응답을 책임지는 server
→ CDN 관점에서는 application 또는 storage가 origin이 될 수 있음
```

한 process가 여러 역할을 동시에 수행할 수도 있다. 이름보다 현재 architecture에서 어디가 TLS, routing, cache, application logic을 담당하는지 보는 것이 중요하다.

운영 기능:

```text
Virtual Host와 Host routing
정적 파일 제공
Reverse Proxy
Connection와 Timeout 관리
Request size 제한
Access/Error Log
Graceful Shutdown
Health Check
```

## 32. Proxy의 현대적 의미

```text
Forward Proxy
→ client를 대신해 외부 server에 요청

Reverse Proxy
→ server 앞에서 요청을 받아 내부 backend로 전달

CDN Edge
→ 사용자 가까이에서 cache, TLS, WAF, proxy 역할

Service Mesh Proxy
→ service 간 traffic, mTLS, retry, telemetry 처리
```

Proxy는 HTTP message를 읽고 변경할 수 있는 intermediary다. Hop-by-hop header 제거, Host 전달, body 크기, buffering, timeout, retry 정책이 요청 결과에 영향을 준다.

## 33. Forwarded Header와 신뢰 경계

```http
Forwarded: for=203.0.113.10;proto=https;host=api.example.com
```

현장에서 자주 보는 비표준 계열:

```http
X-Forwarded-For: 203.0.113.10, 10.0.1.20
X-Forwarded-Proto: https
X-Forwarded-Host: api.example.com
```

`X-Forwarded-For`는 proxy를 거칠 때 값이 이어질 수 있다. 무조건 첫 값이나 마지막 값을 선택하는 방식보다 신뢰하는 proxy 대역과 hop 수를 설정해 오른쪽부터 신뢰 경계를 벗어나는 client 주소를 계산한다.

외부에서 직접 application에 접근할 수 있으면 공격자가 header를 임의 설정할 수 있다. application port를 private network에 두고 신뢰한 load balancer와 proxy만 접근하도록 제한한다.

## 34. Gateway, Tunnel, Relay

### API Gateway

```text
Authentication과 Authorization
Rate Limiting
Request Routing
API Key와 Usage Plan
Request/Response Transformation
Logging과 Metric
```

단순 Reverse Proxy보다 API 운영 정책을 중앙화하는 기능이 많다. 모든 비즈니스 권한을 Gateway에만 두면 내부 호출이나 우회 경로에서 규칙이 빠질 수 있으므로 resource 권한은 application에서도 확인한다.

### CONNECT Tunnel

Forward Proxy를 통해 특정 host와 TCP tunnel을 만든다.

```http
CONNECT example.com:443 HTTP/1.1
Host: example.com:443
```

Proxy가 성공하면 이후 TLS byte를 tunnel로 중계할 수 있다. 기업 proxy, HTTPS proxying, 개발 도구에서 볼 수 있다.

허용 대상과 port를 제한하지 않으면 내부망 접근이나 임의 tunnel로 악용될 수 있다.

### TLS Passthrough

중간 proxy가 TLS를 복호화하지 않고 TCP 수준에서 backend로 전달한다. backend가 인증서를 가지며 proxy는 HTTP path를 볼 수 없어 L7 routing과 header 조작이 제한된다.

### Relay

수신한 protocol data를 다른 연결로 전달하는 일반적인 중계 개념이다. 제품 용어를 외우기보다 중간 장비가 어느 계층까지 해석하고 어디서 새 연결을 만드는지 확인한다.

## 35. Protocol Upgrade, WebSocket, SSE, gRPC

### WebSocket Upgrade

HTTP/1.1 요청으로 시작해 protocol 전환을 요청할 수 있다.

```http
Connection: Upgrade
Upgrade: websocket
```

성공 시 `101 Switching Protocols` 이후 WebSocket frame을 주고받는다. Reverse Proxy에서는 Upgrade 관련 header 전달과 긴 idle timeout 설정이 필요하다.

### Server-Sent Events

```http
Content-Type: text/event-stream
```

Server에서 client로 단방향 event stream을 제공한다. 일반 HTTP와 재연결 방식을 사용해 알림과 진행 상태 전달에 적합하다.

### gRPC

일반적으로 HTTP/2 stream과 binary message format을 활용한다. Browser REST API와 동일하지 않으며 load balancer, proxy의 HTTP/2 upstream 지원과 timeout 설정을 확인해야 한다.

## 36. Web Robot과 robots.txt

웹 로봇 전체를 깊게 공부할 필요는 없지만 crawler가 서비스에 접근하는 방식과 부하 영향은 알아야 한다.

```text
검색 엔진 crawler
링크 preview bot
보안 scanner
악성 scraper
내부 monitoring bot
```

`robots.txt` 예:

```text
User-agent: *
Disallow: /admin/
```

중요한 점:

```text
robots.txt는 자발적으로 따르는 crawler 정책
인증이나 접근 제어 기능이 아님
민감한 URL을 적으면 오히려 경로가 공개될 수 있음
악성 bot은 무시할 수 있음
```

실제 보호에는 인증, WAF, rate limiting, bot management, resource 제한이 필요하다.

## 37. CORS와 Browser Security

CORS는 browser가 다른 origin의 response를 frontend JavaScript에 공개할지 결정하는 정책이다. Server-to-server 요청 자체를 막는 network 보안 기능이 아니다.

### Simple Request와 Preflight

조건을 벗어나는 cross-origin 요청 전에 browser가 OPTIONS preflight를 보낼 수 있다.

```http
OPTIONS /members HTTP/1.1
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization
```

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

Credential을 허용할 때 `Access-Control-Allow-Origin: *`를 사용할 수 없다. 허용할 origin을 명확히 검증한다.

### 주요 보안 Header

```text
Strict-Transport-Security
→ HTTPS 강제 정책

Content-Security-Policy
→ script, image, connect source 제한

X-Content-Type-Options: nosniff
→ media type 추측 제한

Referrer-Policy
→ 다른 site로 보낼 referrer 정보 범위 제어

Permissions-Policy
→ camera, microphone 등 browser 기능 범위 제어

frame-ancestors 또는 X-Frame-Options
→ clickjacking 방어
```

Header 하나로 모든 공격을 막을 수 없으며 입력 검증, 출력 encoding, session 보안과 함께 사용한다.

## 38. Transcoding의 현대적 사용

Transcoding은 intermediary가 content 표현을 다른 형식으로 변환하는 개념이다.

현대적인 예:

```text
CDN이 gzip 또는 Brotli 압축
원본 image를 WebP나 AVIF로 변환
화면 크기에 맞게 image resize
동영상을 여러 bitrate와 codec으로 변환
```

주의점:

```text
변환 결과별 cache key와 Vary
Content-Type과 Content-Encoding 정확성
원본 품질 손실
CPU 비용
서명된 콘텐츠와 무결성 검증 영향
```

옛 투명 proxy 협상 세부를 외우기보다 CDN이 어떤 request header와 device 정보로 variant를 선택하고 cache하는지 이해하는 것이 실용적이다.

## 39. 콘텐츠 발행과 배포의 현대적 구조

과거 웹 발행 도구의 세부는 제외해도 되지만 다음 구조는 cloud 학습과 직접 연결된다.

```text
사용자
→ DNS
→ CDN Edge
→ WAF / Load Balancer
→ Origin Server 또는 Object Storage
```

### 정적 Asset 배포

```text
파일명에 content hash 포함
→ app.8f31c2.js

긴 Cache-Control
→ public, max-age=31536000, immutable

HTML은 짧게 cache
→ 새 hash asset을 참조하도록 빠르게 갱신
```

같은 파일명으로 내용을 바꾸고 CDN invalidation에만 의존하면 edge와 browser에 이전 파일이 남을 수 있다. Content-addressed filename이 더 예측 가능하다.

### CDN과 Origin

```text
CDN hit
→ edge가 바로 응답

CDN miss
→ origin에서 가져와 정책에 따라 저장
```

Origin은 public internet에 직접 열지 않고 CDN 또는 load balancer만 접근하게 제한할 수 있다. Cache key, Query String, Cookie, Authorization 전달 정책을 명확히 설정한다.

### Signed URL과 Private Content

제한된 시간 동안 특정 object 접근을 허용하는 서명 URL을 사용할 수 있다.

```text
만료 시간
resource path
서명
선택적인 client 조건
```

URL은 browser history, log, referrer에 남을 수 있으므로 만료 시간을 짧게 하고 민감 token logging을 피한다.

## 40. 현대 HTTP 장애 분석 순서

```text
1. DNS가 올바른 IP 또는 CDN을 가리키는가?
2. TCP 또는 QUIC 연결이 되는가?
3. TLS version, SNI, 인증서, ALPN 협상이 정상인가?
4. 실제 HTTP version은 무엇인가?
5. Request method, Host, path, query가 올바른가?
6. Content-Type, Content-Length, Encoding이 올바른가?
7. Cookie와 Authorization이 전달되는가?
8. CORS preflight와 credential 설정이 맞는가?
9. CDN 또는 browser cache가 이전 응답을 반환하는가?
10. Proxy timeout, buffering, retry가 요청을 변경하는가?
11. Application log와 trace에 요청이 도착했는가?
12. Response status, header, body가 어느 계층에서 생성됐는가?
```

확인 명령:

```bash
curl -v https://api.example.com/members/1
curl -I https://example.com/app.js
curl --http2 -v https://example.com
curl --compressed -v https://example.com/app.js
openssl s_client -connect example.com:443 -servername example.com -alpn h2
```

`curl`이 지원하는 protocol은 설치된 build에 따라 다를 수 있다.

## 41. 우선순위별 학습 순서

### 우선순위 상

```text
HTTP message와 method 의미론
Safe와 Idempotent
Status와 Redirect
Connection 재사용과 Timeout
Message Framing
Content-Type, Content-Length, Encoding
Cookie 보안
TLS 1.3과 인증서
HTTP/2 Frame, Stream, Multiplexing
HTTP/3와 QUIC 차이
내용 협상과 Vary
```

### 우선순위 중

```text
Cache directive와 재검증
Range와 Streaming
국제화와 UTF-8
CDN과 콘텐츠 배포
CORS와 보안 Header
SSE, WebSocket, gRPC
```

### 개념만 알면 되는 부분

```text
Digest Authentication 계산 방식
과거 투명 내용 협상 구현
옛 Proxy 제품별 용어
웹 로봇의 세부 crawler algorithm
과거 웹 콘텐츠 발행 도구
```

## 42. 직접 설명할 때 핵심 문장

```text
HTTP는 resource에 대한 요청과 representation 전달의 의미를 정의하는 stateless application protocol이다.
HTTP/1.1에서는 Content-Length와 chunked encoding으로 message 경계를 판단하고, 해석 차이는 request smuggling 같은 보안 문제로 이어질 수 있다.
HTTP cache는 freshness와 validator를 이용하며 ETag, Cache-Control, Vary를 함께 이해해야 한다.
Cookie는 browser가 조건에 맞는 요청에 자동 첨부하는 상태 정보이므로 Secure, HttpOnly, SameSite와 CSRF를 함께 봐야 한다.
TLS는 암호화, 무결성, server 인증을 제공하고 SNI와 ALPN으로 host와 application protocol 선택을 돕는다.
HTTP/2는 TCP 연결 안에서 frame과 stream을 multiplexing하고, HTTP/3는 QUIC stream으로 TCP 수준의 head-of-line blocking을 줄인다.
제외된 옛 기술은 세부 구현까지 외울 필요는 없지만 현대 API Gateway, CDN, 인증, tunnel, crawler 보안으로 이어지는 핵심 개념은 알아야 한다.
```

## 공식 참고 자료

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [RFC 9112: HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)
- [RFC 9113: HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)
- [RFC 9114: HTTP/3](https://www.rfc-editor.org/rfc/rfc9114.html)
- [RFC 8446: TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html)
- [RFC 6797: HTTP Strict Transport Security](https://www.rfc-editor.org/rfc/rfc6797.html)
- [Fetch Standard: CORS](https://fetch.spec.whatwg.org/)
