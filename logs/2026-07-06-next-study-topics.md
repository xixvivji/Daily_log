# 2026-07-06 다음 학습 내용 정리

## 현재 위치

지금까지 정리한 내용은 크게 세 묶음이다.

```text
1. 네트워크 큰그림
2. 프록시 / 리버스 프록시 / 라우팅
3. 단일 EC2 + Docker + Nginx 기반 blue/green 배포 개념
```

이제 바로 이어서 공부할 내용은 **Nginx 심화 → Docker 네트워크 → AWS 네트워크** 순서가 좋다.

이 순서가 좋은 이유는 현재 이해한 구조와 바로 연결되기 때문이다.

```text
사용자
→ Nginx
→ blue container 또는 green container
→ backend application
```

여기서 더 깊게 이해해야 할 부분은 다음 세 가지다.

```text
Nginx가 요청을 어떻게 처리하는가
Docker 컨테이너 포트와 네트워크가 어떻게 연결되는가
AWS에서는 이 구조를 VPC, Security Group, ALB로 어떻게 확장하는가
```

## 1순위: Nginx 심화

### 왜 먼저 공부해야 하는가?

현재 blue/green 배포 구조에서 사용자의 요청을 실제 컨테이너로 보내는 핵심 역할은 Nginx가 한다.

```text
사용자
→ Nginx
→ 127.0.0.1:8080 또는 127.0.0.1:8081
```

Nginx 설정을 제대로 이해하지 못하면 다음 문제가 생겼을 때 원인을 찾기 어렵다.

```text
배포 후 404 발생
Nginx는 살아 있는데 백엔드 연결 실패
502 Bad Gateway
504 Gateway Timeout
HTTPS 리다이렉트 반복
파일 업로드 실패
클라이언트 IP가 이상하게 찍힘
```

### 공부할 내용

```text
server block
location 매칭 규칙
proxy_pass
proxy_pass trailing slash
upstream block
nginx -t
nginx reload
access.log
error.log
proxy_connect_timeout
proxy_read_timeout
proxy_send_timeout
client_max_body_size
HTTP to HTTPS redirect
X-Forwarded-* 헤더
```

### 핵심 개념

Nginx는 요청을 받으면 먼저 `server` 블록을 고르고, 그다음 `location` 블록을 고른다.

```nginx
server {
    listen 80;
    server_name example.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8080;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

이 설정의 의미는 다음과 같다.

```text
example.com/api/ 로 시작하는 요청 → 127.0.0.1:8080
그 외 요청 → 127.0.0.1:3000
```

`proxy_pass` 뒤의 슬래시도 중요하다.

```nginx
location /api/ {
    proxy_pass http://backend;
}
```

이 경우:

```text
/api/users → backend가 /api/users로 받음
```

반면:

```nginx
location /api/ {
    proxy_pass http://backend/;
}
```

이 경우:

```text
/api/users → backend가 /users로 받을 수 있음
```

이 차이를 모르면 배포 후 특정 API만 404가 나는 문제를 놓치기 쉽다.

### 확인해야 할 명령어

```bash
nginx -t
nginx -s reload
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
curl -I http://localhost
curl -v http://localhost/api/health
```

### 정리 목표

```text
Nginx가 요청을 어떤 server/location에 매칭하는지 설명할 수 있다.
proxy_pass의 슬래시 유무에 따른 path 전달 차이를 설명할 수 있다.
502, 504가 났을 때 Nginx error.log와 upstream 설정을 확인할 수 있다.
blue/green 전환 시 nginx -t 후 reload해야 하는 이유를 설명할 수 있다.
```

## 2순위: Docker 네트워크

### 왜 공부해야 하는가?

단일 EC2 blue/green 배포는 Docker 포트 매핑을 이해해야 정확히 설명할 수 있다.

예를 들어 blue와 green 컨테이너가 둘 다 내부에서는 8080을 사용해도, 호스트에서는 다른 포트로 열 수 있다.

```text
blue container 내부: 8080 → EC2 host:8080
green container 내부: 8080 → EC2 host:8081
```

이 구조를 모르면 "컨테이너 두 개가 둘 다 8080 쓰면 충돌나는 것 아닌가?" 같은 부분이 헷갈린다.

### 공부할 내용

```text
container port
host port
docker run -p
bridge network
host network
container name resolution
Docker DNS
docker-compose network
localhost의 의미
컨테이너 내부 localhost와 호스트 localhost 차이
```

### 핵심 개념

Docker에서 포트는 두 층으로 나뉜다.

```text
컨테이너 내부 포트
호스트 포트
```

예:

```bash
docker run -p 8080:8080 blue-app
docker run -p 8081:8080 green-app
```

의미:

```text
blue-app 컨테이너 내부 8080 → EC2 호스트 8080
green-app 컨테이너 내부 8080 → EC2 호스트 8081
```

컨테이너 내부에서는 둘 다 8080을 써도 된다.

하지만 같은 EC2 호스트에서 같은 IP와 같은 포트를 동시에 점유할 수는 없다.

```text
0.0.0.0:8080 → blue
0.0.0.0:8080 → green
```

이렇게 하면 충돌이 난다.

```text
address already in use
```

그래서 host port를 다르게 둔다.

```text
blue  → host 8080
green → host 8081
```

### Nginx와 연결

Nginx는 호스트 기준 포트로 컨테이너에 접근한다.

```nginx
location / {
    proxy_pass http://127.0.0.1:8080; # blue
}
```

green 전환 후:

```nginx
location / {
    proxy_pass http://127.0.0.1:8081; # green
}
```

### 확인해야 할 명령어

```bash
docker ps
docker port <container>
docker inspect <container>
docker logs <container>
curl -v http://127.0.0.1:8080/health
curl -v http://127.0.0.1:8081/health
```

### 정리 목표

```text
컨테이너 내부 포트와 호스트 포트 차이를 설명할 수 있다.
docker run -p 8081:8080의 의미를 설명할 수 있다.
같은 EC2에서 같은 IP:PORT를 두 프로세스가 동시에 쓸 수 없는 이유를 설명할 수 있다.
Nginx가 컨테이너 내부 포트가 아니라 호스트에 열린 포트로 접근한다는 점을 설명할 수 있다.
```

## 3순위: AWS VPC / Security Group / ALB

### 왜 공부해야 하는가?

현재 구조는 EC2 한 대에서 Nginx가 직접 외부 요청을 받는 방식이다.

```text
사용자
→ EC2 Public IP
→ Nginx
→ Docker container
```

클라우드 구조로 확장하면 보통 앞에 ALB를 둔다.

```text
사용자
→ Route 53
→ ALB
→ EC2 Target Group
→ Nginx
→ Docker container
```

이 구조를 이해하려면 VPC, Subnet, Route Table, Security Group, ALB, Target Group을 알아야 한다.

### 공부할 내용

```text
VPC
CIDR
Subnet
Public Subnet
Private Subnet
Route Table
Internet Gateway
NAT Gateway
Security Group
NACL
ALB
NLB
Target Group
Health Check
Route 53
```

### 핵심 개념

VPC는 AWS 안에서 만드는 내 전용 네트워크다.

```text
VPC = 클라우드 안의 가상 네트워크
Subnet = VPC를 더 작게 나눈 네트워크 구역
Route Table = 트래픽을 어디로 보낼지 정하는 규칙
Internet Gateway = 인터넷으로 나가는 문
Security Group = 인스턴스 단위 방화벽
ALB = HTTP/HTTPS 요청을 여러 대상에게 보내는 L7 로드밸런서
Target Group = ALB가 트래픽을 보낼 대상 묶음
```

### EC2 + ALB 구조

```text
사용자
→ ALB:443
→ Target Group
→ EC2:80
→ Nginx
→ backend container
```

Security Group은 보통 이런 식으로 나눈다.

```text
ALB Security Group
- inbound: 80, 443 from 0.0.0.0/0

EC2 Security Group
- inbound: 80 from ALB Security Group
- inbound: 22 from 내 IP
```

이렇게 하면 EC2가 인터넷 전체에 직접 열리는 것을 줄일 수 있다.

### 확인해야 할 것

```text
ALB listener가 80/443을 듣고 있는가
Target Group health check가 통과하는가
EC2 Security Group이 ALB에서 오는 요청을 허용하는가
Nginx가 EC2 내부에서 80 포트를 듣고 있는가
Nginx가 Docker container로 proxy_pass 하는가
```

### 정리 목표

```text
VPC, Subnet, Route Table, Internet Gateway의 역할을 설명할 수 있다.
Security Group과 NACL의 차이를 설명할 수 있다.
ALB, Target Group, Health Check의 관계를 설명할 수 있다.
사용자 → ALB → EC2 → Nginx → Container 흐름을 그릴 수 있다.
```

## 4순위: DNS / Route 53

### 왜 공부해야 하는가?

사용자는 서버 IP를 직접 입력하지 않고 도메인으로 접속한다.

```text
https://api.example.com
```

이 도메인이 ALB나 EC2로 연결되려면 DNS 설정을 이해해야 한다.

### 공부할 내용

```text
도메인
Hosted Zone
A Record
AAAA Record
CNAME
Alias Record
TTL
DNS 캐싱
Route 53
ALB와 도메인 연결
```

### 핵심 개념

AWS Route 53에서는 ALB에 도메인을 연결할 때 Alias Record를 많이 사용한다.

```text
api.example.com
→ Alias
→ ALB DNS Name
```

EC2 고정 IP에 직접 연결할 수도 있지만, 운영 구조에서는 ALB 앞단에 도메인을 붙이는 경우가 많다.

### 정리 목표

```text
도메인 이름이 IP나 ALB로 연결되는 흐름을 설명할 수 있다.
A Record, CNAME, Alias Record 차이를 설명할 수 있다.
TTL과 DNS 캐싱 때문에 변경이 바로 반영되지 않을 수 있다는 점을 설명할 수 있다.
```

## 5순위: HTTPS / TLS

### 왜 공부해야 하는가?

운영 서비스는 대부분 HTTPS를 사용한다.

그리고 HTTPS를 어디서 끝낼지 결정해야 한다.

```text
사용자
→ HTTPS
→ ALB 또는 Nginx
→ HTTP 또는 HTTPS
→ Backend
```

### 공부할 내용

```text
TLS
HTTPS
인증서
CA
ACM
TLS termination
TLS passthrough
backend re-encryption
HTTP to HTTPS redirect
Secure Cookie
X-Forwarded-Proto
```

### 핵심 개념

TLS 종료는 HTTPS 연결을 특정 지점에서 끝내고, 그 뒤쪽으로는 HTTP 또는 다시 HTTPS로 넘기는 것이다.

예:

```text
사용자
→ HTTPS
→ ALB
→ HTTP
→ EC2 Nginx
→ backend container
```

또는:

```text
사용자
→ HTTPS
→ Nginx
→ HTTP
→ backend container
```

이때 백엔드가 원래 요청이 HTTPS였다는 사실을 알아야 하면 `X-Forwarded-Proto` 같은 헤더가 필요하다.

### 정리 목표

```text
HTTPS와 TLS의 관계를 설명할 수 있다.
TLS termination이 무엇인지 설명할 수 있다.
ALB에서 TLS를 종료하는 구조와 Nginx에서 TLS를 종료하는 구조를 구분할 수 있다.
X-Forwarded-Proto가 왜 필요한지 설명할 수 있다.
```

## 추천 학습 순서 요약

```text
1. Nginx 심화
2. Docker 네트워크
3. AWS VPC / Security Group / ALB
4. DNS / Route 53
5. HTTPS / TLS
6. CI/CD와 배포 자동화
7. Monitoring / Logging
8. Kubernetes Service / Ingress
```

## 지금 당장 이어서 볼 주제

바로 다음 학습은 **Nginx 심화**로 잡는 것이 좋다.

특히 아래 4개를 먼저 정리하면 된다.

```text
location 매칭 규칙
proxy_pass path 전달
upstream block
access.log / error.log
```

이 4개를 이해하면 현재 blue/green 배포 구조에서 Nginx가 정확히 어떤 역할을 하는지 더 명확해진다.

## 한 줄 정리

```text
다음 학습은 Nginx 심화부터 시작하고, 그다음 Docker 네트워크와 AWS VPC/ALB로 확장하면 현재 배포 구조와 클라우드 구조가 자연스럽게 이어진다.
```
