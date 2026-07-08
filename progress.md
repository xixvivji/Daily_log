# 현재 정리 상태와 보강 필요 내용

## 기준

전체 학습 범위는 [list.md](list.md)에 정리되어 있다.

`list.md`는 네트워크 기본부터 클라우드 운영까지 전체 공부 범위를 잡아둔 파일이고, `infrastructure/` 아래 파일들은 실제로 자세히 정리한 인프라 학습 노트다.

현재 작성된 인프라 상세 노트는 다음 9개다.

```text
infrastructure/2026-07-03-network-basics-01.md
infrastructure/2026-07-03-proxy-routing.md
infrastructure/2026-07-04-nginx-proxy-routing-troubleshooting.md
infrastructure/2026-07-06-nginx-docker-aws-infra-foundations.md
infrastructure/2026-07-07-nginx-docker-aws-infra.md
infrastructure/2026-07-07-deployment-strategies.md
infrastructure/2026-07-07-nginx-docker-aws-operations.md
infrastructure/2026-07-08-ip-subnet-mask-cidr.md
infrastructure/2026-07-08-network-protocol-deep-dive.md
```

## 현재 자세히 정리된 부분

### 1. 네트워크 기본

관련 파일:

```text
infrastructure/2026-07-03-network-basics-01.md
```

정리된 내용:

```text
네트워크란 무엇인가
패킷
프로토콜
클라이언트 / 서버
IP와 MAC 주소 차이
같은 네트워크와 다른 네트워크 구분
게이트웨이
라우터와 스위치
LAN과 WAN
사설 IP와 공인 IP
NAT
HTTP 요청이 계층을 지나며 포장되는 흐름
사이트가 안 열릴 때 확인 순서
```

상태:

```text
기본 개념 정리 완료
IP 주소, 서브넷 마스크, CIDR은 별도 상세 문서에서 보강됨
TCP, DNS, HTTP, TLS는 네트워크 프로토콜 심화 문서에서 보강됨
```

## 2. 프록시 기본

관련 파일:

```text
infrastructure/2026-07-03-proxy-routing.md
```

정리된 내용:

```text
Proxy란 무엇인가
Forward Proxy
Reverse Proxy
Forward Proxy와 Reverse Proxy 차이
프록시가 요청을 대신 전달하는 구조
프론트 프록시라는 표현보다 Forward Proxy가 정확하다는 점
```

상태:

```text
큰 개념 정리 완료
X-Forwarded 헤더는 별도 문서에서 보강됨
캐싱, 인증, 보안 정책은 별도 심화 정리 가능
```

## 3. 리버스 프록시

관련 파일:

```text
infrastructure/2026-07-03-proxy-routing.md
infrastructure/2026-07-04-nginx-proxy-routing-troubleshooting.md
```

정리된 내용:

```text
Reverse Proxy 구조
Nginx가 리버스 프록시로 동작하는 방식
서버 앞에서 요청을 대신 받는 개념
Nginx와 Kubernetes Ingress Controller의 관계
Ingress는 규칙이고 Ingress Controller가 실제 프록시라는 점
```

상태:

```text
큰 그림 정리 완료
Nginx location, proxy_pass, upstream, 로그, timeout은 별도 문서에서 보강됨
```

## 4. 라우팅

관련 파일:

```text
infrastructure/2026-07-03-proxy-routing.md
```

정리된 내용:

```text
라우팅이란 무엇인가
네트워크 라우팅
HTTP 라우팅
Host 기반 라우팅
Path 기반 라우팅
Kubernetes Ingress 라우팅
```

상태:

```text
개념 정리 완료
라우팅 테이블, default route, static route 같은 네트워크 라우팅 심화는 추가 필요
```

## 5. 로드밸런싱

관련 파일:

```text
infrastructure/2026-07-03-proxy-routing.md
```

정리된 내용:

```text
로드밸런싱이란 무엇인가
리버스 프록시와 로드밸런싱의 차이
Nginx가 리버스 프록시이면서 로드밸런서 역할도 할 수 있다는 점
Blue/Green 트래픽 스위칭은 일반적인 로드밸런싱과 다르다는 점
```

상태:

```text
기본 개념 정리 완료
L4/L7, Round Robin, Least Connections, Sticky Session, Connection Draining은 로드밸런싱 심화 주제로 분리 가능
```

## 6. Nginx 심화 일부

관련 파일:

```text
infrastructure/2026-07-04-nginx-proxy-routing-troubleshooting.md
```

정리된 내용:

```text
Nginx location 매칭 규칙
location / 와 location /api/ 차이
location = /health
proxy_pass 역할
proxy_pass 뒤 슬래시 유무에 따른 path 전달 차이
X-Forwarded-* 헤더 기본
502 / 503 / 504 기본 원인
graceful shutdown 기본
```

상태:

```text
Nginx 입문 심화 정리 완료
server block, location, proxy_pass, upstream, timeout, 로그, X-Forwarded 헤더 정리 완료
rate limit, request body 제한, gzip, 캐싱은 별도 심화 정리 가능
```

## 7. 장애 분석 일부

관련 파일:

```text
infrastructure/2026-07-04-nginx-proxy-routing-troubleshooting.md
```

정리된 내용:

```text
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
Nginx upstream 문제
백엔드 컨테이너 미실행
백엔드 응답 지연
사용 가능한 target 없음
```

상태:

```text
프록시 계층의 5xx 장애 원인 정리 완료
connection refused, timeout, upstream 문제, health check 문제 정리 완료
DNS failure, TLS handshake, CORS 오류는 별도 장애 분석 문서로 분리 가능
```

## 8. 배포와 무중단 일부

관련 파일:

```text
infrastructure/2026-07-04-nginx-proxy-routing-troubleshooting.md
```

정리된 내용:

```text
단일 EC2 Blue/Green Deployment
Nginx 기반 트래픽 스위칭
blue container / green container 구조
Health Check
Graceful Shutdown
docker stop --time
기존 요청을 마무리하고 종료해야 하는 이유
```

상태:

```text
단일 인스턴스 blue/green 구조는 정리됨
Rolling, Blue/Green, Canary, Feature Flag, Shadow, A/B 배포 전략 정리 완료
DB migration 호환성, connection draining, rollback 자동화는 실무 사례 중심으로 더 보강 가능
```

## 9. 운영 인프라 구성 요소

관련 파일:

```text
infrastructure/2026-07-06-nginx-docker-aws-infra-foundations.md
infrastructure/2026-07-07-nginx-docker-aws-infra.md
infrastructure/2026-07-07-nginx-docker-aws-operations.md
```

정리된 내용:

```text
Nginx server block
Nginx location matching
proxy_pass path 처리
upstream block
nginx -t / reload
access.log / error.log
Docker host port와 container port
Docker bridge network
docker-compose service DNS
AWS VPC / Subnet / Route Table
Security Group / NACL
ALB / Target Group / Health Check
DNS / Route 53 / TTL
HTTPS / TLS / ACM / TLS termination
Monitoring / Logging
CI/CD 배포 자동화
Kubernetes Service / Ingress / readinessProbe
```

상태:

```text
단일 EC2 + Docker + Nginx 구조에서 AWS 운영 구조로 확장하는 내용 정리 완료
Kubernetes는 Service/Ingress/readinessProbe 중심으로 입문 정리 완료
Kubernetes 네트워크 전체 구조, CNI, kube-proxy, NetworkPolicy는 별도 심화 정리 가능
```

## 10. 배포 전략

관련 파일:

```text
infrastructure/2026-07-07-deployment-strategies.md
```

정리된 내용:

```text
Recreate 배포
Rolling 배포
Blue/Green 배포
Canary 배포
Feature Flag 배포
Shadow 배포
A/B Test와 배포 전략의 차이
단일 EC2 blue/green 컨테이너 구조
로드밸런싱과 트래픽 스위칭 차이
리소스 사용량과 운영 복잡도 trade-off
DB migration 호환성
rollback 전략
실무에서 Canary를 쓰는 이유
```

상태:

```text
주요 배포 전략과 trade-off 정리 완료
Kubernetes Deployment, Argo Rollouts, ALB weighted target group 같은 도구 기반 예시는 별도 실습 문서로 분리 가능
```

## 11. IP 주소와 서브넷 마스크 상세

관련 파일:

```text
infrastructure/2026-07-08-ip-subnet-mask-cidr.md
```

정리된 내용:

```text
IPv4 주소가 32비트인 이유
8비트와 0~255 범위
10진수와 2진수 변환
IP 주소의 네트워크 부분과 호스트 부분
서브넷 마스크의 의미
255.255.255.0이 /24가 되는 이유
/24에서 앞 24비트가 네트워크가 되는 과정
네트워크 주소 계산 방법
브로드캐스트 주소 계산 방법
/24에서 사용 가능한 IP가 1~254인 이유
같은 네트워크와 다른 네트워크 판단
/16, /24, /25 차이
CIDR 숫자와 주소 개수 계산
게이트웨이가 필요한 이유
게이트웨이가 같은 네트워크 안에 있어야 하는 이유
0.0.0.0/0
127.0.0.1/32
사설 IP 대역
AWS VPC와 Subnet 예시
IP 대역이 겹치면 생기는 문제
```

상태:

```text
IP 주소, 서브넷 마스크, CIDR 계산 기초 정리 완료
/25, /26 같은 세부 subnet 분할도 입문 수준에서 정리됨
```

## 12. 네트워크 프로토콜 심화

관련 파일:

```text
infrastructure/2026-07-08-network-protocol-deep-dive.md
```

정리된 내용:

```text
IP 주소와 CIDR
/16과 /24 차이
VPC와 Subnet 대역
IP 대역이 겹치면 생기는 문제
TCP 3-way handshake
connection refused
connection timed out
no route to host
TCP 종료와 TIME_WAIT
DNS 조회 흐름
recursive resolver
root DNS / TLD DNS / authoritative DNS
A Record / CNAME / Route 53 Alias
TTL과 DNS 캐시
HTTP 요청과 응답 구조
HTTP Host 헤더
주요 HTTP status code
HTTPS와 TLS handshake
인증서 검증
TLS termination
Timeout 종류
keep-alive
DNS → TCP → TLS → HTTP → Nginx → Docker → Application 장애 구분 순서
```

상태:

```text
운영 장애 분석에 필요한 TCP, DNS, HTTP, TLS 기본 심화 정리 완료
TCP congestion control, HTTP/2, HTTP/3, DNSSEC은 별도 심화 주제로 분리 가능
```

## 아직 보강하면 좋은 부분

현재 문서들은 네트워크 큰그림, 프록시, Nginx, Docker, AWS 운영 구조, 배포 전략, TCP/DNS/HTTP/TLS 심화까지는 꽤 자세히 정리되어 있다.

남은 보강 포인트는 이미 작성한 내용의 빈 곳이라기보다, 별도 심화 주제로 빼는 것이 좋은 내용들이다.

### 네트워크 심화

```text
ARP
TCP congestion control
UDP 사용 사례
HTTP cache
HTTP/2와 HTTP/3
DNSSEC
```

### 운영 장애 분석 심화

```text
DNS failure
TLS handshake failure
connection refused
connection timeout
read timeout
CORS 오류
502 / 503 / 504 실제 로그 예시
Nginx access log format 커스터마이징
CloudWatch Alarm 설계
```

### Kubernetes 심화

```text
CNI
kube-proxy
ClusterIP 동작 방식
NodePort 동작 방식
Ingress Controller 종류
NetworkPolicy
Pod DNS
Service discovery
RollingUpdate 전략
readinessProbe와 livenessProbe 차이
```

### AWS / 클라우드 심화

```text
IAM User / Group / Role / Policy
EC2 Auto Scaling Group
Launch Template
S3 / EBS / EFS
RDS / Redis
CloudWatch Logs / Metrics / Alarms
AWS Systems Manager
Terraform 기초
비용 구조
보안 모범 사례
```

## 현재 상태 한 줄 정리

```text
네트워크 큰그림, 프록시/라우팅, Nginx, Docker 네트워크, AWS 운영 인프라, 배포 전략까지는 상세 노트가 작성되어 있다.
TCP/DNS/HTTP/TLS 심화도 추가되었고, 남은 부분은 Kubernetes 내부 네트워크, AWS IAM/Storage/Database/IaC 같은 확장 주제다.
```
