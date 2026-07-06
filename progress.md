# 현재 정리 상태와 다음 학습 순서

## 기준

현재 전체 로드맵은 [list.md](list.md)에 정리되어 있다.

`list.md`는 네트워크 기본부터 클라우드 운영까지 전체 공부 범위를 잡아둔 파일이고, `logs/` 아래 파일들은 실제로 자세히 정리한 학습 로그다.

현재 작성된 상세 로그는 다음 3개다.

```text
logs/2026-07-03-network-basics-01.md
logs/2026-07-03-proxy-routing.md
logs/2026-07-04-proxy-routing-study-plan.md
```

## 현재 자세히 정리된 부분

### 1. 네트워크 기본

관련 파일:

```text
logs/2026-07-03-network-basics-01.md
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
세부 주제인 주소 체계, TCP, DNS, HTTP는 별도 심화 정리 필요
```

## 2. 프록시 기본

관련 파일:

```text
logs/2026-07-03-proxy-routing.md
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
프록시 헤더, 캐싱, 인증, 보안 쪽은 추가 정리 필요
```

## 3. 리버스 프록시

관련 파일:

```text
logs/2026-07-03-proxy-routing.md
logs/2026-07-04-proxy-routing-study-plan.md
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
Nginx 설정 세부 문법은 계속 보강 필요
```

## 4. 라우팅

관련 파일:

```text
logs/2026-07-03-proxy-routing.md
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
logs/2026-07-03-proxy-routing.md
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
L4/L7, Round Robin, Least Connections, Sticky Session, Connection Draining은 추가 정리 필요
```

## 6. Nginx 심화 일부

관련 파일:

```text
logs/2026-07-04-proxy-routing-study-plan.md
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
실제 설정 예시, timeout, 로그, TLS, rate limit은 추가 정리 필요
```

## 7. 장애 분석 일부

관련 파일:

```text
logs/2026-07-04-proxy-routing-study-plan.md
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
프록시 계층의 5xx 장애는 일부 정리됨
DNS failure, connection refused, timeout, TLS 오류, CORS 오류는 추가 정리 필요
```

## 8. 배포와 무중단 일부

관련 파일:

```text
logs/2026-07-04-proxy-routing-study-plan.md
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
Rolling, Canary, Connection Draining, DB migration 호환성은 추가 정리 필요
```

## 아직 상세 정리가 필요한 부분

### 네트워크 심화

```text
2. 주소 체계
3. 포트와 소켓
4. TCP / UDP
5. DNS
6. HTTP
7. HTTPS / TLS
```

### 프록시 / Nginx / 장애 분석 심화

```text
10. 프록시 헤더
12. 로드밸런싱 심화
13. Nginx 심화 보강
14. 장애 분석 보강
15. 배포와 무중단 보강
```

### 컨테이너 / Kubernetes

```text
16. Docker 네트워크
17. Kubernetes 네트워크
26. Container Platform
27. API Gateway
28. Service Mesh
```

### 클라우드

```text
18. 클라우드 네트워크
19. IAM
20. Compute
21. Storage
22. Database
23. Monitoring / Logging
24. CI/CD
25. IaC
29. 보안
30. 비용
31. 실습 명령어
```

## 다음에 이어서 공부하면 좋은 순서

현재까지 프록시와 blue/green 배포 흐름을 많이 다뤘기 때문에, 바로 이어서 공부하기 좋은 순서는 다음과 같다.

```text
1. Nginx 심화 보강
2. Docker 네트워크
3. AWS VPC / Security Group / ALB
4. DNS / Route 53
5. HTTPS / TLS
6. CI/CD와 배포 자동화
7. Monitoring / Logging
8. Kubernetes Service / Ingress
```

## 가장 우선순위 높은 다음 주제

### 1순위: Nginx 심화 보강

공부할 내용:

```text
server block
location 우선순위
proxy_pass trailing slash
upstream block
nginx -t
nginx reload
access.log
error.log
proxy_connect_timeout
proxy_read_timeout
client_max_body_size
HTTP to HTTPS redirect
```

이유:

```text
현재 blue/green 배포 구조와 직접 연결된다.
Nginx가 active 컨테이너로 요청을 넘기는 핵심 역할을 한다.
배포 후 404, 502, 504 같은 문제를 분석하려면 Nginx 설정을 읽을 수 있어야 한다.
```

### 2순위: Docker 네트워크

공부할 내용:

```text
container port
host port
docker run -p
bridge network
container name resolution
docker-compose network
blue/green 컨테이너 포트 매핑
```

이유:

```text
단일 EC2에서 컨테이너 두 개를 띄우는 blue/green 구조와 바로 연결된다.
컨테이너 내부 포트와 호스트 포트를 구분해야 배포 구조가 명확해진다.
```

### 3순위: AWS VPC / Security Group / ALB

공부할 내용:

```text
VPC
Subnet
Public Subnet
Private Subnet
Route Table
Internet Gateway
Security Group
ALB
Target Group
Health Check
```

이유:

```text
EC2 하나에서 직접 Nginx로 받는 구조에서,
ALB와 Target Group을 두는 구조로 확장할 수 있다.
클라우드 네트워크를 이해하면 배포 구조를 더 안전하고 확장 가능하게 만들 수 있다.
```

## 현재 상태 한 줄 정리

```text
네트워크 큰그림과 프록시/라우팅/단일 EC2 blue-green 배포 개념은 정리됐고,
다음은 Nginx 세부 설정, Docker 네트워크, AWS VPC/ALB 쪽으로 이어가면 된다.
```
