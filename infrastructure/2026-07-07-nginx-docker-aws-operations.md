# 2026-07-07 Nginx, Docker, AWS 운영 인프라 학습 내용

## 전체 그림

지금까지 정리한 네트워크, 프록시, 라우팅은 결국 아래 운영 트래픽 구조를 이해하기 위한 기반이다.

```text
사용자
→ DNS
→ ALB 또는 EC2 Public IP
→ Nginx
→ Docker container
→ Backend application
```

단일 EC2 blue/green 배포 구조로 보면 더 구체적으로는 다음과 같다.

```text
사용자
→ Nginx
→ blue container: host 8080
또는
→ green container: host 8081
```

이 구조를 제대로 설명하려면 Nginx, Docker 네트워크, AWS 네트워크, DNS, HTTPS, 모니터링, CI/CD를 연결해서 이해해야 한다.

이 문서는 Nginx와 Docker가 traffic을 전환하는 인프라 구현에 집중한다. 전략 간 비교, resource trade-off와 rollback 정책은 [DevOps 배포 전략 비교](../devops/03-deployment-strategies.md)에서 다룬다.

## 1. Nginx 심화

## Nginx의 역할

Nginx는 클라이언트 요청을 먼저 받고, 뒤쪽 애플리케이션 서버나 컨테이너로 요청을 넘기는 리버스 프록시로 자주 사용된다.

```text
Client
→ Nginx
→ Backend
```

현재 blue/green 배포 구조에서는 Nginx가 active 컨테이너를 선택하는 진입점 역할을 한다.

```text
운영 중 blue active:
사용자 → Nginx → 127.0.0.1:8080

green 전환 후:
사용자 → Nginx → 127.0.0.1:8081
```

이때 Nginx는 로드밸런싱을 하는 것이 아니라, 설정된 upstream 또는 proxy_pass 대상에게 요청을 넘기는 트래픽 스위칭 역할을 한다.

## server block

`server` 블록은 어떤 포트와 도메인으로 들어온 요청을 처리할지 정한다.

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

의미:

```text
80번 포트로 들어온 요청을 받는다.
Host가 api.example.com인 요청을 처리한다.
모든 path 요청을 127.0.0.1:8080으로 넘긴다.
```

`server_name`은 HTTP 요청의 `Host` 헤더와 연결된다.

```http
Host: api.example.com
```

하나의 Nginx가 여러 도메인을 처리할 수 있는 이유도 `server_name`으로 요청을 나눌 수 있기 때문이다.

## location matching

`location`은 요청 path를 기준으로 어떤 설정 블록을 사용할지 고른다.

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

요청별 매칭:

```text
/health      → location = /health
/api/users   → location /api/
/api/orders  → location /api/
/about       → location /
/            → location /
```

자주 쓰는 location 형태:

```text
location /           prefix 매칭
location /api/       /api/로 시작하는 요청 매칭
location = /health   정확히 /health만 매칭
location ^~ /static/ 정규식 검사보다 prefix를 우선
location ~ \.jpg$    정규식 매칭
```

헬스체크는 보통 정확히 한 경로만 빠르게 응답하면 되므로 아래처럼 많이 둔다.

```nginx
location = /health {
    return 200 "ok";
}
```

## proxy_pass

`proxy_pass`는 Nginx가 받은 요청을 뒤쪽 서버로 넘기는 지시어다.

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
}
```

흐름:

```text
사용자 요청
→ Nginx
→ 127.0.0.1:8080 backend
```

blue/green 구조에서는 `proxy_pass` 대상이 active 컨테이너를 가리킨다.

```nginx
location / {
    proxy_pass http://127.0.0.1:8080; # blue
}
```

green으로 전환하면 다음처럼 바뀐다.

```nginx
location / {
    proxy_pass http://127.0.0.1:8081; # green
}
```

## proxy_pass trailing slash

Nginx에서 자주 헷갈리는 부분은 `proxy_pass` 뒤의 슬래시다.

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

이 차이 때문에 아래 같은 문제가 생길 수 있다.

```text
로컬에서는 /api/users 정상
Nginx 뒤에서는 404
백엔드 컨테이너는 살아 있음
Nginx도 요청을 받음
하지만 백엔드가 실제로 받은 path가 /users로 바뀜
```

따라서 API 서버가 `/api/users`를 기대하는지, `/users`를 기대하는지에 따라 `proxy_pass` 설정을 맞춰야 한다.

## upstream block

`upstream`은 백엔드 서버 묶음을 이름으로 정의하는 기능이다.

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

blue/green에서는 upstream만 바꿔도 active 컨테이너를 전환할 수 있다.

```nginx
upstream backend {
    server 127.0.0.1:8081;
}
```

여러 서버를 넣으면 로드밸런싱 성격이 생긴다.

```nginx
upstream backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
}
```

이 경우 Nginx는 두 서버로 요청을 나눠 보낼 수 있다.

단, 단일 blue/green 트래픽 스위칭은 보통 하나만 active로 둔다.

```text
blue 100%
green 0%
```

또는:

```text
blue 0%
green 100%
```

## nginx -t와 reload

Nginx 설정을 수정한 뒤에는 바로 reload하지 말고 먼저 문법 검사를 해야 한다.

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

blue/green 전환에서 중요한 이유:

```text
Nginx 설정 파일 수정
→ nginx -t로 문법 검사
→ 정상일 때만 reload
→ 새 요청이 green으로 이동
```

문법 검사를 하지 않고 잘못된 설정을 reload하면 전체 진입점이 깨질 수 있다.

## access.log와 error.log

Nginx 장애 분석에서 가장 먼저 볼 로그는 두 가지다.

```text
access.log: 어떤 요청이 들어왔고 어떤 응답을 줬는지 기록
error.log: upstream 연결 실패, timeout, 설정 문제 등 에러 기록
```

확인 명령어:

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

장애 상황별 확인:

```text
404
→ access.log에서 요청 path 확인
→ proxy_pass path rewrite 의심

502
→ error.log에서 upstream connection refused 확인
→ 컨테이너가 떠 있는지, 포트가 맞는지 확인

504
→ error.log에서 upstream timed out 확인
→ backend 응답 지연 또는 timeout 설정 확인
```

## timeout 설정

Nginx에는 upstream과 통신할 때 사용하는 timeout 설정이 있다.

```nginx
location / {
    proxy_connect_timeout 5s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    proxy_pass http://backend;
}
```

의미:

```text
proxy_connect_timeout
→ upstream 서버와 연결을 맺는 데 기다리는 시간

proxy_send_timeout
→ upstream으로 요청을 보내는 데 기다리는 시간

proxy_read_timeout
→ upstream 응답을 읽는 데 기다리는 시간
```

백엔드 API가 오래 걸리면 `proxy_read_timeout` 때문에 504가 날 수 있다.

하지만 timeout을 무작정 길게 늘리는 것은 좋은 해결책이 아니다.

```text
API가 왜 오래 걸리는지 확인
DB 쿼리 확인
외부 API 호출 확인
비동기 처리 고려
timeout은 서비스 특성에 맞게 조정
```

## X-Forwarded 헤더

Nginx 뒤의 백엔드는 실제 사용자가 아니라 Nginx로부터 요청을 받는다.

그래서 원래 클라이언트 정보를 헤더로 넘겨야 한다.

```nginx
location / {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

각 헤더 의미:

```text
Host
→ 원래 요청 도메인

X-Real-IP
→ Nginx가 본 클라이언트 IP

X-Forwarded-For
→ 프록시 체인을 거친 클라이언트 IP 목록

X-Forwarded-Proto
→ 원래 요청이 http였는지 https였는지
```

`X-Forwarded-Proto`가 없으면 백엔드가 HTTPS 요청을 HTTP로 오해할 수 있다.

그 결과:

```text
HTTPS 리다이렉트 반복
Secure Cookie 문제
OAuth callback URL 문제
백엔드가 http URL을 생성하는 문제
```

## 2. Docker 네트워크

## Docker 포트 구조

Docker에서 포트는 두 층으로 나뉜다.

```text
container port
host port
```

컨테이너 내부 애플리케이션이 8080에서 실행된다고 해도, 외부에서 접근하려면 호스트 포트에 매핑해야 한다.

```bash
docker run -p 8080:8080 backend
```

의미:

```text
host 8080
→ container 8080
```

형식:

```text
-p HOST_PORT:CONTAINER_PORT
```

## blue/green 포트 매핑

단일 EC2에서 blue/green 컨테이너를 동시에 띄우려면 host port를 다르게 둔다.

```bash
docker run -d --name backend-blue -p 8080:8080 backend:v1
docker run -d --name backend-green -p 8081:8080 backend:v2
```

구조:

```text
EC2 host 8080 → blue container 내부 8080
EC2 host 8081 → green container 내부 8080
```

컨테이너 내부에서는 둘 다 8080을 써도 된다.

하지만 호스트에서는 같은 포트를 동시에 사용할 수 없다.

불가능한 예:

```text
blue  → 0.0.0.0:8080
green → 0.0.0.0:8080
```

결과:

```text
address already in use
```

## localhost 차이

Docker에서 `localhost`는 위치에 따라 의미가 다르다.

EC2 호스트에서:

```text
localhost
→ EC2 자기 자신
```

컨테이너 내부에서:

```text
localhost
→ 컨테이너 자기 자신
```

따라서 컨테이너 안에서 `localhost:3306`으로 접근하면 EC2의 DB가 아니라 컨테이너 내부의 3306을 찾는다.

컨테이너가 호스트의 서비스에 접근해야 한다면 네트워크 구성을 따로 고려해야 한다.

## bridge network

Docker 기본 네트워크는 보통 bridge 방식이다.

```text
Docker bridge network
→ 컨테이너들이 가상 네트워크 안에서 IP를 받음
→ 포트 매핑을 통해 호스트와 연결
```

docker-compose를 쓰면 같은 compose 네트워크 안의 서비스끼리는 서비스 이름으로 접근할 수 있다.

```yaml
services:
  backend:
    image: backend

  redis:
    image: redis
```

backend에서 redis 접근:

```text
redis:6379
```

이건 Docker DNS가 서비스 이름을 컨테이너 IP로 해석해주기 때문이다.

## Nginx와 Docker 연결

단일 EC2에서 Nginx가 호스트에 설치되어 있고, backend가 Docker 컨테이너라면 Nginx는 host port로 접근한다.

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
}
```

이 요청 흐름:

```text
Nginx
→ EC2 host 8080
→ Docker port mapping
→ blue container 내부 8080
```

green 전환:

```nginx
location / {
    proxy_pass http://127.0.0.1:8081;
}
```

## 3. AWS VPC / Security Group / ALB

## VPC

VPC는 AWS 안에서 만드는 가상 네트워크다.

예:

```text
VPC CIDR: 10.0.0.0/16
```

이 안에 여러 subnet을 만든다.

```text
public subnet: 10.0.1.0/24
private subnet: 10.0.2.0/24
```

VPC는 집이나 회사 내부망을 AWS 안에 만든 것처럼 생각하면 된다.

## Public Subnet과 Private Subnet

Public Subnet은 Internet Gateway로 나가는 route가 있는 subnet이다.

```text
0.0.0.0/0 → Internet Gateway
```

Private Subnet은 인터넷으로 직접 나가는 route가 없는 subnet이다.

운영 구조 예:

```text
ALB → Public Subnet
EC2 App Server → Private Subnet
RDS → Private Subnet
```

처음에는 EC2를 public subnet에 둘 수 있다.

하지만 보안을 강화하면 ALB만 public subnet에 두고, EC2는 private subnet에 두는 구조를 많이 쓴다.

## Route Table

Route Table은 subnet의 트래픽을 어디로 보낼지 정한다.

예:

```text
10.0.0.0/16 → local
0.0.0.0/0  → Internet Gateway
```

의미:

```text
VPC 내부 대역은 local로 통신
그 외 인터넷 목적지는 Internet Gateway로 보냄
```

private subnet이 외부로 나가야 할 때는 NAT Gateway를 사용한다.

```text
Private Subnet
→ NAT Gateway
→ Internet Gateway
→ Internet
```

## Security Group

Security Group은 AWS 리소스 단위 방화벽이다.

EC2에 붙일 수도 있고 ALB에 붙일 수도 있다.

예:

```text
ALB Security Group
- inbound 80 from 0.0.0.0/0
- inbound 443 from 0.0.0.0/0

EC2 Security Group
- inbound 80 from ALB Security Group
- inbound 22 from 내 IP
```

이렇게 하면 사용자는 ALB로만 접근하고, EC2는 ALB에서 오는 HTTP 요청만 받도록 제한할 수 있다.

Security Group은 stateful이다.

```text
들어온 요청에 대한 응답 트래픽은 자동 허용
```

NACL은 subnet 단위이고 stateless라서 inbound/outbound를 더 명시적으로 봐야 한다.

## ALB와 Target Group

ALB는 Application Load Balancer다.

HTTP/HTTPS 레벨에서 요청을 처리하는 L7 로드밸런서다.

```text
사용자
→ ALB
→ Target Group
→ EC2
```

ALB 구성 요소:

```text
Listener
→ 80 또는 443 포트에서 요청 수신

Rule
→ Host, Path 조건으로 라우팅

Target Group
→ 트래픽을 보낼 대상 묶음

Health Check
→ 대상이 정상인지 확인
```

예:

```text
ALB Listener 443
→ /api/* 요청은 api-target-group
→ /admin/* 요청은 admin-target-group
```

Target Group health check가 실패하면 ALB는 해당 target으로 트래픽을 보내지 않는다.

## 4. DNS / Route 53

## DNS 흐름

사용자는 IP보다 도메인으로 서비스에 접속한다.

```text
https://api.example.com
```

브라우저는 먼저 DNS를 통해 IP 또는 ALB 주소를 찾는다.

```text
api.example.com
→ DNS 조회
→ ALB DNS Name 또는 IP
```

## Route 53

Route 53은 AWS의 관리형 DNS 서비스다.

도메인을 관리하려면 Hosted Zone을 만든다.

```text
example.com Hosted Zone
```

그 안에 레코드를 만든다.

```text
api.example.com
www.example.com
```

## A, CNAME, Alias

A Record:

```text
도메인 → IPv4 주소
```

CNAME:

```text
도메인 → 다른 도메인 이름
```

Alias Record:

```text
도메인 → AWS 리소스
```

ALB에 연결할 때는 Route 53 Alias Record를 자주 쓴다.

```text
api.example.com
→ Alias
→ my-alb-123.ap-northeast-2.elb.amazonaws.com
```

ALB는 IP가 바뀔 수 있으므로 직접 IP를 박는 것보다 ALB DNS Name이나 Alias를 쓰는 것이 맞다.

## TTL

TTL은 DNS 응답을 얼마나 캐싱할지 정하는 값이다.

```text
TTL 300
→ 300초 동안 DNS 응답 캐싱
```

DNS를 바꿨는데 바로 반영되지 않는 이유가 TTL과 캐시 때문이다.

## 5. HTTPS / TLS

## HTTPS와 TLS

HTTPS는 HTTP에 TLS 암호화가 붙은 것이다.

```text
HTTP + TLS = HTTPS
```

TLS는 통신 내용을 암호화하고, 서버가 신뢰할 수 있는 서버인지 인증서로 확인한다.

## 인증서와 CA

브라우저는 서버 인증서를 확인한다.

```text
서버 인증서
→ 중간 인증서
→ 루트 CA
```

CA는 인증서를 발급하는 신뢰 기관이다.

AWS에서는 ACM으로 인증서를 발급받아 ALB나 CloudFront에 연결할 수 있다.

## TLS termination

TLS termination은 HTTPS 연결을 특정 지점에서 끝내는 것이다.

ALB에서 TLS 종료:

```text
사용자
→ HTTPS
→ ALB
→ HTTP
→ EC2 / Nginx
→ Backend
```

Nginx에서 TLS 종료:

```text
사용자
→ HTTPS
→ Nginx
→ HTTP
→ Backend
```

둘 중 어디서 종료할지는 구조에 따라 다르다.

ALB를 쓰면 인증서 관리를 ACM과 ALB에서 처리할 수 있어 운영이 편해진다.

## X-Forwarded-Proto

ALB나 Nginx에서 TLS를 종료하고 백엔드로 HTTP로 넘기면, 백엔드는 자기에게 HTTP 요청이 왔다고 생각할 수 있다.

하지만 원래 사용자는 HTTPS로 접속했다.

이 정보를 전달하는 헤더가 `X-Forwarded-Proto`다.

```text
X-Forwarded-Proto: https
```

이 헤더를 제대로 처리하지 않으면:

```text
HTTP to HTTPS redirect 반복
Secure Cookie 문제
OAuth redirect_uri 문제
백엔드가 http URL 생성
```

## 6. Monitoring / Logging

## 메트릭과 로그

메트릭은 숫자로 보는 상태다.

```text
CPU 사용률
메모리 사용률
응답 시간
5xx 에러율
요청 수
```

로그는 실제 이벤트 기록이다.

```text
요청 path
응답 status
에러 메시지
stack trace
upstream timeout
```

장애 분석에서는 둘 다 필요하다.

## Nginx 로그

Nginx access log:

```text
누가 어떤 path로 요청했는가
응답 status code가 무엇인가
응답 시간이 얼마나 걸렸는가
```

Nginx error log:

```text
upstream connection refused
upstream timed out
permission denied
설정 문제
```

명령어:

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Docker logs

컨테이너 애플리케이션 로그는 `docker logs`로 확인한다.

```bash
docker logs backend-blue
docker logs backend-green
```

장애 흐름:

```text
Nginx 502
→ Nginx error.log 확인
→ upstream 포트 확인
→ docker ps 확인
→ docker logs 확인
```

## CloudWatch

AWS에서는 CloudWatch로 메트릭과 로그를 볼 수 있다.

```text
CloudWatch Metrics
→ CPU, 네트워크, ALB 5xx, Target Response Time

CloudWatch Logs
→ 애플리케이션 로그, 시스템 로그

CloudWatch Alarm
→ 특정 지표가 임계치를 넘으면 알림
```

예:

```text
ALB 5xx 에러율 증가
Target Response Time 증가
EC2 CPU 90% 이상
Disk 사용량 증가
```

## 7. CI/CD 배포 자동화

## CI와 CD

CI는 코드를 자주 통합하고 검증하는 과정이다.

```text
build
test
lint
```

CD는 검증된 코드를 배포하는 과정이다.

```text
image build
image push
server deploy
health check
rollback
```

## GitHub Actions 흐름

blue/green 배포 자동화 흐름:

```text
git push
→ GitHub Actions 실행
→ 테스트
→ Docker image build
→ ECR 또는 registry push
→ EC2 접속
→ inactive 컨테이너 실행
→ health check
→ Nginx upstream 전환
→ nginx -t
→ nginx reload
→ old 컨테이너 graceful stop
```

핵심은 새 컨테이너를 먼저 띄우고 검증한 뒤 트래픽을 넘기는 것이다.

```text
old active 유지
new inactive 실행
new health check 통과
traffic switch
old stop
```

## Secrets

CI/CD에서 민감한 값은 코드에 넣으면 안 된다.

```text
SSH private key
AWS access key
DB password
Docker registry token
```

GitHub Actions에서는 Secrets나 OIDC를 사용한다.

가능하면 장기 Access Key보다 OIDC 기반 Role Assume 구조가 더 안전하다.

## Rollback

자동 배포에는 rollback 흐름이 있어야 한다.

예:

```text
green 배포
health check 실패
→ Nginx 전환하지 않음
→ green 제거
→ blue 유지
```

전환 후 문제가 생긴 경우:

```text
Nginx upstream을 이전 포트로 되돌림
nginx -t
nginx reload
```

## 8. Kubernetes Service / Ingress

## Pod

Pod는 Kubernetes에서 컨테이너를 실행하는 최소 단위다.

Pod는 언제든 새로 만들어지고 사라질 수 있다.

그래서 Pod IP는 안정적인 주소로 보면 안 된다.

## Service

Service는 변하는 Pod들을 안정적으로 묶어주는 네트워크 진입점이다.

```text
Service
→ Pod A
→ Pod B
→ Pod C
```

대표 타입:

```text
ClusterIP
→ 클러스터 내부에서만 접근

NodePort
→ 각 노드의 특정 포트로 노출

LoadBalancer
→ 클라우드 로드밸런서와 연결
```

## Ingress

Ingress는 HTTP/HTTPS 요청을 어느 Service로 보낼지 정하는 규칙이다.

중요한 점:

```text
Ingress = 규칙
Ingress Controller = 실제 리버스 프록시
```

흐름:

```text
사용자
→ Ingress Controller
→ Service
→ Pod
```

예:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
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

## readinessProbe

readinessProbe는 Pod가 트래픽을 받을 준비가 되었는지 판단한다.

준비되지 않은 Pod에는 Service가 트래픽을 보내지 않는다.

이것은 무중단 배포와 직접 관련이 있다.

```text
새 Pod 생성
→ readinessProbe 실패 중
→ 트래픽 안 받음
→ readinessProbe 성공
→ Service가 트래픽 전달
```

## 최종 정리

```text
Nginx는 요청을 받고 active 컨테이너로 넘기는 리버스 프록시다.
Docker 네트워크는 컨테이너 내부 포트와 호스트 포트의 차이를 이해해야 한다.
AWS VPC와 ALB는 단일 EC2 구조를 운영형 클라우드 구조로 확장하는 기반이다.
DNS와 Route 53은 도메인을 ALB나 서버로 연결한다.
HTTPS/TLS는 운영 서비스에서 필수이며 TLS 종료 위치가 중요하다.
Monitoring/Logging은 장애 원인 분석을 가능하게 한다.
CI/CD는 blue/green 배포를 반복 가능하고 안전하게 자동화한다.
Kubernetes Service/Ingress는 컨테이너 운영을 클러스터 단위로 확장하는 핵심이다.
```
