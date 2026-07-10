# 2026-07-10 네트워크 장애 분석 실전: DNS부터 Application까지

## 핵심 관점

운영에서 "사이트가 안 열린다"는 말은 너무 넓다.

실제로는 아래 중 하나다.

```text
DNS가 안 됨
라우팅이 안 됨
방화벽이 막음
TCP 연결이 안 됨
TLS 인증서가 안 맞음
HTTP 라우팅이 틀림
Nginx upstream이 죽음
컨테이너가 안 떠 있음
애플리케이션이 DB에서 막힘
```

장애 분석은 감으로 찍는 것이 아니라 요청 흐름을 앞에서 뒤로 쪼개는 것이다.

```text
DNS
→ Routing
→ Firewall
→ TCP
→ TLS
→ HTTP
→ Proxy
→ Container
→ Application
→ Database / External API
```

## 1. 전체 체크 순서

기본 순서:

```text
1. 도메인이 올바른 대상으로 해석되는가?
2. 목적지 포트로 TCP 연결이 되는가?
3. HTTPS 인증서가 정상인가?
4. HTTP status code가 무엇인가?
5. ALB Target Group이 healthy인가?
6. Nginx access.log에 요청이 찍히는가?
7. Nginx error.log에 upstream 오류가 있는가?
8. Container가 떠 있는가?
9. Backend health check가 통과하는가?
10. DB나 외부 API에서 막히는가?
```

이 순서를 지키면 문제 범위를 빠르게 줄일 수 있다.

## 2. DNS 문제

증상:

```text
브라우저에서 사이트를 찾을 수 없음
curl: Could not resolve host
특정 네트워크에서만 접속 안 됨
도메인 변경 후 일부 사용자만 예전 서버로 감
```

확인:

```bash
dig api.example.com
dig +short api.example.com
dig @8.8.8.8 api.example.com
dig @1.1.1.1 api.example.com
nslookup api.example.com
```

봐야 할 것:

```text
원하는 ALB 또는 IP로 해석되는가?
TTL이 너무 길지 않은가?
resolver마다 응답이 다른가?
NXDOMAIN인가?
SERVFAIL인가?
```

조치:

```text
Route 53 레코드 확인
Hosted Zone 확인
NS 위임 확인
TTL 확인
브라우저/OS DNS cache 고려
```

## 3. Routing 문제

증상:

```text
같은 VPC 내부는 되는데 인터넷이 안 됨
private EC2가 패키지 설치를 못 함
ALB에서 target으로 못 감
```

AWS에서 확인:

```text
Subnet Route Table
0.0.0.0/0 경로
Internet Gateway 연결
NAT Gateway 위치
VPC local route
```

Public subnet:

```text
0.0.0.0/0 → Internet Gateway
```

Private subnet:

```text
0.0.0.0/0 → NAT Gateway
```

주의:

```text
NAT Gateway는 public subnet에 있어야 한다.
private subnet의 route table이 NAT Gateway를 가리켜야 한다.
```

## 4. Firewall 문제

증상:

```text
connection timed out
ALB health check 실패
SSH 접속 안 됨
외부에서 80/443 접속 안 됨
```

확인:

```text
Security Group inbound
Security Group outbound
NACL inbound
NACL outbound
OS firewall
서버 프로세스 listen 여부
```

권장 SG 예:

```text
ALB SG
- 80 from 0.0.0.0/0
- 443 from 0.0.0.0/0

EC2 SG
- app port from ALB SG
- 22 from 내 IP/32
```

SSH를 열 때:

```text
나쁨: 22 from 0.0.0.0/0
좋음: 22 from 내 공인 IP/32
```

## 5. TCP 문제

확인 명령어:

```bash
nc -vz api.example.com 443
curl -v http://127.0.0.1:8080/health
ss -lntp
```

`connection refused`:

```text
목적지까지 갔지만 해당 포트에서 받아주는 프로세스가 없음
```

의심:

```text
앱이 죽음
포트 틀림
Docker port mapping 틀림
Nginx proxy_pass 포트 틀림
```

`connection timed out`:

```text
응답이 오지 않음
```

의심:

```text
Security Group
NACL
Route Table
대상 IP 오류
네트워크 경로 문제
```

## 6. TLS 문제

증상:

```text
브라우저 인증서 경고
도메인 불일치
인증서 만료
HTTPS만 실패
```

확인:

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
```

봐야 할 것:

```text
인증서 Subject / SAN에 도메인이 포함되는가?
인증서가 만료되지 않았는가?
중간 인증서 체인이 정상인가?
SNI가 필요한 구조인가?
```

ALB 사용 시:

```text
ACM 인증서 연결 확인
Listener 443 확인
Security Group 443 허용 확인
```

## 7. HTTP 문제

확인:

```bash
curl -v https://api.example.com/health
curl -I https://api.example.com
```

상태 코드별 판단:

```text
301 / 302
→ redirect 설정 확인

400
→ 요청 형식, Host, header 확인

401
→ 인증 필요 또는 token 문제

403
→ 권한, WAF, 인증/인가, static file 권한 확인

404
→ path, Nginx location, backend route 확인

405
→ method 불일치

413
→ body size 제한

429
→ rate limit

500
→ backend application error

502
→ proxy upstream 연결/응답 문제

503
→ 사용 가능한 target 없음

504
→ upstream 응답 timeout
```

## 8. ALB 문제

확인:

```text
Listener 80/443
Listener Rule
Target Group
Health Check path
Health Check port
Target health status
ALB Security Group
EC2 Security Group
```

Target unhealthy 원인:

```text
Health check path가 없음
앱이 늦게 뜸
EC2 SG가 ALB SG를 허용하지 않음
Nginx가 backend로 proxy_pass 실패
앱 port가 target group port와 다름
```

## 9. Nginx 문제

확인:

```bash
nginx -t
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

봐야 할 것:

```text
요청이 access.log에 찍히는가?
status code가 무엇인가?
upstream connection refused가 있는가?
upstream timed out이 있는가?
proxy_pass 대상이 맞는가?
location 매칭이 예상과 같은가?
```

자주 나는 문제:

```text
proxy_pass trailing slash 때문에 path가 바뀜
active blue/green 포트가 틀림
nginx reload 전에 nginx -t를 안 함
client_max_body_size가 작아서 413 발생
X-Forwarded-Proto 누락으로 redirect 반복
```

## 10. Docker 문제

확인:

```bash
docker ps
docker logs backend
docker port backend
curl -f http://127.0.0.1:8080/health
curl -f http://127.0.0.1:8081/health
```

봐야 할 것:

```text
컨테이너가 실행 중인가?
host port가 열려 있는가?
container 내부 port와 host port가 맞는가?
health check가 통과하는가?
환경 변수가 맞는가?
DB 연결 설정이 맞는가?
```

Blue/Green 예:

```text
blue:  host 8080 → container 8080
green: host 8081 → container 8080
```

Nginx가 active 포트를 바라보는지 확인한다.

## 11. Backend 문제

Nginx와 Docker까지 정상인데 500이 나면 backend를 본다.

확인:

```text
application log
exception stack trace
DB connection
DB migration
external API timeout
thread pool
connection pool
환경 변수
secret
```

500과 504 차이:

```text
500
→ backend가 응답은 했지만 내부 오류

504
→ proxy가 backend 응답을 기다리다 timeout
```

## 12. 대표 시나리오

### 도메인을 못 찾음

```text
dig 실패
→ DNS / Route 53 / NS 위임 확인
```

### 도메인은 되는데 접속 timeout

```text
DNS 정상
TCP timeout
→ Security Group / NACL / Route Table 확인
```

### 502 Bad Gateway

```text
Nginx error.log 확인
upstream connection refused
→ backend container / port / proxy_pass 확인
```

### 504 Gateway Timeout

```text
Nginx error.log 확인
upstream timed out
→ backend 처리 시간 / DB / 외부 API / timeout 설정 확인
```

### HTTPS redirect 반복

```text
ALB에서 TLS 종료
backend는 HTTP로 인식
→ X-Forwarded-Proto 처리 확인
```

### ALB Target unhealthy

```text
Health check path
Target port
EC2 SG inbound from ALB SG
앱 listen port
Nginx proxy_pass
```

## 13. 실전 체크리스트

장애가 났을 때 순서:

```text
1. dig로 DNS 확인
2. curl -v로 HTTP/TLS 흐름 확인
3. nc로 포트 연결 확인
4. ALB Target Health 확인
5. Security Group 확인
6. Route Table 확인
7. Nginx access.log 확인
8. Nginx error.log 확인
9. docker ps 확인
10. docker logs 확인
11. backend health check 확인
12. application log 확인
13. DB / external API 확인
```

## 최종 정리

```text
장애 분석은 DNS부터 Application까지 흐름을 나눠서 본다.
DNS 문제는 서버까지 요청이 도달하지 않는다.
TCP timeout은 방화벽이나 라우팅 문제일 가능성이 높다.
connection refused는 포트에 프로세스가 없거나 거절된 상황이다.
TLS 문제는 HTTP 요청 전에 실패할 수 있다.
HTTP status code는 장애 분석의 첫 단서다.
502는 upstream 연결/응답 문제, 504는 upstream 응답 지연 문제다.
ALB, Nginx, Docker, Backend 로그를 순서대로 보면 원인을 좁힐 수 있다.
```
