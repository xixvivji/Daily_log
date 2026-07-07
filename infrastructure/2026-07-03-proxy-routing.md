# 2026-07-03 프록시와 라우팅: Forward Proxy, Reverse Proxy, Ingress

## 핵심 질문

프록시와 라우팅 개념을 정확히 구분한다.

- 프록시가 무엇인지 설명할 수 있다.
- Forward Proxy와 Reverse Proxy의 차이를 설명할 수 있다.
- 라우팅이 무엇인지 네트워크 라우팅과 HTTP 라우팅으로 나눠 설명할 수 있다.
- Nginx가 리버스 프록시로 동작하는 방식을 이해한다.
- Kubernetes Ingress와 Ingress Controller의 차이를 설명할 수 있다.
- 로드밸런서, API Gateway, Service Mesh와 리버스 프록시의 관계를 이해한다.

## 1. 프록시란 무엇인가?

프록시(proxy)는 중간에서 대신 요청하거나 대신 응답을 전달하는 서버 또는 구성요소다.

`proxy`라는 말 자체가 대리인, 중개자라는 뜻에 가깝다.

기본 구조:

```text
클라이언트 → 프록시 → 서버
```

클라이언트가 서버에 직접 요청하지 않고, 중간의 프록시를 거쳐 요청한다.

프록시가 하는 일은 상황에 따라 다르다.

```text
요청 전달
응답 전달
접근 제어
인증 처리
캐싱
압축
TLS 종료
로드밸런싱
로그 수집
보안 필터링
라우팅
```

프록시는 크게 두 종류로 많이 나눈다.

```text
Forward Proxy: 클라이언트 앞에 있는 프록시
Reverse Proxy: 서버 앞에 있는 프록시
```

## 2. Forward Proxy란?

Forward Proxy는 클라이언트 쪽을 대신해서 외부 서버에 요청을 보내는 프록시다.

흐름:

```text
클라이언트 → Forward Proxy → 인터넷 서버
```

예를 들어 회사 내부망에서 직원 PC가 인터넷에 직접 나가지 못하고 회사 프록시 서버를 거쳐야 하는 구조가 있다.

```text
직원 PC
→ 회사 Forward Proxy
→ google.com
```

이 경우 서버 입장에서는 실제 직원 PC가 아니라 회사 프록시가 요청한 것처럼 보일 수 있다.

Forward Proxy의 목적:

```text
클라이언트의 외부 접속 통제
특정 사이트 차단
접속 로그 기록
캐싱
클라이언트 IP 숨김
보안 검사
내부망에서 외부망으로 나가는 트래픽 관리
```

예시:

```text
회사 인터넷 프록시
학교/기관 웹 필터링 프록시
VPN 일부 구조
브라우저에 직접 설정하는 HTTP 프록시
개발 환경에서 사용하는 로컬 프록시
```

Forward Proxy에서 중요한 관점:

```text
프록시가 클라이언트를 대신한다.
서버는 클라이언트보다 프록시를 먼저 본다.
주 관심사는 클라이언트 보호, 통제, 익명화, 외부 접속 관리다.
```

정리:

```text
Forward Proxy는 클라이언트가 외부 서버에 나갈 때 중간에서 대신 요청해 주는 프록시다.
```

## 3. Reverse Proxy란?

Reverse Proxy는 서버 앞에 서서 클라이언트 요청을 대신 받고, 뒤쪽의 실제 서버로 전달하는 프록시다.

흐름:

```text
클라이언트 → Reverse Proxy → 실제 서버
```

예를 들어 사용자가 `https://example.com`으로 접속한다고 하자.

```text
사용자 브라우저
→ Nginx Reverse Proxy
→ Backend App Server
```

사용자는 뒤쪽에 실제 서버가 몇 대 있는지 모른다. 사용자는 그냥 `example.com`에 요청한다고 생각한다.

Reverse Proxy의 목적:

```text
서버 숨김
로드밸런싱
TLS 종료
HTTP 라우팅
정적 파일 서빙
압축
캐싱
인증 처리
Rate Limit
WAF 연동
로그 수집
무중단 배포 보조
```

대표 예시:

```text
Nginx
Apache HTTP Server
HAProxy
Traefik
Envoy
Kong
AWS ALB
Cloudflare
Kubernetes Ingress Controller
```

Reverse Proxy에서 중요한 관점:

```text
프록시가 서버를 대신한다.
클라이언트는 실제 서버가 아니라 프록시에 접속한다.
주 관심사는 서버 보호, 요청 분배, HTTP 라우팅, TLS 처리다.
```

정리:

```text
Reverse Proxy는 서버 앞에서 클라이언트 요청을 받아 뒤쪽 서버로 전달하는 프록시다.
```

## 4. Forward Proxy와 Reverse Proxy 차이

둘 다 중간에서 요청을 전달하지만, 어느 쪽을 대신하느냐가 다르다.

```text
Forward Proxy = 클라이언트 편
Reverse Proxy = 서버 편
```

비교:

```text
Forward Proxy
- 클라이언트 앞에 있음
- 클라이언트가 외부로 나갈 때 사용
- 서버 입장에서는 프록시가 요청자처럼 보일 수 있음
- 목적: 접속 통제, 익명화, 캐싱, 보안 검사

Reverse Proxy
- 서버 앞에 있음
- 외부 요청이 내부 서버로 들어올 때 사용
- 클라이언트 입장에서는 프록시가 실제 서버처럼 보임
- 목적: 로드밸런싱, TLS 종료, 라우팅, 서버 보호
```

그림으로 보면 다음과 같다.

```text
Forward Proxy

클라이언트들 → Forward Proxy → 인터넷 서버들

Reverse Proxy

클라이언트들 → Reverse Proxy → 내부 서버들
```

예시로 구분:

```text
회사 PC가 회사 프록시를 통해 외부 사이트 접속
→ Forward Proxy

사용자가 Nginx를 통해 내부 WAS에 접속
→ Reverse Proxy

Kubernetes에서 Ingress Controller가 요청을 Pod로 전달
→ Reverse Proxy

브라우저에 HTTP 프록시 서버 주소를 직접 설정
→ Forward Proxy
```

## 5. 라우팅이란?

라우팅(routing)은 요청이나 패킷을 어디로 보낼지 결정하는 과정이다.

라우팅은 여러 계층에서 쓰이는 말이다.

```text
네트워크 라우팅: IP 패킷을 어느 네트워크로 보낼지 결정
HTTP 라우팅: HTTP 요청을 어느 애플리케이션 서버로 보낼지 결정
애플리케이션 라우팅: URL path를 어느 핸들러 함수로 보낼지 결정
```

같은 단어지만 계층이 다르다.

## 6. 네트워크 라우팅

네트워크 라우팅은 IP 패킷을 목적지 네트워크까지 보내는 과정이다.

예:

```text
내 PC: 192.168.0.10
목적지: 8.8.8.8
게이트웨이: 192.168.0.1
```

내 PC는 `8.8.8.8`이 같은 네트워크에 없다고 판단한다.

그래서 기본 게이트웨이로 보낸다.

```text
내 PC
→ 공유기
→ ISP 라우터
→ 여러 인터넷 라우터
→ 8.8.8.8
```

라우터는 라우팅 테이블을 보고 다음 hop을 결정한다.

라우팅 테이블 예시:

```text
192.168.0.0/24 → local network
10.0.0.0/8 → vpn0
0.0.0.0/0 → default gateway
```

핵심:

```text
네트워크 라우팅은 IP 주소와 네트워크 대역을 기준으로 다음 경로를 결정한다.
```

## 7. HTTP 라우팅

HTTP 라우팅은 HTTP 요청의 `Host`, `Path`, `Header`, `Method` 등을 보고 어느 서버로 보낼지 결정하는 것이다.

예:

```text
api.example.com/users → user-api 서버
api.example.com/orders → order-api 서버
www.example.com → frontend 서버
admin.example.com → admin 서버
```

이런 라우팅은 리버스 프록시가 많이 담당한다.

Nginx 예시:

```nginx
server {
    listen 80;
    server_name example.com;

    location /api/ {
        proxy_pass http://backend:8080;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
```

위 설정의 의미:

```text
example.com/api/ 로 시작하는 요청 → backend:8080
그 외 요청 → frontend:3000
```

Host 기반 라우팅 예시:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://api-server:8080;
    }
}

server {
    listen 80;
    server_name admin.example.com;

    location / {
        proxy_pass http://admin-server:8080;
    }
}
```

핵심:

```text
HTTP 라우팅은 HTTP 요청 정보를 보고 뒤쪽의 어느 서비스로 보낼지 결정한다.
```

## 8. Nginx는 리버스 프록시인가?

Nginx는 웹 서버이면서 리버스 프록시로도 많이 쓰인다.

Nginx가 할 수 있는 일:

```text
정적 파일 서빙
리버스 프록시
로드밸런싱
TLS 종료
압축
캐싱
Rate Limit
접속 로그 기록
```

가장 흔한 구조:

```text
사용자
→ Nginx
→ Spring Boot / Node.js / Django / Rails 같은 백엔드 서버
```

Nginx 리버스 프록시 예:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

설명:

```text
사용자는 api.example.com:80으로 접속한다.
Nginx는 요청을 127.0.0.1:8080으로 넘긴다.
백엔드 서버는 직접 인터넷에 노출되지 않아도 된다.
X-Forwarded-For 같은 헤더로 원래 클라이언트 IP 정보를 전달할 수 있다.
```

## 9. 왜 백엔드 앞에 Nginx를 둘까?

백엔드 서버를 직접 인터넷에 노출하지 않고 Nginx를 앞에 두는 이유는 많다.

```text
TLS 인증서를 Nginx에서 관리하기 위해
80/443 포트 진입점을 하나로 통일하기 위해
여러 백엔드로 요청을 나누기 위해
정적 파일은 Nginx가 빠르게 처리하기 위해
접속 로그를 한 곳에서 남기기 위해
Rate Limit 같은 보호 기능을 넣기 위해
무중단 배포를 쉽게 하기 위해
```

예:

```text
/api/ → backend:8080
/admin/ → admin:8081
/static/ → Nginx가 직접 파일 서빙
/ → frontend:3000
```

이런 구성이 가능하다.

## 10. 로드밸런싱과 리버스 프록시

로드밸런싱은 요청을 여러 서버에 나누어 보내는 것이다.

```text
사용자들
→ 리버스 프록시 / 로드밸런서
→ app1, app2, app3
```

Nginx 예시:

```nginx
upstream backend_pool {
    server app1:8080;
    server app2:8080;
    server app3:8080;
}

server {
    listen 80;

    location / {
        proxy_pass http://backend_pool;
    }
}
```

이 경우 Nginx가 요청을 `app1`, `app2`, `app3`으로 나누어 보낸다.

로드밸런싱 알고리즘 예:

```text
Round Robin: 순서대로 분배
Least Connections: 연결 수가 적은 서버로 분배
IP Hash: 클라이언트 IP 기준으로 같은 서버에 보내기
Weighted: 서버마다 가중치를 다르게 주기
```

정리:

```text
리버스 프록시는 서버 앞에서 요청을 받는 역할이고, 로드밸런싱은 그 요청을 여러 서버에 분배하는 기능이다.
```

## 11. TLS 종료란?

TLS 종료(TLS termination)는 HTTPS 암호화 연결을 리버스 프록시에서 끝내는 것이다.

흐름:

```text
브라우저
→ HTTPS
→ Nginx
→ HTTP 또는 HTTPS
→ 백엔드 서버
```

Nginx가 인증서를 가지고 있고, 클라이언트와의 HTTPS 연결을 처리한다.

그 뒤 내부 백엔드로는 HTTP로 넘길 수도 있고 HTTPS로 다시 넘길 수도 있다.

장점:

```text
인증서 관리를 한 곳에서 할 수 있다.
백엔드 서버는 HTTP 애플리케이션 로직에 집중할 수 있다.
TLS 설정을 중앙에서 통제할 수 있다.
여러 백엔드가 같은 인증서 정책을 사용할 수 있다.
```

주의:

```text
프록시 뒤쪽 내부망도 안전하지 않다면 백엔드까지 HTTPS를 유지해야 한다.
클라우드나 Kubernetes 환경에서는 어디서 TLS를 종료할지 설계가 중요하다.
```

## 12. Kubernetes Ingress란?

Kubernetes Ingress는 외부 HTTP/HTTPS 요청을 클러스터 내부 Service로 보내기 위한 규칙이다.

중요:

```text
Ingress 자체는 실제 프록시가 아니다.
Ingress는 라우팅 규칙이다.
실제로 트래픽을 받는 것은 Ingress Controller다.
```

구조:

```text
사용자
→ LoadBalancer
→ Ingress Controller
→ Kubernetes Service
→ Pod
```

Ingress 예시:

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
api.example.com으로 들어온 HTTP 요청을 api-service의 8080 포트로 보내라.
```

여기서 `api-service`는 Pod로 직접 가리키는 게 아니라 Service다.

Service가 다시 실제 Pod들로 트래픽을 보낸다.

```text
Ingress Controller
→ Service
→ Pod A / Pod B / Pod C
```

## 13. Ingress Controller란?

Ingress Controller는 Ingress 규칙을 읽고 실제로 요청을 처리하는 리버스 프록시다.

대표 Ingress Controller:

```text
NGINX Ingress Controller
Traefik
HAProxy Ingress
Kong Ingress Controller
AWS Load Balancer Controller
Istio Ingress Gateway
```

예를 들어 NGINX Ingress Controller를 설치하면, 컨트롤러가 Kubernetes API에서 Ingress 리소스를 감시한다.

```text
Ingress 리소스 생성
→ NGINX Ingress Controller가 감지
→ Nginx 설정을 내부적으로 생성/반영
→ 외부 요청을 Service로 프록시
```

정확한 표현:

```text
Ingress = 라우팅 규칙
Ingress Controller = 실제 리버스 프록시
```

## 14. Kubernetes Service와 Ingress 차이

Kubernetes에서 Service와 Ingress는 역할이 다르다.

Service:

```text
Pod들을 안정적으로 묶어주는 내부 진입점
Pod IP가 바뀌어도 고정된 이름과 IP를 제공
L4 수준의 로드밸런싱
ClusterIP, NodePort, LoadBalancer 타입이 있음
```

Ingress:

```text
HTTP/HTTPS 외부 진입 규칙
Host와 Path 기반 라우팅
TLS 설정 가능
여러 Service를 하나의 외부 진입점으로 묶을 수 있음
```

구조:

```text
외부 사용자
→ Ingress Controller
→ Service
→ Pod
```

예:

```text
api.example.com/users → user-service → user Pod들
api.example.com/orders → order-service → order Pod들
www.example.com → frontend-service → frontend Pod들
```

## 15. API Gateway와 리버스 프록시

API Gateway도 리버스 프록시의 확장된 형태로 볼 수 있다.

리버스 프록시가 주로 요청 전달, 라우팅, TLS, 로드밸런싱을 담당한다면, API Gateway는 API 운영에 필요한 기능을 더 많이 가진다.

API Gateway 기능:

```text
인증/인가
API Key 관리
JWT 검증
Rate Limit
요청/응답 변환
버전 라우팅
사용량 측정
쿼터 관리
서비스 디스커버리
```

예:

```text
클라이언트
→ API Gateway
→ user-service / order-service / payment-service
```

대표 제품:

```text
Kong
AWS API Gateway
Apigee
Tyk
KrakenD
Spring Cloud Gateway
```

정리:

```text
API Gateway는 API 중심 기능이 강화된 리버스 프록시라고 이해하면 쉽다.
```

## 16. Service Mesh와 리버스 프록시

Service Mesh는 서비스 간 통신을 관리하는 인프라 계층이다.

대표적으로 Istio, Linkerd, Consul Connect가 있다.

Service Mesh에서는 각 서비스 옆에 사이드카 프록시가 붙는 구조가 많다.

```text
service-a
→ sidecar proxy
→ sidecar proxy
→ service-b
```

Istio에서는 Envoy가 사이드카 프록시로 많이 쓰인다.

Service Mesh가 제공하는 기능:

```text
서비스 간 mTLS
트래픽 분할
카나리 배포
재시도
타임아웃
서킷 브레이커
관측성
정책 적용
```

정리:

```text
Ingress는 외부에서 내부로 들어오는 트래픽을 다루는 경우가 많고,
Service Mesh는 내부 서비스 간 트래픽까지 세밀하게 다루는 경우가 많다.
```

## 17. 자주 헷갈리는 표현 정리

### 프론트 프록시?

보통 정확한 용어는 Forward Proxy다.

가끔 클라이언트 앞에 있다는 의미로 front proxy라고 말하는 사람이 있을 수 있지만, 일반적으로 네트워크에서 표준적으로 많이 쓰는 표현은 Forward Proxy다.

```text
Forward Proxy = 클라이언트 앞
Reverse Proxy = 서버 앞
```

### Nginx는 웹 서버인가 프록시인가?

둘 다 가능하다.

```text
정적 파일을 직접 응답하면 웹 서버
뒤쪽 서버로 요청을 넘기면 리버스 프록시
여러 서버로 나누어 보내면 로드밸런서 역할
```

### Ingress는 리버스 프록시인가?

정확히는 아니다.

```text
Ingress = Kubernetes 리소스, 라우팅 규칙
Ingress Controller = 실제 리버스 프록시
```

다만 실무 대화에서는 "Ingress가 요청을 라우팅한다"라고 말하는 경우가 많다. 이때 실제 동작 주체는 Ingress Controller라고 이해하면 된다.

### Load Balancer와 Reverse Proxy는 같은가?

완전히 같은 말은 아니다.

```text
Reverse Proxy = 서버 앞에서 요청을 대신 받아 뒤로 넘김
Load Balancer = 요청을 여러 서버로 분산
```

하지만 많은 제품이 둘 다 한다.

```text
Nginx: Reverse Proxy + Load Balancer
HAProxy: Reverse Proxy + Load Balancer
AWS ALB: Reverse Proxy 성격 + Load Balancer
```

## 18. 전체 흐름 예시

사용자가 Kubernetes에 배포된 웹 서비스를 호출한다고 가정한다.

```text
사용자 브라우저
→ DNS 조회
→ Cloudflare
→ AWS ALB
→ NGINX Ingress Controller
→ Kubernetes Service
→ Pod
```

각 단계 역할:

```text
DNS: 도메인을 IP로 변환
Cloudflare: CDN, WAF, TLS, 캐싱, 프록시
AWS ALB: 외부 로드밸런서
NGINX Ingress Controller: Host/Path 기반 리버스 프록시
Service: Pod 그룹에 대한 안정적인 내부 진입점
Pod: 실제 애플리케이션 실행
```

예:

```text
https://api.example.com/users/1
```

흐름:

```text
1. 브라우저가 api.example.com의 IP를 DNS로 조회
2. 사용자가 HTTPS 요청 전송
3. 외부 로드밸런서가 클러스터 진입점으로 전달
4. Ingress Controller가 Host와 Path를 확인
5. api-service로 프록시
6. api-service가 실제 Pod 중 하나로 전달
7. Pod가 응답 생성
8. 응답이 반대 방향으로 돌아감
```

## 19. 장애가 났을 때 확인 순서

리버스 프록시/Ingress 구조에서 접속이 안 되면 계층별로 확인한다.

```text
1. DNS가 맞는 IP를 가리키는가?
2. 외부 로드밸런서가 살아 있는가?
3. 80/443 포트가 열려 있는가?
4. TLS 인증서가 정상인가?
5. Ingress 규칙의 host/path가 맞는가?
6. Ingress Controller가 정상 동작 중인가?
7. Service 이름과 포트가 맞는가?
8. Service endpoint에 Pod가 붙어 있는가?
9. Pod가 Ready 상태인가?
10. 애플리케이션이 정상 응답하는가?
```

Kubernetes에서 자주 쓰는 확인 명령어:

```bash
kubectl get ingress
kubectl describe ingress app-ingress
kubectl get svc
kubectl describe svc api-service
kubectl get endpoints api-service
kubectl get pods
kubectl logs deploy/api
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller
```

일반 서버/Nginx에서 확인:

```bash
curl -v https://api.example.com
curl -I https://api.example.com
nc -vz api.example.com 443
nginx -t
systemctl status nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## 20. 핵심 요약

```text
프록시 = 중간에서 대신 요청/응답을 전달하는 구성요소
Forward Proxy = 클라이언트를 대신해서 외부 서버에 요청
Reverse Proxy = 서버를 대신해서 클라이언트 요청을 받음
라우팅 = 요청이나 패킷을 어디로 보낼지 결정하는 것
네트워크 라우팅 = IP 기준으로 다음 경로 결정
HTTP 라우팅 = Host, Path 등 HTTP 정보 기준으로 백엔드 결정
Nginx = 웹 서버이자 리버스 프록시/로드밸런서로 사용 가능
Ingress = Kubernetes의 HTTP/HTTPS 라우팅 규칙
Ingress Controller = Ingress 규칙을 실제로 처리하는 리버스 프록시
Service = Pod 그룹으로 트래픽을 보내는 Kubernetes 내부 진입점
API Gateway = API 운영 기능이 강화된 리버스 프록시
Service Mesh = 서비스 간 통신을 프록시로 제어하는 인프라 계층
```

## 21. 한 문장 정리

```text
Forward Proxy는 클라이언트 앞에서 외부 요청을 대신하고, Reverse Proxy는 서버 앞에서 들어오는 요청을 대신 받으며, Ingress는 Kubernetes에서 리버스 프록시가 어떤 Service로 보낼지 정의하는 HTTP 라우팅 규칙이다.
```
