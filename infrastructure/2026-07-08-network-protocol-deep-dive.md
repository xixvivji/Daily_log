# 2026-07-08 네트워크 프로토콜 심화: TCP, DNS, HTTP, TLS

## 핵심 관점

이 문서는 TCP, DNS, HTTP, TLS 각각의 세부 내용을 반복하는 전용 심화 문서가 아니라, 한 요청에서 네 protocol이 어떤 순서로 연결되고 장애 계층을 어떻게 구분하는지 보는 통합 문서다.

- [TCP 심화](2026-07-10-tcp-deep-dive.md)
- [DNS 심화](2026-07-10-dns-deep-dive.md)
- [HTTP와 HTTPS 심화](2026-07-10-http-https-deep-dive.md)
- [현대 HTTP 완성](2026-07-11-modern-http-complete-guide.md)

지금까지 정리한 내용은 아래 흐름을 이해하는 데 집중했다.

```text
사용자
→ DNS
→ ALB 또는 EC2
→ Nginx
→ Docker container
→ Backend application
```

이제 더 깊게 봐야 하는 부분은 요청이 실제로 실패했을 때 어느 계층에서 문제가 났는지 구분하는 능력이다.

```text
DNS가 실패한 것인가?
TCP 연결이 실패한 것인가?
TLS 핸드셰이크가 실패한 것인가?
HTTP 요청은 갔는데 애플리케이션이 실패한 것인가?
프록시가 upstream 응답을 못 받은 것인가?
```

운영에서 "사이트가 안 열린다"는 말은 너무 넓다.

실제로는 아래 중 하나일 수 있다.

```text
도메인이 잘못된 IP를 가리킴
DNS 캐시가 오래된 값을 들고 있음
서버 포트가 열려 있지 않음
Security Group이 막고 있음
TCP 연결은 되지만 TLS 인증서가 잘못됨
TLS는 되지만 HTTP Host나 path 라우팅이 잘못됨
Nginx는 받았지만 upstream container가 죽어 있음
백엔드는 살아 있지만 DB 연결이 실패함
```

그래서 다음 학습은 네트워크 심화 중에서도 운영 장애 분석과 가장 많이 연결되는 주제부터 보는 것이 좋다.

```text
1. IP 주소와 CIDR
2. TCP 연결 과정
3. DNS 조회 흐름
4. HTTP 요청과 응답
5. HTTPS / TLS 핸드셰이크
6. Timeout과 Connection 관리
7. 실제 장애 구분 방법
```

## 1. IP 주소와 CIDR

### IP 주소를 더 봐야 하는 이유

IP 주소는 네트워크에서 장비를 찾기 위한 논리 주소다.

이미 IP와 MAC의 차이는 정리했지만, 클라우드와 Docker를 보면 IP 주소를 더 정확히 읽을 수 있어야 한다.

예:

```text
VPC CIDR: 10.0.0.0/16
public subnet: 10.0.1.0/24
private subnet: 10.0.2.0/24
Docker bridge: 172.17.0.0/16
내 로컬 공유기 대역: 192.168.0.0/24
```

이 숫자를 보면 아래 질문에 답할 수 있어야 한다.

```text
같은 네트워크 대역인가?
서로 라우팅이 필요한가?
IP 범위가 겹치지 않는가?
Subnet을 더 나눌 수 있는가?
라우팅 테이블에 어떤 대역을 넣어야 하는가?
```

### CIDR 표기

CIDR은 IP 대역을 표현하는 방식이다.

```text
10.0.0.0/16
192.168.0.0/24
172.17.0.0/16
```

뒤의 `/숫자`는 네트워크 부분이 몇 비트인지 나타낸다.

IPv4는 32비트다.

```text
/24
→ 앞 24비트가 네트워크 부분
→ 뒤 8비트가 호스트 부분
→ 2^8 = 256개 주소
```

예:

```text
192.168.0.0/24
주소 범위: 192.168.0.0 ~ 192.168.0.255
```

실제로 모든 주소를 장비에 줄 수 있는 것은 아니다.

보통 네트워크 주소와 브로드캐스트 주소 같은 특수 주소가 있다.

AWS subnet에서도 일부 IP는 AWS가 예약한다.

### /16과 /24 차이

```text
10.0.0.0/16
→ 대략 10.0.0.0 ~ 10.0.255.255
→ 큰 네트워크

10.0.1.0/24
→ 대략 10.0.1.0 ~ 10.0.1.255
→ 더 작은 subnet
```

VPC를 `/16`으로 만들고, subnet을 `/24`로 나누는 구조가 자주 쓰인다.

```text
VPC: 10.0.0.0/16

public-a: 10.0.1.0/24
public-c: 10.0.2.0/24
private-a: 10.0.11.0/24
private-c: 10.0.12.0/24
```

이렇게 나누면 가용 영역별로 public/private subnet을 분리할 수 있다.

### IP 대역이 겹치면 생기는 문제

서로 연결해야 하는 네트워크의 CIDR이 겹치면 라우팅이 애매해진다.

예:

```text
회사 내부망: 10.0.0.0/16
AWS VPC: 10.0.0.0/16
```

VPN으로 연결하려고 하면 문제가 생길 수 있다.

```text
10.0.1.20으로 가는 패킷이 회사 내부 장비를 의미하는가?
AWS EC2를 의미하는가?
```

그래서 VPC CIDR은 나중에 연결될 네트워크와 겹치지 않게 잡는 것이 중요하다.

## 2. TCP 연결 과정

### TCP를 알아야 하는 이유

HTTP, HTTPS, SSH, MySQL, PostgreSQL 같은 많은 프로토콜은 TCP 위에서 동작한다.

```text
HTTP → TCP
HTTPS → TLS → TCP
SSH → TCP
MySQL → TCP
PostgreSQL → TCP
```

그래서 웹 요청이 실패했을 때도 먼저 TCP 연결이 되는지 봐야 한다.

```text
DNS 성공
→ IP 확인
→ TCP 연결 시도
→ TLS 협상
→ HTTP 요청
```

TCP 연결 자체가 안 되면 HTTP 문제를 볼 단계가 아니다.

### 3-way handshake

TCP 연결은 보통 3-way handshake로 시작한다.

```text
Client → Server: SYN
Server → Client: SYN-ACK
Client → Server: ACK
```

의미:

```text
SYN
→ 연결을 시작하고 싶다.

SYN-ACK
→ 요청을 받았고 나도 연결 준비가 됐다.

ACK
→ 확인했다. 이제 데이터를 주고받자.
```

예를 들어 브라우저가 `https://example.com`에 접속하면 443 포트로 TCP 연결을 먼저 맺는다.

```text
브라우저
→ example.com:443
→ TCP 3-way handshake
→ TLS handshake
→ HTTP request
```

### TCP 연결 실패 유형

TCP 연결 단계에서 자주 보는 실패는 크게 세 가지다.

```text
connection refused
connection timed out
no route to host
```

`connection refused`:

```text
대상 IP까지는 갔지만 해당 포트에서 듣는 프로세스가 없음
또는 방화벽이 거절 응답을 보냄
```

예:

```text
Nginx가 127.0.0.1:8080으로 proxy_pass
하지만 8080에 backend container가 안 떠 있음
→ connection refused
→ Nginx 502 가능
```

`connection timed out`:

```text
패킷을 보냈지만 응답이 오지 않음
방화벽, Security Group, NACL, 라우팅 문제 가능
```

예:

```text
ALB가 EC2:80으로 요청
EC2 Security Group이 ALB 요청을 허용하지 않음
→ timeout 또는 unhealthy target
```

`no route to host`:

```text
목적지로 가는 라우팅 경로를 찾지 못함
route table, gateway, network 설정 문제 가능
```

### TCP 종료와 TIME_WAIT

TCP 연결은 종료할 때도 절차가 있다.

일반적으로 FIN과 ACK를 주고받으며 닫는다.

연결이 닫힌 뒤에도 한쪽은 잠깐 `TIME_WAIT` 상태에 머문다.

이유:

```text
늦게 도착하는 패킷이 새 연결에 섞이지 않게 함
상대방이 마지막 ACK를 못 받았을 때 재전송에 대응함
```

서버에서 연결이 매우 많이 생기면 `TIME_WAIT`가 많이 보일 수 있다.

운영에서 중요한 점:

```text
TIME_WAIT 자체는 정상 TCP 동작이다.
하지만 너무 많이 쌓이면 connection reuse, keep-alive, 커널 파라미터, 애플리케이션 연결 관리도 봐야 한다.
```

## 3. DNS 조회 흐름

### DNS를 더 봐야 하는 이유

DNS는 도메인 이름을 IP 주소나 다른 도메인 이름으로 바꿔준다.

```text
api.example.com
→ 203.0.113.10
```

또는 ALB를 쓸 때는:

```text
api.example.com
→ my-alb-123.ap-northeast-2.elb.amazonaws.com
```

사이트가 안 열릴 때 DNS가 틀리면 서버와 애플리케이션은 멀쩡해도 접속이 안 된다.

### DNS 조회 순서

브라우저가 도메인을 입력받으면 바로 authoritative DNS로 가지 않는다.

대략 아래 흐름을 거친다.

```text
브라우저 캐시
→ OS 캐시
→ 로컬 DNS resolver
→ recursive resolver
→ root DNS
→ TLD DNS
→ authoritative DNS
```

예:

```text
api.example.com
```

조회 흐름:

```text
root DNS
→ .com 담당 TLD DNS 알려줌

.com TLD DNS
→ example.com authoritative DNS 알려줌

example.com authoritative DNS
→ api.example.com 레코드 응답
```

사용자는 보통 이 전체 과정을 직접 보지 않는다.

대부분은 ISP DNS, 회사 DNS, Google DNS, Cloudflare DNS 같은 recursive resolver가 대신 처리한다.

### A, CNAME, Alias 차이

A Record:

```text
도메인 → IPv4 주소
```

예:

```text
api.example.com → 203.0.113.10
```

CNAME:

```text
도메인 → 다른 도메인
```

예:

```text
www.example.com → example.com
```

Route 53 Alias:

```text
도메인 → AWS 리소스
```

예:

```text
api.example.com
→ ALB
```

ALB는 IP가 바뀔 수 있으므로 A Record에 ALB IP를 직접 넣는 것보다 Alias로 연결하는 것이 운영에 맞다.

### TTL과 캐시

TTL은 DNS 응답을 얼마나 오래 캐싱할지 정하는 값이다.

```text
TTL 300
→ 300초 동안 캐싱 가능
```

DNS 레코드를 바꿨는데 바로 반영되지 않는 이유는 캐시 때문이다.

운영에서 배포나 도메인 이전을 할 때는 TTL을 미리 낮춰두기도 한다.

예:

```text
기존 TTL: 3600
변경 전 TTL: 60으로 낮춤
DNS 변경
안정화 후 TTL 다시 조정
```

## 4. HTTP 요청과 응답

### HTTP를 더 봐야 하는 이유

HTTP는 웹 애플리케이션의 실제 요청/응답 형식이다.

TCP 연결과 TLS 협상이 성공해도 HTTP 레벨에서 실패할 수 있다.

예:

```text
TCP 연결 성공
TLS 인증서 정상
HTTP 요청 도착
하지만 Host 라우팅 실패
→ 404
```

또는:

```text
HTTP 요청 도착
Nginx가 backend로 전달
backend에서 예외 발생
→ 500
```

### HTTP 요청 구조

HTTP 요청은 크게 start line, headers, body로 나뉜다.

```http
GET /api/users HTTP/1.1
Host: api.example.com
User-Agent: curl/8.0
Accept: application/json
```

각 부분:

```text
GET
→ HTTP method

/api/users
→ path

HTTP/1.1
→ HTTP version

Host
→ 어떤 도메인으로 요청했는지
```

Nginx는 `Host`와 `path`를 보고 라우팅할 수 있다.

```nginx
server_name api.example.com;

location /api/ {
    proxy_pass http://backend;
}
```

### HTTP 응답 구조

HTTP 응답도 status line, headers, body로 나뉜다.

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-cache

{"ok": true}
```

상태 코드는 장애 분석의 첫 단서다.

```text
2xx
→ 성공

3xx
→ 리다이렉트

4xx
→ 클라이언트 요청 문제

5xx
→ 서버 또는 프록시 문제
```

### 자주 보는 상태 코드

```text
200 OK
→ 정상

301 Moved Permanently
→ 영구 리다이렉트

302 Found
→ 임시 리다이렉트

400 Bad Request
→ 요청 형식 문제

401 Unauthorized
→ 인증 필요 또는 인증 실패

403 Forbidden
→ 권한 없음

404 Not Found
→ path 또는 라우팅 대상 없음

405 Method Not Allowed
→ method 불일치

413 Payload Too Large
→ 요청 body가 너무 큼

429 Too Many Requests
→ rate limit

500 Internal Server Error
→ 애플리케이션 내부 오류

502 Bad Gateway
→ 프록시가 upstream에서 정상 응답을 못 받음

503 Service Unavailable
→ 사용 가능한 대상 없음

504 Gateway Timeout
→ upstream 응답 시간 초과
```

### HTTP Host 헤더

하나의 서버 IP에서 여러 도메인을 처리할 수 있는 이유는 Host 헤더 때문이다.

```http
Host: api.example.com
```

Nginx는 이 값을 보고 server block을 고른다.

```nginx
server {
    listen 80;
    server_name api.example.com;
}

server {
    listen 80;
    server_name admin.example.com;
}
```

같은 IP로 들어와도 Host가 다르면 다른 서버 블록이 선택될 수 있다.

## 5. HTTPS와 TLS 핸드셰이크

### TLS를 더 봐야 하는 이유

HTTPS는 HTTP에 TLS가 붙은 구조다.

```text
HTTPS = HTTP + TLS
```

브라우저가 HTTPS 사이트에 접속하면 HTTP 요청을 보내기 전에 TLS 협상을 먼저 한다.

```text
DNS 조회
→ TCP 연결
→ TLS handshake
→ HTTP request
→ HTTP response
```

TLS 단계에서 실패하면 애플리케이션 로그에는 아무것도 안 남을 수 있다.

왜냐하면 HTTP 요청이 애플리케이션까지 도달하지 않았기 때문이다.

### TLS가 하는 일

TLS는 크게 세 가지 역할을 한다.

```text
암호화
→ 중간에서 내용을 훔쳐봐도 읽기 어렵게 함

무결성
→ 중간에서 데이터가 바뀌었는지 확인

인증
→ 접속한 서버가 진짜 그 도메인의 서버인지 인증서로 확인
```

### 인증서 검증

브라우저는 서버 인증서를 확인한다.

```text
서버 인증서
→ 중간 인증서
→ 루트 CA
```

확인하는 것:

```text
인증서가 만료되지 않았는가?
도메인 이름이 인증서에 포함되어 있는가?
신뢰할 수 있는 CA가 발급했는가?
인증서 체인이 올바른가?
```

예:

```text
사용자가 https://api.example.com 접속
서버 인증서가 www.example.com만 포함
→ 인증서 이름 불일치
```

### TLS termination 위치

TLS termination은 HTTPS 연결을 어디서 끝낼지 정하는 것이다.

ALB에서 종료:

```text
사용자
→ HTTPS
→ ALB
→ HTTP
→ EC2 Nginx
→ Backend
```

Nginx에서 종료:

```text
사용자
→ HTTPS
→ Nginx
→ HTTP
→ Backend
```

둘 다 가능하지만 ALB를 쓰면 ACM 인증서를 붙여 운영하기 쉽다.

중요한 점은 백엔드가 원래 요청이 HTTPS였다는 것을 알 수 있어야 한다는 것이다.

```http
X-Forwarded-Proto: https
```

이 헤더가 없으면 백엔드가 잘못 판단할 수 있다.

```text
HTTP로 들어왔다고 생각함
→ HTTPS로 리다이렉트
→ 프록시 뒤에서 리다이렉트 반복
```

## 6. Timeout과 Connection 관리

### Timeout을 알아야 하는 이유

운영 장애에서 timeout은 매우 흔하다.

하지만 timeout이라는 말도 여러 종류가 있다.

```text
DNS timeout
TCP connect timeout
TLS handshake timeout
Nginx proxy_connect_timeout
Nginx proxy_read_timeout
application request timeout
database query timeout
external API timeout
```

어떤 timeout인지 구분하지 않으면 원인을 잘못 찾는다.

### connect timeout

connect timeout은 연결을 맺는 단계에서 시간이 초과된 것이다.

예:

```text
Nginx
→ backend:8080으로 TCP 연결 시도
→ 응답 없음
→ connect timeout
```

의심:

```text
backend가 안 떠 있음
포트가 다름
Security Group 또는 방화벽이 막음
route table 문제
```

### read timeout

read timeout은 연결은 됐지만 응답을 읽는 데 시간이 너무 오래 걸린 것이다.

예:

```text
Nginx
→ backend 연결 성공
→ HTTP 요청 전달 성공
→ backend 응답이 늦음
→ proxy_read_timeout
→ 504
```

의심:

```text
DB 쿼리 지연
외부 API 지연
애플리케이션 deadlock
thread pool 고갈
connection pool 고갈
```

### keep-alive

HTTP keep-alive는 요청마다 TCP 연결을 새로 만들지 않고 기존 연결을 재사용하는 기능이다.

장점:

```text
TCP handshake 비용 감소
TLS handshake 비용 감소
응답 지연 감소
서버 자원 효율 개선
```

하지만 idle connection이 너무 많거나 timeout 설정이 맞지 않으면 문제가 될 수도 있다.

```text
ALB idle timeout
Nginx keepalive timeout
backend server timeout
```

프록시와 백엔드의 timeout 값이 서로 맞지 않으면 간헐적인 502가 날 수 있다.

## 7. 실제 장애 구분 방법

### 요청 흐름 기준으로 나누기

문제가 생기면 아래 순서로 나눠서 본다.

```text
1. DNS 조회가 되는가?
2. IP와 포트로 TCP 연결이 되는가?
3. HTTPS라면 TLS 인증서가 정상인가?
4. HTTP 응답 status code는 무엇인가?
5. Nginx access.log에 요청이 찍히는가?
6. Nginx error.log에 upstream 오류가 있는가?
7. backend container log에 요청이 찍히는가?
8. DB나 외부 API 호출에서 막히는가?
```

### DNS 확인

```bash
dig api.example.com
nslookup api.example.com
```

확인:

```text
원하는 IP 또는 ALB 주소로 해석되는가?
TTL이 너무 길지 않은가?
다른 DNS resolver에서도 같은 결과인가?
```

### TCP 확인

```bash
nc -vz api.example.com 443
curl -v http://127.0.0.1:8080/health
```

확인:

```text
포트가 열려 있는가?
connection refused인가?
timeout인가?
```

### TLS 확인

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
```

확인:

```text
인증서 도메인이 맞는가?
인증서 만료일이 정상인가?
인증서 체인이 정상인가?
SNI가 필요한 구조인가?
```

### HTTP 확인

```bash
curl -v https://api.example.com/health
curl -I https://api.example.com
```

확인:

```text
status code가 무엇인가?
redirect가 반복되는가?
Host 헤더가 맞는가?
응답 헤더가 예상과 같은가?
```

### Nginx 확인

```bash
nginx -t
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

확인:

```text
요청이 Nginx까지 도달하는가?
어떤 status code로 응답하는가?
upstream connection refused가 있는가?
upstream timed out이 있는가?
```

### Docker 확인

```bash
docker ps
docker port backend-blue
docker logs backend-blue
curl -f http://127.0.0.1:8080/health
curl -f http://127.0.0.1:8081/health
```

확인:

```text
active container가 떠 있는가?
host port가 올바르게 열려 있는가?
health check가 통과하는가?
Nginx가 바라보는 포트와 active container 포트가 같은가?
```

## 8. Nginx upstream 트래픽 전환과 연결해서 보기

다음은 네트워크 요청이 단일 EC2의 Nginx를 거쳐 두 application version 중 active 대상으로 전달되는 예다.

네트워크 관점의 핵심은 배포 전략 이름이 아니라 DNS, port, proxy upstream이 올바르게 이어지는지 확인하는 것이다. Blue/Green 자체의 선택 기준은 [DevOps 배포 전략 비교](../devops/03-deployment-strategies.md)에서 다룬다.

```text
사용자
→ DNS
→ EC2 또는 ALB
→ Nginx
→ 127.0.0.1:8080 또는 127.0.0.1:8081
→ backend container
```

전환 전:

```text
Nginx proxy_pass → 127.0.0.1:8080
blue container active
```

전환 후:

```text
Nginx proxy_pass → 127.0.0.1:8081
green container active
```

이때 장애가 나면 계층별로 나눠 봐야 한다.

```text
DNS 문제
→ 사용자가 아예 다른 곳으로 감

TCP 문제
→ 포트가 안 열려 있거나 방화벽이 막음

TLS 문제
→ 인증서, SNI, HTTPS 설정 문제

HTTP 문제
→ Host, path, redirect, status code 문제

Nginx upstream 문제
→ active 포트가 잘못됐거나 컨테이너가 죽음

Application 문제
→ backend log에 에러가 남음
```

## 최종 정리

```text
IP와 CIDR은 네트워크 대역과 라우팅 범위를 이해하기 위한 기본이다.
TCP는 HTTP, HTTPS, SSH, DB 연결의 기반이며 connection refused와 timeout을 구분해야 한다.
DNS는 도메인을 실제 대상 주소로 연결하고 TTL과 캐시 때문에 변경 반영이 지연될 수 있다.
HTTP는 Host, path, method, status code를 기준으로 요청과 응답을 분석한다.
HTTPS는 HTTP 전에 TLS handshake와 인증서 검증이 필요하다.
Timeout은 DNS, TCP, TLS, 프록시, 애플리케이션, DB 중 어느 단계인지 나눠야 한다.
운영 장애는 DNS → TCP → TLS → HTTP → Nginx → Docker → Application 순서로 좁혀가면 된다.
```
