# 2026-07-07 Nginx, Docker 네트워크, AWS 배포 인프라 학습 정리

## 현재 기준

지금까지는 네트워크 큰그림, 프록시, 리버스 프록시, 라우팅, 단일 EC2 blue/green 배포 개념을 정리했다.

이제부터는 실제 배포와 운영에서 바로 쓰이는 세부 주제로 들어가면 된다.

현재 이해한 구조는 다음과 같다.

```text
사용자
→ Nginx
→ blue container 또는 green container
→ backend application
```

이 구조를 더 정확히 이해하려면 다음 흐름으로 공부하는 것이 좋다.

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

## 1. Nginx 심화

### Nginx를 공부해야 하는 이유

Nginx는 지금 구조에서 외부 요청을 처음 받는 진입점이다.

```text
사용자 요청
→ Nginx
→ 현재 active 컨테이너
```

Nginx가 어떤 요청을 어떤 컨테이너로 넘기는지 결정한다.

따라서 Nginx 설정을 이해하지 못하면 아래 문제를 제대로 분석하기 어렵다.

```text
배포 후 특정 API만 404
백엔드 컨테이너는 살아 있는데 502 발생
요청이 오래 걸리면 504 발생
파일 업로드 시 413 발생
HTTPS 리다이렉트 반복
클라이언트 IP가 전부 127.0.0.1로 찍힘
blue/green 전환 후 이전 컨테이너로 요청이 감
```

### Nginx 핵심 개념

```text
server block
location matching
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
X-Forwarded-* headers
```

### server block

`server` 블록은 어떤 포트와 도메인으로 들어온 요청을 처리할지 정한다.

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

의미:

```text
80번 포트로 들어온 example.com 요청을 받는다.
요청 path가 /에 매칭되면 127.0.0.1:8080으로 넘긴다.
```

### location matching

`location`은 요청 path를 보고 어떤 처리 블록을 사용할지 고른다.

```nginx
location = /health {
    return 200 "ok";
}

location /api/ {
    proxy_pass http://127.0.0.1:8080;
}

location / {
    proxy_pass http://127.0.0.1:3000;
}
```

요청별 결과:

```text
/health      → 정확히 /health
/api/users   → /api/ location
/about       → / location
/            → / location
```

중요한 점:

```text
location / 는 거의 모든 요청에 매칭될 수 있다.
더 구체적인 location이 있으면 그쪽이 먼저 선택될 수 있다.
health check는 location = /health처럼 정확히 매칭시키는 경우가 많다.
```

### proxy_pass trailing slash

`proxy_pass` 뒤에 슬래시가 있는지 없는지에 따라 백엔드가 받는 path가 달라질 수 있다.

예시 1:

```nginx
location /api/ {
    proxy_pass http://backend;
}
```

요청:

```text
/api/users
```

백엔드가 받는 path:

```text
/api/users
```

예시 2:

```nginx
location /api/ {
    proxy_pass http://backend/;
}
```

요청:

```text
/api/users
```

백엔드가 받는 path:

```text
/users
```

이 차이 때문에 Nginx 뒤에서만 404가 나는 경우가 있다.

### upstream block

`upstream`은 백엔드 서버 묶음을 정의한다.

```nginx
upstream backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;

    location / {
        proxy_pass http://backend;
    }
}
```

blue/green 배포에서는 active 컨테이너 포트를 바꿔서 전환할 수 있다.

```nginx
upstream backend {
    server 127.0.0.1:8081; # green
}
```

### nginx -t와 reload

Nginx 설정을 바꾸면 바로 reload하기 전에 문법 검사를 해야 한다.

```bash
nginx -t
```

문제가 없으면 reload한다.

```bash
nginx -s reload
```

또는 systemd 환경에서는:

```bash
sudo systemctl reload nginx
```

중요한 이유:

```text
설정 파일에 문법 오류가 있으면 Nginx reload가 실패할 수 있다.
blue/green 전환 중 잘못된 설정을 반영하면 전체 서비스 장애가 날 수 있다.
```

### access.log와 error.log

Nginx 장애 분석에서 로그는 필수다.

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

확인할 것:

```text
요청이 Nginx까지 들어왔는가
응답 상태 코드가 무엇인가
어떤 upstream으로 보냈는가
upstream 연결이 실패했는가
timeout이 났는가
```

### Nginx 심화 정리 목표

```text
server와 location의 역할을 설명할 수 있다.
proxy_pass의 path 전달 방식을 설명할 수 있다.
upstream을 사용해 active 컨테이너를 전환하는 구조를 설명할 수 있다.
nginx -t와 reload의 차이를 설명할 수 있다.
502, 504가 났을 때 error.log를 먼저 확인할 수 있다.
```

## 2. Docker 네트워크

### Docker 네트워크를 공부해야 하는 이유

blue/green 배포는 컨테이너 두 개를 동시에 띄우는 구조다.

```text
blue container
green container
```

이때 컨테이너 내부 포트와 EC2 호스트 포트를 구분하지 못하면 배포 구조가 헷갈린다.

예:

```text
blue container 내부 8080 → EC2 host 8080
green container 내부 8080 → EC2 host 8081
```

둘 다 컨테이너 내부에서는 8080을 써도 된다.

하지만 EC2 호스트에서는 같은 IP와 같은 포트를 동시에 점유할 수 없다.

### Docker 네트워크 핵심 개념

```text
container port
host port
docker run -p
bridge network
host network
Docker DNS
container name resolution
docker-compose network
localhost 차이
```

### container port와 host port

Docker 포트 매핑은 아래처럼 쓴다.

```bash
docker run -p 8081:8080 green-app
```

의미:

```text
EC2 host의 8081번 포트
→ green-app 컨테이너 내부 8080번 포트
```

즉 앞쪽이 호스트 포트이고, 뒤쪽이 컨테이너 포트다.

```text
-p HOST_PORT:CONTAINER_PORT
```

blue/green 예:

```bash
docker run -d --name backend-blue -p 8080:8080 backend:blue
docker run -d --name backend-green -p 8081:8080 backend:green
```

구조:

```text
Nginx → 127.0.0.1:8080 → blue container 내부 8080
Nginx → 127.0.0.1:8081 → green container 내부 8080
```

### localhost 주의점

호스트에서 `localhost`는 EC2 자기 자신이다.

컨테이너 안에서 `localhost`는 그 컨테이너 자기 자신이다.

즉 컨테이너 안에서 `localhost:3306`을 호출하면 EC2의 MySQL이 아니라 컨테이너 내부의 3306을 찾는다.

이 차이를 모르면 컨테이너에서 DB나 다른 서비스에 연결할 때 문제가 생긴다.

### Docker bridge network

기본 Docker 네트워크는 bridge 방식이다.

컨테이너는 Docker가 만든 가상 네트워크 안에서 IP를 받는다.

컨테이너끼리는 같은 Docker 네트워크에 있으면 이름으로 통신할 수 있다.

docker-compose 예:

```yaml
services:
  backend:
    image: backend
    ports:
      - "8080:8080"

  redis:
    image: redis
```

이 경우 backend 컨테이너는 redis에 다음처럼 접근할 수 있다.

```text
redis:6379
```

### Docker 네트워크 정리 목표

```text
-p 8081:8080의 의미를 설명할 수 있다.
컨테이너 내부 localhost와 호스트 localhost 차이를 설명할 수 있다.
blue/green 컨테이너가 같은 내부 포트를 써도 되는 이유를 설명할 수 있다.
Nginx가 호스트 포트로 컨테이너에 접근한다는 점을 설명할 수 있다.
```

## 3. AWS VPC / Security Group / ALB

### AWS 네트워크를 공부해야 하는 이유

현재 구조는 EC2 한 대가 직접 요청을 받는 구조에 가깝다.

```text
사용자
→ EC2 Public IP
→ Nginx
→ Docker container
```

클라우드 운영 구조에서는 보통 ALB를 앞에 둔다.

```text
사용자
→ Route 53
→ ALB
→ Target Group
→ EC2
→ Nginx
→ Docker container
```

이 구조를 이해하려면 VPC, Subnet, Route Table, Security Group, ALB, Target Group을 알아야 한다.

### AWS 네트워크 핵심 개념

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

### VPC

VPC는 AWS 안에서 만드는 가상 네트워크다.

예:

```text
10.0.0.0/16
```

이 VPC 안에 여러 Subnet을 만든다.

```text
public subnet: 10.0.1.0/24
private subnet: 10.0.2.0/24
```

### Public Subnet과 Private Subnet

Public Subnet은 Internet Gateway로 나가는 route가 있는 subnet이다.

Private Subnet은 직접 인터넷으로 나가는 route가 없는 subnet이다.

일반적인 구조:

```text
ALB → Public Subnet
EC2 / App Server → Private Subnet
RDS → Private Subnet
```

처음에는 단순하게 EC2를 public subnet에 둘 수 있지만, 운영 구조에서는 EC2를 private subnet에 두고 ALB만 외부에 노출하는 구성이 더 안전하다.

### Security Group

Security Group은 인스턴스나 ALB 단위 방화벽이다.

예:

```text
ALB Security Group
- inbound 80 from 0.0.0.0/0
- inbound 443 from 0.0.0.0/0

EC2 Security Group
- inbound 80 from ALB Security Group
- inbound 22 from 내 IP
```

이렇게 하면 사용자는 ALB로만 접근하고, EC2는 ALB에서 오는 요청만 받게 만들 수 있다.

### ALB와 Target Group

ALB는 L7 로드밸런서다.

HTTP Host, Path, Header 같은 정보를 보고 라우팅할 수 있다.

Target Group은 ALB가 트래픽을 보낼 대상 묶음이다.

```text
ALB Listener : 443
→ Target Group
→ EC2 instances
```

ALB는 Target Group에 health check를 수행한다.

Target이 unhealthy면 트래픽을 보내지 않는다.

### AWS 네트워크 정리 목표

```text
VPC와 Subnet의 관계를 설명할 수 있다.
Public Subnet과 Private Subnet 차이를 설명할 수 있다.
Security Group이 어떤 역할을 하는지 설명할 수 있다.
ALB, Target Group, Health Check의 관계를 설명할 수 있다.
사용자 → ALB → EC2 → Nginx → Container 흐름을 그릴 수 있다.
```

## 4. DNS / Route 53

### DNS와 Route 53을 공부해야 하는 이유

사용자는 보통 IP가 아니라 도메인으로 서비스에 접속한다.

```text
https://api.example.com
```

이 도메인이 ALB나 EC2로 연결되려면 DNS를 알아야 한다.

### DNS와 Route 53 핵심 개념

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

### Route 53과 ALB 연결

ALB는 고정 IP를 직접 쓰기보다 DNS Name을 제공한다.

예:

```text
my-alb-123.ap-northeast-2.elb.amazonaws.com
```

Route 53에서는 보통 Alias Record로 도메인을 ALB에 연결한다.

```text
api.example.com
→ Alias Record
→ ALB DNS Name
```

### TTL

TTL은 DNS 응답을 얼마나 오래 캐싱할지 정하는 값이다.

TTL이 길면 DNS 변경이 바로 반영되지 않을 수 있다.

운영 중 도메인 이전이나 ALB 교체를 할 때 TTL을 고려해야 한다.

### DNS 정리 목표

```text
도메인이 ALB까지 연결되는 흐름을 설명할 수 있다.
A Record, CNAME, Alias Record 차이를 설명할 수 있다.
TTL 때문에 DNS 변경이 늦게 보일 수 있다는 점을 설명할 수 있다.
```

## 5. HTTPS / TLS

### HTTPS와 TLS를 공부해야 하는 이유

실제 서비스는 대부분 HTTPS를 사용한다.

그리고 HTTPS를 어디서 종료할지 정해야 한다.

```text
사용자
→ HTTPS
→ ALB 또는 Nginx
→ HTTP 또는 HTTPS
→ Backend
```

TLS 종료 위치를 잘못 이해하면 HTTPS 리다이렉트, Secure Cookie, OAuth callback, mixed content 문제가 생길 수 있다.

### HTTPS와 TLS 핵심 개념

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

### TLS termination

TLS termination은 HTTPS 암호화 연결을 특정 지점에서 끝내는 것이다.

예:

```text
사용자
→ HTTPS
→ ALB
→ HTTP
→ EC2 Nginx
→ backend container
```

이 구조에서는 ALB가 인증서를 가지고 HTTPS를 처리한다.

ALB 뒤쪽은 HTTP로 통신할 수도 있다.

다른 구조:

```text
사용자
→ HTTPS
→ Nginx
→ HTTP
→ backend container
```

이 경우 Nginx가 인증서를 가지고 HTTPS를 처리한다.

### X-Forwarded-Proto

프록시 뒤의 백엔드는 자기에게 HTTP 요청이 왔다고 생각할 수 있다.

하지만 원래 사용자는 HTTPS로 접속했을 수 있다.

이 정보를 넘기기 위해 `X-Forwarded-Proto`를 사용한다.

```nginx
proxy_set_header X-Forwarded-Proto $scheme;
```

이 설정이 없으면 다음 문제가 생길 수 있다.

```text
HTTPS 리다이렉트 무한 반복
Secure Cookie 설정 문제
OAuth redirect_uri 문제
백엔드가 http URL을 생성하는 문제
```

### HTTPS / TLS 정리 목표

```text
HTTPS와 TLS의 관계를 설명할 수 있다.
TLS termination이 무엇인지 설명할 수 있다.
ALB에서 TLS 종료하는 구조와 Nginx에서 TLS 종료하는 구조를 구분할 수 있다.
X-Forwarded-Proto가 왜 필요한지 설명할 수 있다.
```

## 6. CI/CD와 배포 자동화

### CI/CD를 공부해야 하는 이유

수동 배포는 실수하기 쉽고 반복이 많다.

CI/CD는 코드를 push했을 때 빌드, 테스트, 이미지 생성, 서버 배포까지 자동화하는 흐름이다.

현재 blue/green 배포와 연결하면 다음 흐름이 된다.

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

### CI/CD 핵심 개념

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
rollback
```

### 배포 자동화 정리 목표

```text
CI와 CD의 차이를 설명할 수 있다.
GitHub Actions workflow 구조를 설명할 수 있다.
Docker image를 build하고 registry에 push하는 흐름을 설명할 수 있다.
blue/green 배포를 자동화할 때 health check와 rollback이 왜 필요한지 설명할 수 있다.
```

## 7. Monitoring / Logging

### 모니터링과 로깅을 공부해야 하는 이유

운영에서는 장애가 났을 때 원인을 찾아야 한다.

원인을 찾으려면 로그와 메트릭이 있어야 한다.

```text
메트릭 → 시스템 상태 숫자
로그 → 실제 요청과 에러 기록
트레이싱 → 요청이 여러 서비스를 지나간 흐름
```

### 모니터링과 로깅 핵심 개념

```text
CloudWatch Metrics
CloudWatch Logs
Alarm
Dashboard
Log retention
Application log
Nginx access.log
Nginx error.log
Docker logs
Tracing
```

### 확인할 지표

```text
CPU 사용률
Memory 사용률
Disk 사용률
HTTP 5xx 비율
응답 시간
ALB Target Response Time
Target Health
컨테이너 재시작 여부
```

### Monitoring / Logging 정리 목표

```text
메트릭과 로그의 차이를 설명할 수 있다.
Nginx access.log와 error.log를 구분할 수 있다.
CloudWatch Logs와 Metrics의 역할을 설명할 수 있다.
장애가 났을 때 어떤 로그와 지표를 먼저 볼지 정할 수 있다.
```

## 8. Kubernetes Service / Ingress

### Kubernetes Service와 Ingress를 공부해야 하는 이유

EC2 한 대에서 Docker 컨테이너를 직접 운영하는 방식은 단순하지만 확장성과 복구 자동화가 약하다.

Kubernetes로 가면 Pod, Service, Ingress가 트래픽 흐름을 담당한다.

```text
사용자
→ Ingress Controller
→ Service
→ Pod
```

### Kubernetes Service와 Ingress 핵심 개념

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

### Service

Pod는 언제든 새로 만들어지고 IP가 바뀔 수 있다.

Service는 변하는 Pod들을 안정적으로 묶어주는 진입점이다.

```text
Service
→ Pod A
→ Pod B
→ Pod C
```

### Ingress

Ingress는 HTTP/HTTPS 요청을 어느 Service로 보낼지 정하는 규칙이다.

실제로 프록시하는 것은 Ingress Controller다.

```text
Ingress = 규칙
Ingress Controller = 실제 리버스 프록시
```

예:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
```

의미:

```text
api.example.com으로 들어온 요청을 api-service:8080으로 보낸다.
```

### Kubernetes 정리 목표

```text
Pod와 Service의 관계를 설명할 수 있다.
Ingress와 Ingress Controller의 차이를 설명할 수 있다.
Service가 Pod IP 변경 문제를 어떻게 해결하는지 설명할 수 있다.
readinessProbe가 트래픽 전환과 어떤 관련이 있는지 설명할 수 있다.
```

## 추천 순서 요약

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

## 당장 다음에 자세히 정리할 주제

가장 먼저 자세히 정리할 주제는 **Nginx 심화**다.

이유:

```text
현재 blue/green 배포 구조와 가장 직접적으로 연결된다.
배포 중 자주 나는 404, 502, 504 문제와 연결된다.
Docker와 AWS로 넘어가기 전에 요청이 어떻게 프록시되는지 정확히 알아야 한다.
```

Nginx 심화에서 먼저 볼 세부 항목:

```text
server block
location matching
proxy_pass path 처리
upstream block
nginx -t / reload
access.log / error.log
timeout 설정
X-Forwarded-* 헤더
```

## 최종 정리

```text
지금은 네트워크와 프록시 큰그림을 끝내고,
실제 배포 구조를 구성하는 Nginx, Docker, AWS 네트워크로 넘어갈 단계다.
다음 학습은 Nginx 심화부터 시작하는 것이 가장 자연스럽다.
```
