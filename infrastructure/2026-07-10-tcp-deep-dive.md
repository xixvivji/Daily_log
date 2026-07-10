# 2026-07-10 TCP 심화: 연결, 재전송, Timeout, Keep-Alive

## 핵심 관점

TCP는 백엔드와 인프라에서 거의 매일 마주치는 기반 프로토콜이다.

웹 요청도, SSH 접속도, 데이터베이스 연결도 대부분 TCP 위에서 동작한다.

```text
HTTP  → TCP
HTTPS → TLS → TCP
SSH   → TCP
MySQL → TCP
Redis → TCP
```

그래서 장애가 났을 때 아래를 구분할 수 있어야 한다.

```text
포트가 아예 안 열려 있는가?
네트워크 경로가 막혀 있는가?
연결은 됐는데 응답이 느린가?
연결이 너무 많이 쌓였는가?
서버가 연결을 먼저 끊는가?
클라이언트가 timeout을 먼저 내는가?
```

## 1. TCP가 해결하려는 문제

IP는 목적지까지 패킷을 보내는 역할을 한다.

하지만 IP 자체는 아래를 보장하지 않는다.

```text
패킷이 반드시 도착하는가?
순서대로 도착하는가?
중복 패킷이 없는가?
상대가 받을 준비가 되었는가?
너무 빠르게 보내서 상대를 터뜨리지 않는가?
```

TCP는 이 문제를 해결하기 위해 연결, 순서, 재전송, 흐름 제어, 혼잡 제어를 제공한다.

```text
연결 지향
순서 보장
손실 패킷 재전송
흐름 제어
혼잡 제어
```

## 2. TCP 3-way handshake

TCP 연결은 데이터를 보내기 전에 먼저 연결을 맺는다.

```text
Client → Server: SYN
Server → Client: SYN-ACK
Client → Server: ACK
```

의미:

```text
SYN
→ 연결하고 싶다.

SYN-ACK
→ 요청 받았다. 나도 연결 준비됐다.

ACK
→ 확인했다. 이제 데이터 보내자.
```

웹 요청 흐름으로 보면:

```text
브라우저
→ DNS 조회
→ 서버 IP 확인
→ 서버 443 포트로 TCP 연결
→ TLS handshake
→ HTTP 요청
```

TCP 연결이 실패하면 HTTP 요청은 시작도 못 한다.

## 3. TCP 4-way close

TCP 연결 종료는 양쪽 방향을 각각 닫는다.

단순화하면:

```text
Client → Server: FIN
Server → Client: ACK
Server → Client: FIN
Client → Server: ACK
```

TCP는 양방향 통신이라서 한쪽이 "나는 더 보낼 데이터가 없다"고 해도, 상대방은 아직 보낼 데이터가 있을 수 있다.

그래서 종료 과정이 연결 시작보다 복잡하다.

## 4. TCP 상태

운영 중 자주 보는 TCP 상태는 다음과 같다.

```text
LISTEN
→ 서버가 특정 포트에서 연결을 기다리는 상태

ESTABLISHED
→ 연결이 성립되어 데이터 송수신 가능한 상태

TIME_WAIT
→ 연결 종료 후 잠시 대기하는 상태

CLOSE_WAIT
→ 상대가 연결 종료를 요청했지만 내 애플리케이션이 아직 닫지 않은 상태

SYN_SENT
→ 클라이언트가 SYN을 보냈고 응답을 기다리는 상태

SYN_RECV
→ 서버가 SYN을 받고 SYN-ACK를 보낸 상태
```

서버에서 `LISTEN`이 없으면 해당 포트에서 받는 프로세스가 없는 것이다.

```bash
ss -lntp
```

예:

```text
LISTEN 0 128 0.0.0.0:80
```

의미:

```text
서버가 80번 포트에서 TCP 연결을 기다리고 있다.
```

## 5. TIME_WAIT

TIME_WAIT는 연결 종료 후 잠시 남아 있는 정상 상태다.

이유:

```text
늦게 도착한 패킷이 새 연결에 섞이지 않게 함
마지막 ACK가 유실됐을 때 재전송에 대응함
```

TIME_WAIT가 보인다고 무조건 문제는 아니다.

하지만 너무 많이 쌓이면 아래를 의심한다.

```text
짧은 TCP 연결을 너무 많이 생성
HTTP keep-alive 미사용
DB connection pool 미사용
외부 API를 매 요청마다 새 연결로 호출
로드밸런서와 서버 timeout 불일치
```

## 6. CLOSE_WAIT

CLOSE_WAIT는 상대가 연결을 닫겠다고 했는데 내 애플리케이션이 아직 소켓을 닫지 않은 상태다.

많이 쌓이면 애플리케이션 버그일 수 있다.

예:

```text
상대가 FIN 보냄
서버 OS는 받음
하지만 애플리케이션이 close를 호출하지 않음
→ CLOSE_WAIT 누적
```

결과:

```text
파일 디스크립터 고갈
새 연결 실패
간헐적인 장애
```

TIME_WAIT는 정상적으로 흔히 보일 수 있지만, CLOSE_WAIT가 계속 쌓이면 애플리케이션 연결 해제 로직을 봐야 한다.

## 7. Connection Refused

`connection refused`는 목적지까지 갔지만 해당 포트에서 연결을 받아주는 대상이 없거나 거절한 상황이다.

예:

```text
Nginx → 127.0.0.1:8080
하지만 8080에 backend container가 없음
→ connection refused
→ Nginx 502 가능
```

확인:

```bash
curl -v http://127.0.0.1:8080/health
ss -lntp
docker ps
docker port backend
```

주요 원인:

```text
프로세스가 죽음
포트가 다름
컨테이너 포트 매핑이 다름
Nginx proxy_pass 포트가 틀림
애플리케이션이 127.0.0.1에만 bind되어 외부에서 접근 불가
```

## 8. Connection Timed Out

`connection timed out`은 연결 요청을 보냈는데 응답이 오지 않는 상황이다.

connection refused와 다르게 상대가 명확히 거절한 것이 아니라 응답 자체가 없다.

주요 원인:

```text
Security Group이 막음
NACL이 막음
OS 방화벽이 막음
라우팅 테이블에 경로가 없음
서버가 다른 subnet에 있고 경로가 없음
대상 IP가 틀림
```

AWS에서 자주 보는 예:

```text
ALB → EC2:80
EC2 Security Group이 ALB SG를 허용하지 않음
→ Target Group health check timeout
```

확인:

```text
Security Group inbound
Security Group outbound
NACL inbound/outbound
Route Table
서버 프로세스 listen 여부
```

## 9. Read Timeout

Read timeout은 연결은 됐고 요청도 보냈지만 응답을 읽는 데 시간이 너무 오래 걸리는 상황이다.

예:

```text
Nginx → backend 연결 성공
HTTP 요청 전달 성공
backend 응답 지연
Nginx proxy_read_timeout 초과
→ 504 Gateway Timeout
```

의심:

```text
DB 쿼리 지연
외부 API 지연
thread pool 고갈
connection pool 고갈
애플리케이션 deadlock
락 경합
```

connect timeout과 read timeout은 다르다.

```text
connect timeout
→ 연결을 맺는 단계 실패

read timeout
→ 연결 이후 응답을 기다리다 실패
```

## 10. Keep-Alive

TCP 연결은 생성 비용이 있다.

```text
TCP 3-way handshake
TLS handshake
커널 리소스
서버 connection 관리
```

HTTP keep-alive는 요청마다 새 연결을 만들지 않고 기존 연결을 재사용한다.

장점:

```text
연결 생성 비용 감소
응답 지연 감소
서버 자원 효율 증가
TLS handshake 반복 감소
```

하지만 keep-alive timeout이 서로 맞지 않으면 간헐적인 문제가 생길 수 있다.

예:

```text
ALB idle timeout: 60초
Backend keep-alive timeout: 30초
```

backend가 먼저 연결을 닫았는데 ALB가 그 연결을 재사용하려 하면 오류가 날 수 있다.

## 11. Flow Control

Flow control은 받는 쪽이 처리할 수 있는 만큼만 보내도록 조절하는 기능이다.

TCP에는 receive window가 있다.

```text
받는 쪽이 지금 얼마나 더 받을 수 있는지 알려줌
보내는 쪽은 그 범위 안에서 전송
```

받는 쪽 애플리케이션이 느리면 window가 줄어들 수 있다.

결과:

```text
전송 속도 감소
응답 지연
처리량 저하
```

## 12. Congestion Control

Congestion control은 네트워크가 혼잡할 때 전송량을 조절하는 기능이다.

대표 개념:

```text
slow start
congestion window
packet loss
retransmission
```

처음부터 최대 속도로 보내지 않고 천천히 늘린다.

```text
처음에는 적게 보냄
ACK가 잘 오면 점점 늘림
손실이 감지되면 줄임
```

운영에서 직접 튜닝할 일은 많지 않지만, 네트워크 지연과 처리량을 이해할 때 중요하다.

## 13. Retransmission

TCP는 손실된 패킷을 재전송한다.

손실이 발생하면:

```text
ACK가 안 옴
timeout 발생
패킷 재전송
```

재전송이 많으면 아래를 의심한다.

```text
네트워크 품질 문제
패킷 손실
혼잡
무선 네트워크 불안정
MTU 문제
```

패킷 캡처로 확인할 때는 retransmission이 중요한 단서가 된다.

## 14. Backend에서 TCP를 볼 때

백엔드 서버 운영 중 TCP와 관련해서 자주 확인하는 것:

```text
서버가 포트를 listen 중인가?
connection refused인가 timeout인가?
ESTABLISHED 연결이 너무 많은가?
TIME_WAIT가 과도하게 많은가?
CLOSE_WAIT가 누적되는가?
DB connection pool이 부족한가?
외부 API 호출 timeout이 적절한가?
ALB/Nginx/backend timeout이 서로 맞는가?
```

명령어:

```bash
ss -lntp
ss -ant
curl -v http://127.0.0.1:8080/health
nc -vz example.com 443
```

## 최종 정리

```text
TCP는 연결 지향 통신이며 HTTP, HTTPS, SSH, DB 연결의 기반이다.
3-way handshake는 연결 시작 과정이다.
4-way close는 연결 종료 과정이다.
TIME_WAIT는 정상 상태일 수 있지만 너무 많으면 연결 재사용 구조를 봐야 한다.
CLOSE_WAIT가 쌓이면 애플리케이션이 소켓을 닫지 않는 문제일 수 있다.
connection refused는 포트에 프로세스가 없거나 거절된 상황이다.
connection timed out은 방화벽, 라우팅, 네트워크 경로 문제일 가능성이 높다.
read timeout은 연결 이후 응답이 늦은 상황이다.
keep-alive는 연결 재사용으로 성능을 높이지만 timeout 설정을 맞춰야 한다.
```
