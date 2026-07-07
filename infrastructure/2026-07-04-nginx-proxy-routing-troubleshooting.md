# 2026-07-04 프록시와 라우팅 심화 개념 정리

## 핵심 관점

프록시와 라우팅을 더 공부하되, 추상적인 개념을 늘리기보다 실제 배포 구조에서 바로 쓰이는 내용 위주로 정리한다.

현재 기준에서 가장 중요한 연결점은 다음 구조다.

```text
사용자
→ Nginx
→ blue container 또는 green container
→ backend application
```

이 구조를 제대로 이해하려면 단순히 "Nginx가 리버스 프록시다"에서 끝나면 안 된다.

아래 5개는 EC2, Docker, Nginx 기반 배포에서 자주 마주치는 핵심 개념이다.

```text
1. Nginx location 매칭 규칙
2. proxy_pass 경로 처리
3. X-Forwarded-* 프록시 헤더
4. 502 / 503 / 504 장애 원인
5. 무중단 배포와 graceful shutdown
```

각 개념은 다음 질문과 연결해서 보면 좋다.

```text
이 개념이 왜 필요한가?
Nginx 설정에서는 어디에 등장하는가?
장애가 나면 어떤 증상으로 보이는가?
내가 만든 blue/green 배포 구조와 어떻게 연결되는가?
```

## 1. Nginx location 매칭 규칙

### 1. Nginx location 매칭 규칙 - 왜 필요한가?

Nginx에서 요청을 어디로 보낼지는 `location` 블록이 결정한다.

예를 들어 아래처럼 설정할 수 있다.

```nginx
server {
    listen 80;

    location /api/ {
        proxy_pass http://127.0.0.1:8080;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

이 설정은 대략 이런 의미다.

```text
/api/ 로 시작하는 요청 → backend
그 외 요청 → frontend
```

하지만 location 규칙이 많아지면 어떤 블록이 선택되는지 헷갈릴 수 있다.

### 알아야 할 location 종류

```nginx
location / {
}

location /api/ {
}

location = /health {
}

location ^~ /static/ {
}

location ~ \.jpg$ {
}
```

각 의미:

```text
location /           기본 prefix 매칭
location /api/       /api/ 로 시작하는 요청 매칭
location = /health   정확히 /health 만 매칭
location ^~ /static/ prefix 매칭 후 정규식 검사 건너뜀
location ~ \.jpg$    대소문자 구분 정규식 매칭
location ~* \.jpg$   대소문자 무시 정규식 매칭
```

### 매칭 우선순위

대략 아래 순서로 이해하면 된다.

```text
1. = 정확히 일치하는 location
2. ^~ prefix location
3. 정규식 location
4. 가장 긴 prefix location
```

예시:

```nginx
location = /health {
    return 200 "ok";
}

location /api/ {
    proxy_pass http://backend;
}

location / {
    proxy_pass http://frontend;
}
```

요청별 결과:

```text
/health        → location = /health
/api/users     → location /api/
/api/orders/1  → location /api/
/              → location /
/about         → location /
```

### 1. Nginx location 매칭 규칙 - 핵심 정리

```text
location / 와 location /api/ 차이를 설명할 수 있다.
location = /health 가 왜 health check에 자주 쓰이는지 설명할 수 있다.
요청 path를 보고 어떤 location이 선택될지 예측할 수 있다.
```

## 2. proxy_pass 경로 처리

### 2. proxy_pass 경로 처리 - 왜 필요한가?

Nginx에서 가장 자주 헷갈리는 부분 중 하나가 `proxy_pass` 뒤의 슬래시다.

아래 두 설정은 비슷해 보이지만 URI 전달 방식이 달라질 수 있다.

```nginx
location /api/ {
    proxy_pass http://backend;
}
```

```nginx
location /api/ {
    proxy_pass http://backend/;
}
```

### 2. proxy_pass 경로 처리 - 핵심 개념

`proxy_pass`에 URI 부분이 있느냐 없느냐가 중요하다.

```text
proxy_pass http://backend;
→ 원래 URI를 거의 그대로 넘김

proxy_pass http://backend/;
→ location에 매칭된 prefix를 바꿔서 넘길 수 있음
```

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

백엔드가 받는 경로:

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

백엔드가 받는 경로:

```text
/users
```

즉 `/api/` prefix가 제거된 것처럼 동작할 수 있다.

### 언제 문제가 되는가?

백엔드 애플리케이션이 `/api/users`를 기대하는데 Nginx가 `/users`로 넘기면 404가 날 수 있다.

반대로 백엔드는 `/users`를 기대하는데 Nginx가 `/api/users`로 넘겨도 404가 날 수 있다.

증상:

```text
Nginx까지 요청은 도착함
백엔드도 살아 있음
그런데 특정 API만 404
로컬에서는 되는데 배포하면 안 됨
```

이런 경우 `location`과 `proxy_pass`의 경로 처리부터 봐야 한다.

### 2. proxy_pass 경로 처리 - 핵심 정리

```text
proxy_pass http://backend; 와 proxy_pass http://backend/; 차이를 설명할 수 있다.
백엔드가 실제로 어떤 path를 받는지 예측할 수 있다.
404가 났을 때 Nginx 경로 rewrite 문제를 의심할 수 있다.
```

## 3. X-Forwarded-* 프록시 헤더

### 3. X-Forwarded-* 프록시 헤더 - 왜 필요한가?

백엔드 앞에 Nginx 같은 리버스 프록시가 있으면, 백엔드는 클라이언트가 직접 접속한 것이 아니라 Nginx가 접속한 것처럼 볼 수 있다.

구조:

```text
사용자 브라우저
→ Nginx
→ Backend
```

백엔드 입장에서는 요청을 보낸 상대가 사용자 브라우저가 아니라 Nginx일 수 있다.

그래서 원래 클라이언트 정보를 헤더로 전달한다.

### 자주 쓰는 헤더

```text
Host
X-Real-IP
X-Forwarded-For
X-Forwarded-Proto
X-Forwarded-Host
Forwarded
```

Nginx 설정 예:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

각 의미:

```text
Host
→ 원래 요청한 도메인

X-Real-IP
→ Nginx가 본 클라이언트 IP

X-Forwarded-For
→ 프록시를 거친 클라이언트 IP 목록

X-Forwarded-Proto
→ 원래 요청 프로토콜 http 또는 https
```

### 왜 문제가 되는가?

백엔드가 원래 요청이 HTTPS였는지 몰라서 문제가 생길 수 있다.

예:

```text
브라우저 → HTTPS → Nginx → HTTP → Backend
```

이때 백엔드는 자기에게 HTTP로 요청이 왔다고 생각한다.

그래서 다음 문제가 생길 수 있다.

```text
HTTPS 리다이렉트 무한 반복
Secure Cookie 설정 문제
OAuth callback URL 문제
로그에 클라이언트 IP가 전부 127.0.0.1로 찍힘
백엔드가 잘못된 absolute URL 생성
```

### 3. X-Forwarded-* 프록시 헤더 - 핵심 정리

```text
X-Forwarded-For가 왜 필요한지 설명할 수 있다.
X-Forwarded-Proto가 HTTPS 리다이렉트와 어떤 관계인지 설명할 수 있다.
Nginx 뒤의 백엔드에서 클라이언트 IP가 이상하게 찍히는 이유를 설명할 수 있다.
```

## 4. 502 / 503 / 504 장애 원인

### 4. 502 / 503 / 504 장애 원인 - 왜 필요한가?

Nginx를 앞에 두고 배포하면 장애가 났을 때 500만 보는 게 아니라 502, 503, 504를 자주 보게 된다.

이 셋은 모두 프록시/게이트웨이 구조에서 자주 등장한다.

### 502 Bad Gateway

502는 Nginx가 뒤쪽 서버에 요청을 보냈는데 정상 응답을 받지 못했을 때 자주 발생한다.

대표 원인:

```text
백엔드 컨테이너가 죽어 있음
Nginx가 잘못된 포트로 proxy_pass 중
백엔드가 연결을 바로 끊음
upstream 주소가 잘못됨
애플리케이션이 크래시남
```

예:

```text
Nginx → 127.0.0.1:8080
하지만 8080에 아무 프로세스도 없음
→ 502
```

확인:

```bash
curl -v http://127.0.0.1:8080/health
docker ps
docker logs backend-blue
tail -f /var/log/nginx/error.log
```

### 503 Service Unavailable

503은 서비스가 일시적으로 사용할 수 없다는 의미다.

대표 원인:

```text
upstream에 사용 가능한 서버가 없음
백엔드가 준비 상태가 아님
maintenance 상태
로드밸런서 대상이 모두 unhealthy
Ingress Service endpoint가 비어 있음
```

Kubernetes에서는 Service에 연결된 Pod가 Ready가 아니면 503 계열 문제가 날 수 있다.

### 504 Gateway Timeout

504는 프록시가 뒤쪽 서버에 요청했지만 시간 안에 응답을 못 받았다는 뜻이다.

대표 원인:

```text
백엔드 응답이 너무 느림
DB 쿼리가 오래 걸림
외부 API 호출이 지연됨
Nginx proxy timeout이 너무 짧음
네트워크 연결이 지연됨
```

확인:

```text
Nginx timeout 설정
백엔드 응답 시간
DB slow query
외부 API 지연
애플리케이션 로그
```

### 4. 502 / 503 / 504 장애 원인 - 핵심 정리

```text
502는 upstream 연결/응답 문제로 볼 수 있다.
503은 사용할 수 있는 서비스 대상이 없거나 준비되지 않은 상태로 볼 수 있다.
504는 upstream 응답 지연으로 볼 수 있다.
```

## 5. 무중단 배포와 graceful shutdown

### 5. 무중단 배포와 graceful shutdown - 왜 필요한가?

blue/green 컨테이너를 두 개 띄우고 Nginx 방향을 바꾸면 중단 시간을 많이 줄일 수 있다.

하지만 이것만으로 항상 완벽한 무중단 배포가 되는 것은 아니다.

운영 중 요청이 처리되는 도중에 기존 컨테이너를 바로 죽이면 요청이 끊길 수 있다.

### 단일 인스턴스 blue/green 흐름

예:

```text
현재 active: blue:8080
inactive: green:8081
```

배포 순서:

```text
1. green 컨테이너에 새 버전 실행
2. green health check
3. Nginx upstream을 green으로 전환
4. Nginx reload
5. 새 요청은 green으로 이동
6. 기존 blue 요청이 끝날 시간을 잠깐 기다림
7. blue 컨테이너 종료
```

핵심은 이 부분이다.

```text
새 요청은 green으로 보내고,
기존 blue 요청은 가능한 끝까지 처리하게 둔다.
```

### graceful shutdown이란?

graceful shutdown은 애플리케이션을 종료할 때 바로 죽이지 않고, 기존 요청을 마무리할 시간을 주는 것이다.

나쁜 종료:

```text
kill -9
→ 처리 중이던 요청도 즉시 끊김
```

좋은 종료:

```text
SIGTERM 전달
→ 새 요청은 받지 않음
→ 처리 중인 요청 완료
→ 리소스 정리
→ 프로세스 종료
```

Docker에서는 보통 `docker stop`이 먼저 SIGTERM을 보내고, 일정 시간 후에도 안 죽으면 SIGKILL을 보낸다.

```bash
docker stop --time 30 backend-blue
```

의미:

```text
30초 동안 정상 종료를 기다린다.
```

### readiness와 health check

health check는 새 컨테이너가 트래픽을 받을 준비가 되었는지 확인하는 과정이다.

예:

```bash
curl -f http://127.0.0.1:8081/health
```

단순히 프로세스가 떠 있는 것과 요청을 받을 준비가 된 것은 다르다.

확인해야 할 것:

```text
애플리케이션이 정상 시작됐는가?
DB 연결이 되는가?
필수 설정이 로드됐는가?
외부 의존성이 최소한 확인됐는가?
```

### 블루/그린에서 자주 생기는 문제

```text
새 컨테이너가 뜨자마자 전환했는데 아직 앱 초기화 중
Nginx reload 전에 설정 테스트를 안 해서 프록시 깨짐
전환 직후 기존 컨테이너를 바로 죽여 처리 중 요청이 끊김
DB 마이그레이션이 이전 버전과 호환되지 않음
WebSocket 또는 long polling 연결이 끊김
```

Nginx 설정 테스트:

```bash
nginx -t
```

전환 후 확인:

```bash
curl -I https://example.com
curl -f http://127.0.0.1:8081/health
tail -f /var/log/nginx/error.log
docker logs backend-green
```

### 5. 무중단 배포와 graceful shutdown - 핵심 정리

```text
blue/green이 왜 무중단 배포에 도움이 되는지 설명할 수 있다.
Nginx 전환 후 기존 컨테이너를 바로 죽이면 왜 위험한지 설명할 수 있다.
graceful shutdown과 docker stop --time의 의미를 설명할 수 있다.
health check와 readiness의 차이를 설명할 수 있다.
```

## 개념 확인 예시

아래 예시는 개념을 확인할 때 사용할 수 있다.

### Nginx location 결과 예측

아래 설정에서 각 요청이 어느 location으로 가는지 예측한다.

```nginx
location = /health {}
location /api/ {}
location / {}
```

요청:

```text
/health
/api/users
/api
/api/
/about
/
```

### proxy_pass 경로 예측

아래 두 설정에서 `/api/users` 요청이 백엔드에 어떤 path로 전달되는지 비교한다.

```nginx
location /api/ {
    proxy_pass http://backend;
}
```

```nginx
location /api/ {
    proxy_pass http://backend/;
}
```

### 장애 원인 분류

아래 상황은 502, 503, 504 중 어디에 가까운지 분류해 볼 수 있다.

```text
Nginx가 8080으로 보내는데 컨테이너가 안 떠 있음
백엔드가 60초 넘게 응답하지 않음
로드밸런서에 healthy target이 하나도 없음
Ingress Service endpoint가 비어 있음
백엔드 앱이 요청 처리 중 크래시남
```

### 단일 EC2 blue/green 배포 흐름

단일 EC2 blue/green 배포는 보통 아래 흐름으로 정리할 수 있다.

```text
1. inactive 포트 확인
2. 새 이미지 pull
3. inactive 컨테이너 실행
4. health check
5. Nginx 설정 변경
6. nginx -t
7. nginx reload
8. 외부 health check
9. 기존 컨테이너 graceful stop
10. 실패 시 rollback
```

## 마무리 질문

아래 질문에 답할 수 있으면 이 개념들은 어느 정도 정리된 것이다.

```text
Nginx location은 어떤 기준으로 요청을 고르는가?
proxy_pass 뒤에 슬래시가 있으면 무엇이 달라질 수 있는가?
X-Forwarded-For와 X-Forwarded-Proto는 왜 필요한가?
502, 503, 504는 각각 어떤 상황을 의심해야 하는가?
blue/green 배포에서 Nginx 전환 후 기존 컨테이너를 바로 죽이면 왜 위험한가?
graceful shutdown은 어떤 문제를 줄여주는가?
```

## 최종 요약

```text
Nginx location은 HTTP 요청 path를 기준으로 어떤 처리 블록을 사용할지 결정한다.
proxy_pass는 슬래시 유무에 따라 백엔드로 전달되는 URI가 달라질 수 있다.
X-Forwarded-* 헤더는 리버스 프록시 뒤의 백엔드가 원래 클라이언트 정보를 알기 위해 필요하다.
502는 upstream 연결/응답 문제, 503은 사용 가능한 대상 없음, 504는 upstream 응답 지연을 먼저 의심한다.
단일 EC2 blue/green 배포는 로드밸런싱이 아니라 Nginx 리버스 프록시 기반 트래픽 스위칭이다.
무중단에 가깝게 만들려면 health check, nginx -t, reload, graceful shutdown, rollback 순서를 챙겨야 한다.
```
