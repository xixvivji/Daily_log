# 2026-07-07 Nginx, Docker, AWS 운영 인프라 학습 내용

## 현재까지 정리한 내용

지금까지는 인프라 학습의 큰 흐름을 잡았다.

```text
네트워크 기본
프록시 / 리버스 프록시
라우팅
로드밸런싱
배포 전략
단일 EC2 + Docker + Nginx blue/green 배포
```

현재 이해한 핵심 구조는 다음과 같다.

```text
사용자
→ Nginx
→ blue container 또는 green container
→ backend application
```

이제 이어서 볼 학습 내용은 이 구조를 더 정확히 설명하고, 클라우드 운영 구조로 확장하는 주제들이다.

## 학습 내용 순서

```text
1. Nginx 심화
2. Docker 네트워크
3. AWS VPC / Security Group / ALB
4. DNS / Route 53
5. HTTPS / TLS
6. Monitoring / Logging
7. CI/CD 배포 자동화
8. Kubernetes Service / Ingress
```

## 1. Nginx 심화

### Nginx 심화를 먼저 공부하는 이유

현재 blue/green 배포 구조에서 Nginx는 외부 요청을 받아 active 컨테이너로 넘기는 핵심 진입점이다.

```text
사용자
→ Nginx
→ blue:8080 또는 green:8081
```

Nginx 설정을 이해해야 아래 문제를 분석할 수 있다.

```text
Nginx 뒤에서만 API 404 발생
백엔드 컨테이너는 살아 있는데 502 발생
응답 지연으로 504 발생
파일 업로드 시 413 발생
HTTPS 리다이렉트 반복
클라이언트 IP가 전부 127.0.0.1로 찍힘
```

### Nginx 심화에서 볼 내용

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
X-Forwarded-* 헤더
HTTP to HTTPS redirect
```

### Nginx 심화 핵심 목표

```text
server와 location의 역할을 설명할 수 있다.
proxy_pass가 백엔드로 path를 어떻게 넘기는지 설명할 수 있다.
upstream으로 blue/green active 대상을 바꾸는 구조를 설명할 수 있다.
nginx -t 후 reload해야 하는 이유를 설명할 수 있다.
502, 504가 났을 때 error.log와 upstream을 확인할 수 있다.
```

## 2. Docker 네트워크

### Docker 네트워크를 공부하는 이유

단일 EC2 blue/green 배포는 Docker 포트 매핑을 이해해야 정확히 설명할 수 있다.

예:

```text
blue container 내부 8080 → EC2 host 8080
green container 내부 8080 → EC2 host 8081
```

컨테이너 내부에서는 둘 다 8080을 써도 되지만, EC2 호스트에서는 같은 IP와 같은 포트를 동시에 점유할 수 없다.

### Docker 네트워크에서 볼 내용

```text
container port
host port
docker run -p
bridge network
host network
container localhost
host localhost
Docker DNS
container name resolution
docker-compose network
```

### Docker 네트워크 핵심 목표

```text
-p 8081:8080의 의미를 설명할 수 있다.
컨테이너 내부 localhost와 호스트 localhost 차이를 설명할 수 있다.
blue/green 컨테이너가 같은 내부 포트를 써도 되는 이유를 설명할 수 있다.
Nginx가 컨테이너 내부 포트가 아니라 호스트 포트로 접근한다는 점을 설명할 수 있다.
```

## 3. AWS VPC / Security Group / ALB

### AWS 네트워크를 공부하는 이유

현재 구조는 EC2 한 대가 직접 요청을 받는 구조에 가깝다.

```text
사용자
→ EC2 Public IP
→ Nginx
→ Docker container
```

운영 구조로 확장하면 보통 ALB를 앞에 둔다.

```text
사용자
→ Route 53
→ ALB
→ Target Group
→ EC2
→ Nginx
→ Docker container
```

이 구조를 이해하려면 AWS 네트워크 기본 리소스를 알아야 한다.

### AWS 네트워크에서 볼 내용

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
```

### AWS 네트워크 핵심 목표

```text
VPC와 Subnet의 관계를 설명할 수 있다.
Public Subnet과 Private Subnet 차이를 설명할 수 있다.
Security Group이 인스턴스 단위 방화벽이라는 점을 설명할 수 있다.
ALB, Target Group, Health Check의 관계를 설명할 수 있다.
사용자 → ALB → EC2 → Nginx → Container 흐름을 그릴 수 있다.
```

## 4. DNS / Route 53

### DNS와 Route 53을 공부하는 이유

사용자는 서버 IP를 직접 입력하지 않고 도메인으로 서비스에 접속한다.

```text
https://api.example.com
```

이 도메인이 ALB나 EC2로 연결되려면 DNS 설정을 이해해야 한다.

### DNS와 Route 53에서 볼 내용

```text
Domain
Hosted Zone
A Record
AAAA Record
CNAME
Alias Record
TTL
DNS Cache
Route 53
ALB DNS Name
```

### DNS와 Route 53 핵심 목표

```text
도메인이 ALB까지 연결되는 흐름을 설명할 수 있다.
A Record, CNAME, Alias Record 차이를 설명할 수 있다.
TTL 때문에 DNS 변경이 늦게 보일 수 있다는 점을 설명할 수 있다.
```

## 5. HTTPS / TLS

### HTTPS와 TLS를 공부하는 이유

운영 서비스는 대부분 HTTPS를 사용한다.

그리고 HTTPS 연결을 어디서 종료할지 결정해야 한다.

```text
사용자
→ HTTPS
→ ALB 또는 Nginx
→ HTTP 또는 HTTPS
→ Backend
```

TLS 종료 위치를 잘못 이해하면 리다이렉트, 쿠키, OAuth, mixed content 문제가 생길 수 있다.

### HTTPS와 TLS에서 볼 내용

```text
TLS
HTTPS
Certificate
CA
ACM
TLS termination
TLS passthrough
backend re-encryption
SNI
HTTP to HTTPS redirect
Secure Cookie
X-Forwarded-Proto
```

### HTTPS와 TLS 핵심 목표

```text
HTTPS와 TLS의 관계를 설명할 수 있다.
TLS termination이 무엇인지 설명할 수 있다.
ALB에서 TLS를 종료하는 구조와 Nginx에서 TLS를 종료하는 구조를 구분할 수 있다.
X-Forwarded-Proto가 왜 필요한지 설명할 수 있다.
```

## 6. Monitoring / Logging

### 모니터링과 로깅을 공부하는 이유

운영에서는 장애가 났을 때 원인을 찾아야 한다.

원인을 찾으려면 로그와 메트릭이 있어야 한다.

```text
메트릭 → 시스템 상태를 숫자로 보여줌
로그 → 실제 요청과 에러 기록을 보여줌
트레이싱 → 요청이 여러 서비스를 지나간 흐름을 보여줌
```

### 모니터링과 로깅에서 볼 내용

```text
CloudWatch Logs
CloudWatch Metrics
Alarm
Dashboard
Log retention
ALB access log
Nginx access.log
Nginx error.log
Docker logs
5xx 에러율
응답 시간
Target Health
```

### 모니터링과 로깅 핵심 목표

```text
메트릭과 로그의 차이를 설명할 수 있다.
Nginx access.log와 error.log를 구분할 수 있다.
CloudWatch Logs와 Metrics의 역할을 설명할 수 있다.
장애가 났을 때 어떤 로그와 지표를 먼저 볼지 정할 수 있다.
```

## 7. CI/CD 배포 자동화

### CI/CD를 공부하는 이유

수동 배포는 실수하기 쉽고 반복 작업이 많다.

CI/CD는 빌드, 테스트, 이미지 생성, 배포, 검증, 롤백 흐름을 자동화한다.

blue/green 배포와 연결하면 다음 흐름이 된다.

```text
git push
→ GitHub Actions
→ Docker image build
→ image push
→ EC2 접속
→ inactive 컨테이너 실행
→ health check
→ Nginx 전환
→ old 컨테이너 종료
```

### CI/CD에서 볼 내용

```text
GitHub Actions
workflow
job
step
secret
environment variable
Docker image build
ECR
SSH deploy
OIDC
health check
rollback
```

### CI/CD 핵심 목표

```text
CI와 CD의 차이를 설명할 수 있다.
GitHub Actions workflow 구조를 설명할 수 있다.
Docker image를 build하고 registry에 push하는 흐름을 설명할 수 있다.
blue/green 배포 자동화에서 health check와 rollback이 왜 필요한지 설명할 수 있다.
```

## 8. Kubernetes Service / Ingress

### Kubernetes Service와 Ingress를 공부하는 이유

EC2 한 대에서 Docker 컨테이너를 직접 운영하는 방식은 단순하지만 확장성과 복구 자동화가 약하다.

Kubernetes로 가면 Pod, Service, Ingress가 트래픽 흐름을 담당한다.

```text
사용자
→ Ingress Controller
→ Service
→ Pod
```

### Kubernetes Service와 Ingress에서 볼 내용

```text
Pod
Service
ClusterIP
NodePort
LoadBalancer
Endpoint
EndpointSlice
Ingress
IngressClass
Ingress Controller
pathType: Prefix / Exact
TLS Secret
readinessProbe
livenessProbe
```

### Kubernetes Service와 Ingress 핵심 목표

```text
Pod와 Service의 관계를 설명할 수 있다.
Ingress와 Ingress Controller의 차이를 설명할 수 있다.
Service가 Pod IP 변경 문제를 어떻게 해결하는지 설명할 수 있다.
readinessProbe가 트래픽 전환과 어떤 관련이 있는지 설명할 수 있다.
```

## 우선순위 요약

지금 바로 이어서 공부할 순서는 다음과 같다.

```text
1. Nginx 심화
2. Docker 네트워크
3. AWS VPC / Security Group / ALB
4. DNS / Route 53
5. HTTPS / TLS
6. Monitoring / Logging
7. CI/CD 배포 자동화
8. Kubernetes Service / Ingress
```

## 오늘 바로 시작할 주제

오늘 하나만 고르면 **Nginx 심화**를 먼저 보면 된다.

특히 아래 다섯 가지부터 보면 좋다.

```text
location
proxy_pass
upstream
access.log / error.log
timeout
```

이 다섯 가지를 이해하면 현재까지 정리한 `EC2 + Docker + Nginx blue/green` 배포 구조를 훨씬 정확하게 설명할 수 있다.

## 한 줄 정리

```text
지금은 네트워크와 프록시 큰그림을 끝내고, 실제 배포 구조를 구성하는 Nginx, Docker, AWS 네트워크, 운영 자동화로 넘어갈 단계다.
```
