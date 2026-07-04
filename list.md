# 네트워크와 클라우드 전체 학습 리스트

## 목표

백엔드 개발자가 배포, 운영, 장애 분석까지 이해하기 위해 필요한 네트워크와 클라우드 학습 범위를 정리한다.

이 리스트는 단순 암기용이 아니라 아래 흐름을 이해하는 것을 목표로 한다.

```text
사용자
→ DNS
→ 인터넷
→ 클라우드 네트워크
→ 로드밸런서 / 리버스 프록시
→ 컨테이너 / 서버
→ 애플리케이션
→ 데이터베이스 / 스토리지
```

## 1. 네트워크 기본

### 공부할 내용

```text
네트워크란 무엇인가
패킷
프로토콜
클라이언트 / 서버
LAN / WAN
인터넷 구조
ISP
게이트웨이
라우터
스위치
```

### 왜 필요한가

네트워크 기본 개념은 이후에 나오는 IP, DNS, TCP, HTTP, 프록시, 클라우드 네트워크의 바닥이다.

특히 장애가 났을 때 "어디까지 통신이 되는가"를 판단하려면 네트워크가 어떤 장비와 규칙으로 구성되는지 알아야 한다.

## 2. 주소 체계

### 공부할 내용

```text
IPv4
IPv6
공인 IP / 사설 IP
고정 IP / 유동 IP
MAC 주소
ARP
서브넷 마스크
CIDR
기본 게이트웨이
라우팅 테이블
```

### 왜 필요한가

IP 주소와 서브넷을 모르면 같은 네트워크인지 다른 네트워크인지 판단할 수 없다.

AWS VPC, Subnet, Route Table, Security Group을 이해하려면 주소 체계와 CIDR은 반드시 필요하다.

## 3. 포트와 소켓

### 공부할 내용

```text
포트 번호
well-known port
ephemeral port
소켓
listen
bind
localhost
127.0.0.1
0.0.0.0
같은 IP:PORT 중복 바인딩 문제
```

### 왜 필요한가

애플리케이션은 IP만으로 구분되지 않고 포트까지 포함해서 구분된다.

한 EC2 인스턴스에서 blue 컨테이너와 green 컨테이너를 동시에 띄울 때도 같은 호스트 포트를 동시에 쓸 수 없으므로 포트 개념이 중요하다.

## 4. TCP / UDP

### 공부할 내용

```text
TCP와 UDP 차이
TCP 3-way handshake
TCP 4-way termination
SYN / ACK / FIN / RST
재전송
순서 보장
흐름 제어
혼잡 제어
keep-alive
TIME_WAIT
UDP 사용 사례
```

### 왜 필요한가

HTTP, HTTPS, SSH, DB 연결 대부분은 TCP 위에서 동작한다.

연결 지연, 연결 끊김, TIME_WAIT, keep-alive 같은 문제를 이해하려면 TCP 흐름을 알아야 한다.

## 5. DNS

### 공부할 내용

```text
DNS란 무엇인가
도메인 구조
Root DNS
TLD DNS
Authoritative DNS
Recursive Resolver
A 레코드
AAAA 레코드
CNAME
MX
NS
TXT
TTL
DNS 캐싱
도메인 전파
Route 53 같은 관리형 DNS
```

### 왜 필요한가

사용자는 보통 IP가 아니라 도메인으로 서비스에 접속한다.

도메인 연결, HTTPS 인증서, 로드밸런서 연결, Route 53 설정을 이해하려면 DNS가 필수다.

## 6. HTTP

### 공부할 내용

```text
HTTP 요청 / 응답 구조
Method: GET, POST, PUT, PATCH, DELETE
Status Code: 2xx, 3xx, 4xx, 5xx
Header
Body
Cookie
Session
Cache-Control
Content-Type
User-Agent
Host header
CORS
HTTP/1.1
HTTP/2
HTTP/3
```

### 왜 필요한가

백엔드 API, 프론트엔드 통신, 프록시 라우팅, 장애 분석은 대부분 HTTP를 기준으로 이루어진다.

특히 404, 502, 503, 504 같은 상태 코드는 운영 중 자주 마주친다.

## 7. HTTPS / TLS

### 공부할 내용

```text
TLS란 무엇인가
HTTPS 흐름
TLS handshake
인증서
CA
공개키 / 개인키
대칭키 / 비대칭키
SNI
인증서 체인
TLS termination
TLS passthrough
backend re-encryption
mixed content
secure cookie
```

### 왜 필요한가

실제 서비스는 대부분 HTTPS로 운영된다.

Nginx, ALB, CloudFront, Ingress에서 TLS를 어디서 종료할지 결정해야 하며, 이 설정이 잘못되면 리다이렉트, 쿠키, 인증서 오류가 발생한다.

## 8. 프록시 기본

### 공부할 내용

```text
Proxy란 무엇인가
Forward Proxy
Reverse Proxy
Transparent Proxy
프록시와 캐싱
프록시와 보안
프록시와 로그
프록시와 인증
Forwarded header
Via header
```

### 왜 필요한가

프록시는 클라이언트와 서버 사이에서 요청을 대신 전달한다.

Nginx, ALB, API Gateway, Ingress Controller 모두 프록시 개념과 연결된다.

## 9. 리버스 프록시

### 공부할 내용

```text
Reverse Proxy 구조
Nginx
HAProxy
Traefik
Envoy
Apache reverse proxy
upstream
proxy_pass
location matching
path rewrite
Host 기반 라우팅
Path 기반 라우팅
Header 기반 라우팅
WebSocket proxy
gRPC proxy
```

### 왜 필요한가

리버스 프록시는 서버 앞에서 요청을 받고 뒤쪽 애플리케이션으로 전달한다.

EC2 한 대에서 Docker blue/green 배포를 할 때도 Nginx가 리버스 프록시로 동작하며 active 컨테이너로 트래픽을 보낸다.

## 10. 프록시 헤더

### 공부할 내용

```text
Host
X-Real-IP
X-Forwarded-For
X-Forwarded-Proto
X-Forwarded-Host
X-Forwarded-Port
Forwarded
client IP 보존
trusted proxy 설정
프록시 체인
```

### 왜 필요한가

백엔드 앞에 프록시가 있으면 백엔드는 실제 클라이언트 IP나 원래 프로토콜을 직접 알기 어렵다.

이 정보를 잘 넘기지 않으면 로그의 IP가 전부 프록시 IP로 찍히거나 HTTPS 리다이렉트, Secure Cookie 문제가 생길 수 있다.

## 11. 라우팅

### 공부할 내용

```text
네트워크 라우팅
라우팅 테이블
default route
static route
dynamic routing 개념
HTTP routing
Host routing
Path routing
Header routing
Weighted routing
Canary routing
Blue/Green traffic switching
```

### 왜 필요한가

라우팅은 요청이나 패킷을 어디로 보낼지 결정하는 과정이다.

네트워크 라우팅은 IP 기반이고, HTTP 라우팅은 Host, Path, Header 같은 HTTP 정보를 기준으로 동작한다.

## 12. 로드밸런싱

### 공부할 내용

```text
L4 Load Balancing
L7 Load Balancing
Round Robin
Least Connections
IP Hash
Weighted Round Robin
Health Check
Sticky Session
Connection Draining
Active / Passive
Active / Active
Nginx load balancing
AWS ALB
AWS NLB
```

### 왜 필요한가

로드밸런싱은 여러 서버나 컨테이너에 트래픽을 나누어 보내는 기능이다.

리버스 프록시와 비슷하게 보일 수 있지만, 리버스 프록시는 앞에서 대신 받는 구조이고 로드밸런싱은 여러 대상에 분산하는 기능이다.

## 13. Nginx 심화

### 공부할 내용

```text
server block
location matching
proxy_pass trailing slash
upstream block
nginx -t
nginx reload
access.log
error.log
client_max_body_size
proxy_read_timeout
proxy_connect_timeout
proxy_send_timeout
gzip
cache
rate limit
basic auth
TLS 설정
HTTP to HTTPS redirect
```

### 왜 필요한가

Nginx는 정적 파일 서버, 리버스 프록시, 로드밸런서, TLS 종료 지점으로 자주 쓰인다.

배포 중 502, 경로 404, HTTPS 리다이렉트 문제를 디버깅하려면 Nginx 설정을 읽을 수 있어야 한다.

## 14. 장애 분석

### 공부할 내용

```text
DNS failure
Connection refused
Connection timed out
No route to host
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
Too many redirects
CORS error
SSL certificate error
Mixed content
WebSocket failed
client IP가 127.0.0.1로 찍히는 문제
HTTP인데 HTTPS로 인식 못 하는 문제
```

### 왜 필요한가

운영에서는 "안 된다"를 구체적인 원인으로 좁혀야 한다.

DNS, TCP 연결, 포트, TLS, HTTP, 애플리케이션 로그 순서로 확인하는 습관이 필요하다.

## 15. 배포와 무중단

### 공부할 내용

```text
Blue/Green Deployment
Canary Deployment
Rolling Deployment
Traffic Switching
Health Check
Readiness Check
Liveness Check
Graceful Shutdown
SIGTERM
SIGKILL
docker stop --time
Connection Draining
Rollback
DB Migration 호환성
```

### 왜 필요한가

컨테이너 하나만 교체하면 배포 중 서비스 중단이 생길 수 있다.

Blue/Green 배포, health check, graceful shutdown을 이해하면 중단 시간을 줄이고 롤백 가능한 구조를 만들 수 있다.

## 16. Docker 네트워크

### 공부할 내용

```text
bridge network
host network
none network
container port
host port
port mapping
docker run -p
Docker DNS
container name resolution
docker-compose network
같은 컨테이너 내부 포트와 호스트 포트 차이
```

### 왜 필요한가

Docker에서는 컨테이너 내부 포트와 호스트 포트가 다르다.

blue 컨테이너와 green 컨테이너가 둘 다 내부에서는 8080을 써도, 호스트 포트는 8080과 8081처럼 다르게 매핑할 수 있다.

## 17. Kubernetes 네트워크

### 공부할 내용

```text
Pod IP
ClusterIP
NodePort
LoadBalancer
Service
Endpoint / EndpointSlice
Ingress
IngressClass
Ingress Controller
pathType: Prefix / Exact
TLS Secret
readinessProbe
livenessProbe
NetworkPolicy
CoreDNS
kube-proxy
CNI
```

### 왜 필요한가

Kubernetes에서는 Pod가 직접 외부에 노출되지 않는다.

Service와 Ingress를 통해 트래픽을 전달하고, Ingress Controller가 리버스 프록시처럼 동작한다.

## 18. 클라우드 네트워크

### 공부할 내용

```text
VPC
Subnet
Public Subnet
Private Subnet
Route Table
Internet Gateway
NAT Gateway
Security Group
NACL
Elastic IP
ALB
NLB
Target Group
Health Check
Route 53
CloudFront
WAF
```

### 왜 필요한가

클라우드에서 네트워크는 직접 장비를 만지는 대신 VPC, Subnet, Route Table, Security Group 같은 리소스로 구성한다.

EC2, RDS, ALB, NAT Gateway를 배치하려면 public/private subnet과 route table 구조를 이해해야 한다.

## 19. IAM

### 공부할 내용

```text
사용자
그룹
역할
Policy
최소 권한 원칙
Access Key
Role 기반 권한
EC2 Role
GitHub Actions OIDC
```

### 왜 필요한가

클라우드는 권한 설정이 잘못되면 보안 사고나 배포 실패로 이어진다.

서버, CI/CD, 애플리케이션이 AWS 리소스에 접근할 때는 IAM Role과 최소 권한 원칙을 이해해야 한다.

## 20. Compute

### 공부할 내용

```text
EC2
AMI
Instance Type
Auto Scaling Group
Launch Template
Elastic IP
User Data
ECS
EKS
Fargate
```

### 왜 필요한가

Compute는 애플리케이션이 실제로 실행되는 영역이다.

처음에는 EC2로 시작하고, 이후에는 ECS, EKS, Fargate 같은 관리형 컨테이너 실행 환경으로 확장할 수 있다.

## 21. Storage

### 공부할 내용

```text
S3
EBS
EFS
Object Storage
Block Storage
File Storage
S3 bucket policy
S3 lifecycle
S3 static website hosting
```

### 왜 필요한가

애플리케이션은 코드 실행뿐 아니라 파일, 이미지, 로그, 백업 데이터를 저장해야 한다.

S3, EBS, EFS는 저장 방식과 사용 목적이 다르므로 구분해서 이해해야 한다.

## 22. Database

### 공부할 내용

```text
RDS
Aurora
DynamoDB
ElastiCache
Backup
Read Replica
Multi-AZ
Connection Pool
```

### 왜 필요한가

운영 환경에서는 DB를 직접 설치하기보다 관리형 서비스를 많이 사용한다.

백업, 장애 조치, 읽기 복제, 커넥션 풀을 이해해야 안정적인 백엔드 운영이 가능하다.

## 23. Monitoring / Logging

### 공부할 내용

```text
CloudWatch Metrics
CloudWatch Logs
Alarm
Dashboard
Log retention
Tracing
AWS X-Ray
Application log
Access log
Error log
```

### 왜 필요한가

장애를 해결하려면 먼저 관측할 수 있어야 한다.

메트릭, 로그, 알람, 트레이싱을 통해 CPU, 메모리, 응답 시간, 에러율, 요청 흐름을 확인해야 한다.

## 24. CI/CD

### 공부할 내용

```text
GitHub Actions
Docker image build
ECR
배포 스크립트
Blue/Green Deployment
Rollback
Secret 관리
OIDC
환경 변수
```

### 왜 필요한가

CI/CD는 코드를 자동으로 빌드, 테스트, 배포하는 흐름이다.

배포 자동화가 있어야 실수와 반복 작업을 줄이고, rollback 가능한 구조를 만들 수 있다.

## 25. IaC

### 공부할 내용

```text
Terraform
CloudFormation
CDK
state 관리
module
plan
apply
destroy
drift
```

### 왜 필요한가

클라우드 리소스를 콘솔에서 수동으로 만들면 재현성과 추적성이 떨어진다.

IaC는 VPC, EC2, RDS, ALB 같은 리소스를 코드로 관리해 일관된 인프라를 만들 수 있게 해준다.

## 26. Container Platform

### 공부할 내용

```text
ECS
EKS
Fargate
Task Definition
Service
Cluster
Ingress / Load Balancer 연동
Rolling update
Blue/Green deployment
```

### 왜 필요한가

EC2에 직접 컨테이너를 띄우는 방식은 단순하지만 운영 부담이 있다.

ECS, EKS, Fargate를 이해하면 컨테이너 스케줄링, 서비스 복구, 배포 전략을 더 체계적으로 다룰 수 있다.

## 27. API Gateway

### 공부할 내용

```text
API Gateway란 무엇인가
Reverse Proxy와 차이
인증 / 인가
JWT 검증
API Key
Rate Limit
Quota
Request / Response transform
Version routing
Kong
AWS API Gateway
Spring Cloud Gateway
```

### 왜 필요한가

API Gateway는 단순 리버스 프록시보다 API 운영 기능이 강한 진입점이다.

인증, 사용량 제한, 버전 라우팅, 요청 변환 같은 기능이 필요할 때 사용한다.

## 28. Service Mesh

### 공부할 내용

```text
Service Mesh란 무엇인가
Sidecar proxy
Envoy
Istio
Linkerd
mTLS
Traffic splitting
Retry
Timeout
Circuit breaker
Observability
Ingress Gateway
Egress Gateway
```

### 왜 필요한가

서비스가 많아지면 서비스 간 통신을 일관되게 제어하기 어려워진다.

Service Mesh는 서비스 간 mTLS, 재시도, timeout, 트래픽 분할, 관측성을 프록시 계층에서 제공한다.

## 29. 보안

### 공부할 내용

```text
Firewall
Security Group
NACL
IAM Policy
KMS
Secrets Manager
Parameter Store
WAF
CloudTrail
DDoS 방어
Rate Limiting
IP allowlist / denylist
TLS 설정
HSTS
CORS 보안
Cookie Secure / HttpOnly / SameSite
Header 보안
Zero Trust 개념
```

### 왜 필요한가

운영 환경에서는 기능이 동작하는 것만큼 안전하게 동작하는 것이 중요하다.

네트워크 접근 제어, 권한, 암호화, 시크릿 관리, 감사 로그는 기본 보안 요소다.

## 30. 비용

### 공부할 내용

```text
Free Tier
Billing
Cost Explorer
Budget
Reserved Instance
Savings Plans
NAT Gateway 비용
로그 저장 비용
데이터 전송 비용
미사용 리소스 정리
```

### 왜 필요한가

클라우드는 리소스를 쉽게 만들 수 있지만 비용도 쉽게 증가한다.

특히 NAT Gateway, 로그 저장, 데이터 전송, 미사용 EC2나 EBS는 초보자가 놓치기 쉬운 비용 포인트다.

## 31. 실습 명령어

### 공부할 내용

```text
ping
traceroute
dig
nslookup
curl -v
curl -I
nc -vz
telnet
lsof -i
netstat
ss
tcpdump
wireshark
openssl s_client
docker ps
docker logs
nginx -t
kubectl get ingress
kubectl describe svc
kubectl get endpoints
```

### 왜 필요한가

개념을 아는 것과 실제 장애를 확인하는 것은 다르다.

명령어를 통해 DNS, TCP 연결, 포트, HTTP 응답, TLS 인증서, 컨테이너 상태, Kubernetes 리소스를 직접 확인할 수 있어야 한다.

## 추천 학습 순서

```text
1. 네트워크 기본
2. 주소 체계
3. 포트와 소켓
4. TCP / UDP
5. DNS
6. HTTP
7. HTTPS / TLS
8. 프록시 기본
9. 리버스 프록시
10. 프록시 헤더
11. 라우팅
12. 로드밸런싱
13. Nginx 심화
14. 장애 분석
15. 배포와 무중단
16. Docker 네트워크
17. 클라우드 네트워크
18. IAM
19. Compute
20. Storage
21. Database
22. Monitoring / Logging
23. CI/CD
24. IaC
25. Container Platform
26. Kubernetes 네트워크
27. API Gateway
28. Service Mesh
29. 보안
30. 비용
31. 실습 명령어
```

## 우선순위 높은 핵심 주제

현재 EC2, Docker, Nginx 기반 배포 경험과 가장 직접적으로 연결되는 주제는 아래와 같다.

```text
Nginx location
proxy_pass
X-Forwarded-* header
502 / 503 / 504
Blue-Green Deployment
Graceful Shutdown
Docker port mapping
AWS VPC
Security Group
AWS ALB / NLB
Route 53
IAM Role
CloudWatch Logs
GitHub Actions
ECR
Kubernetes Ingress
```

## 최종 정리

```text
Network
→ HTTP / HTTPS
→ Proxy / Routing / Nginx
→ Docker Network
→ AWS VPC / ALB / Route 53
→ EC2 / S3 / RDS / IAM
→ CI/CD / Monitoring
→ Terraform
→ ECS 또는 Kubernetes
→ Security / Cost
```
