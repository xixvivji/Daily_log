# 2026-07-09 남은 네트워크 심화: Routing, NAT, DNS, TCP, HTTP, TLS, Firewall

## 핵심 관점

지금까지 정리한 네트워크 내용은 아래 기반을 잡는 데 집중했다.

```text
네트워크란 무엇인가
패킷
프로토콜
IP와 MAC 주소
라우터와 스위치
게이트웨이
사설 IP와 공인 IP
NAT 기본
IP 주소
Subnet Mask
CIDR
같은 네트워크와 다른 네트워크 판단
TCP, DNS, HTTP, TLS 기본 흐름
Nginx / Docker / AWS 배포 구조
```

이제 남은 네트워크 심화는 단순 암기보다 실제 운영 상황에서 문제를 추적하기 위한 내용이다.

예를 들어 사용자가 사이트에 접속하지 못할 때 실제로는 아래 중 하나일 수 있다.

```text
라우팅 테이블에 경로가 없음
default route가 잘못됨
Internet Gateway가 연결되지 않음
Private Subnet에서 NAT Gateway 없이 인터넷으로 나가려 함
Security Group이 막음
NACL이 막음
DNS가 잘못된 대상으로 해석됨
TCP 연결이 안 됨
TLS 인증서가 잘못됨
HTTP Host 또는 path 라우팅이 틀림
Nginx upstream이 죽어 있음
```

따라서 남은 네트워크 주제는 아래 순서로 이해하면 좋다.

```text
1. Routing Table
2. Default Route
3. Internet Gateway
4. NAT / NAT Gateway
5. ARP
6. DNS 심화
7. TCP 심화
8. UDP
9. HTTP 심화
10. HTTPS / TLS 심화
11. Firewall / Security Group / NACL
12. 장애 분석 흐름
```

## 1. Routing Table

### Routing Table이 필요한 이유

IP와 subnet을 배우면 아래 판단까지 할 수 있다.

```text
같은 네트워크면 직접 보낸다.
다른 네트워크면 게이트웨이로 보낸다.
```

그다음 질문은 이것이다.

```text
다른 네트워크로 보낼 때 어떤 게이트웨이로 보내야 하는가?
```

이걸 결정하는 표가 routing table이다.

Routing Table은 목적지 IP 대역별로 다음에 어디로 보낼지 적어둔 규칙표다.

```text
목적지 대역        다음으로 보낼 곳
192.168.0.0/24    직접 연결된 로컬 네트워크
0.0.0.0/0         192.168.0.1 게이트웨이
```

이 표를 보고 운영체제나 라우터는 패킷을 어디로 보낼지 결정한다.

### 집 네트워크 예시

내 PC 설정:

```text
IP:       192.168.0.10/24
Gateway: 192.168.0.1
```

Routing Table을 단순화하면:

```text
Destination       Next Hop
192.168.0.0/24    직접 전달
0.0.0.0/0         192.168.0.1
```

상대가 같은 네트워크:

```text
목적지: 192.168.0.20
```

`192.168.0.20`은 `192.168.0.0/24`에 포함된다.

```text
192.168.0.10 → 192.168.0.20
직접 전달
```

상대가 인터넷:

```text
목적지: 8.8.8.8
```

`8.8.8.8`은 `192.168.0.0/24`에 포함되지 않는다.

그러면 `0.0.0.0/0` 규칙을 사용한다.

```text
192.168.0.10
→ Gateway 192.168.0.1
→ Internet
→ 8.8.8.8
```

### Longest Prefix Match

라우팅 테이블에서 여러 규칙이 매칭될 수 있다.

이때 더 구체적인 규칙이 이긴다.

이를 longest prefix match라고 한다.

예:

```text
Destination       Next Hop
10.0.0.0/16       local
10.0.1.0/24       gateway-a
0.0.0.0/0         gateway-default
```

목적지가:

```text
10.0.1.50
```

이면 아래 두 규칙 모두에 포함된다.

```text
10.0.0.0/16
10.0.1.0/24
```

하지만 `/24`가 `/16`보다 더 구체적이다.

그래서:

```text
10.0.1.0/24 → gateway-a
```

가 선택된다.

목적지가:

```text
10.0.2.50
```

이면 `10.0.1.0/24`에는 포함되지 않고 `10.0.0.0/16`에는 포함된다.

그래서:

```text
10.0.0.0/16 → local
```

이 선택된다.

## 2. Default Route

### Default Route란?

Default Route는 더 구체적인 경로가 없을 때 사용하는 기본 경로다.

보통 이렇게 표현한다.

```text
0.0.0.0/0
```

`0.0.0.0/0`은 모든 IPv4 주소를 의미한다.

왜냐하면 `/0`은 비교할 네트워크 비트가 0개라는 뜻이기 때문이다.

```text
0.0.0.0/0
→ 어떤 목적지든 매칭됨
```

라우팅 테이블에서:

```text
0.0.0.0/0 → 192.168.0.1
```

의미:

```text
내가 아는 로컬 네트워크가 아니면 전부 192.168.0.1로 보내라.
```

집에서는 보통 공유기가 default gateway다.

AWS에서는 public subnet에서 default route가 Internet Gateway를 가리키는 경우가 많다.

```text
0.0.0.0/0 → Internet Gateway
```

private subnet에서는 default route가 NAT Gateway를 가리키는 경우가 많다.

```text
0.0.0.0/0 → NAT Gateway
```

### Default Route가 없으면 어떻게 되는가?

같은 네트워크끼리는 통신할 수 있다.

하지만 외부 네트워크로 나갈 수 없다.

예:

```text
내 IP: 192.168.0.10/24
Routing Table:
192.168.0.0/24 → 직접 전달
```

이 상태에서:

```text
192.168.0.20
```

으로는 갈 수 있다.

하지만:

```text
8.8.8.8
```

으로는 보낼 경로가 없다.

증상:

```text
같은 네트워크의 장비는 ping 됨
인터넷은 안 됨
DNS도 외부 resolver를 쓰면 안 됨
```

## 3. AWS Route Table

### AWS Route Table의 역할

AWS VPC에서도 routing table이 있다.

VPC 안의 subnet은 route table과 연결된다.

Route Table은 해당 subnet에서 나가는 트래픽을 어디로 보낼지 정한다.

예:

```text
VPC: 10.0.0.0/16
Public Subnet: 10.0.1.0/24
Private Subnet: 10.0.2.0/24
```

Public subnet route table:

```text
Destination      Target
10.0.0.0/16      local
0.0.0.0/0        Internet Gateway
```

Private subnet route table:

```text
Destination      Target
10.0.0.0/16      local
0.0.0.0/0        NAT Gateway
```

`local`은 VPC 내부 통신을 의미한다.

```text
10.0.1.10 → 10.0.2.20
VPC 내부 대역이므로 local
```

인터넷으로 나가는 트래픽은 subnet 종류에 따라 다르다.

Public subnet:

```text
0.0.0.0/0 → Internet Gateway
```

Private subnet:

```text
0.0.0.0/0 → NAT Gateway
```

### Public Subnet과 Private Subnet의 차이

Subnet 자체가 public/private인 것은 아니다.

정확히는 route table 때문에 public/private 성격이 정해진다.

Public subnet:

```text
0.0.0.0/0 → Internet Gateway
```

Private subnet:

```text
0.0.0.0/0 → Internet Gateway가 없음
```

또는 외부로 나가야 하면:

```text
0.0.0.0/0 → NAT Gateway
```

즉 핵심은 이것이다.

```text
Internet Gateway로 직접 나갈 수 있으면 public subnet
Internet Gateway로 직접 나갈 수 없으면 private subnet
```

단, public subnet에 있다고 무조건 인터넷에서 접근 가능한 것은 아니다.

아래 조건도 필요하다.

```text
Public IPv4 또는 Elastic IP가 있어야 함
Security Group이 허용해야 함
NACL이 허용해야 함
OS 방화벽이 허용해야 함
해당 포트에서 프로세스가 listen 중이어야 함
```

## 4. Internet Gateway

### Internet Gateway란?

Internet Gateway는 VPC와 인터넷을 연결하는 출입구다.

AWS에서 public subnet의 route table은 보통 Internet Gateway를 향한다.

```text
0.0.0.0/0 → igw-xxxx
```

흐름:

```text
Internet
↔ Internet Gateway
↔ Public Subnet
↔ EC2 또는 ALB
```

Internet Gateway가 있어야 VPC 리소스가 인터넷과 직접 통신할 수 있다.

하지만 Internet Gateway만 있다고 끝은 아니다.

EC2가 인터넷에서 직접 접근 가능하려면:

```text
Subnet route table에 Internet Gateway 경로가 있어야 함
EC2에 Public IP가 있어야 함
Security Group inbound가 열려 있어야 함
NACL inbound/outbound가 허용되어야 함
서버 프로세스가 해당 포트를 열고 있어야 함
```

예:

```text
사용자 → EC2:80
```

필요 조건:

```text
EC2 public IP 존재
Public subnet route table: 0.0.0.0/0 → Internet Gateway
Security Group: inbound 80 허용
NACL: inbound/outbound 허용
Nginx 또는 앱이 80 listen
```

## 5. NAT와 NAT Gateway

### NAT가 필요한 이유

NAT는 Network Address Translation이다.

주소를 바꿔서 통신하게 해주는 기능이다.

가장 흔한 목적은 사설 IP가 인터넷에 나갈 수 있게 하는 것이다.

사설 IP는 인터넷에서 직접 라우팅되지 않는다.

예:

```text
내 PC: 192.168.0.10
공유기 공인 IP: 203.0.113.5
```

내 PC가 인터넷으로 나갈 때:

```text
192.168.0.10:50000
→ 공유기 NAT
→ 203.0.113.5:62000
→ 인터넷 서버
```

인터넷 서버 입장에서는:

```text
203.0.113.5에서 요청이 왔다.
```

라고 본다.

응답이 돌아오면 공유기는 NAT 테이블을 보고 원래 내부 PC로 돌려준다.

```text
203.0.113.5:62000으로 온 응답
→ NAT 테이블 확인
→ 192.168.0.10:50000으로 전달
```

### NAT 테이블

NAT 장비는 변환 정보를 기억한다.

예:

```text
내부 주소              외부로 보이는 주소
192.168.0.10:50000  → 203.0.113.5:62000
192.168.0.11:50001  → 203.0.113.5:62001
```

포트까지 같이 바꿔서 여러 내부 장비가 하나의 공인 IP를 공유할 수 있다.

이런 방식을 PAT 또는 NAPT라고 부르기도 한다.

실무에서는 보통 NAT라고 뭉뚱그려 말하는 경우가 많다.

### AWS NAT Gateway

AWS NAT Gateway는 private subnet의 리소스가 인터넷으로 나갈 수 있게 해준다.

예:

```text
Private EC2
→ NAT Gateway
→ Internet Gateway
→ Internet
```

Private subnet route table:

```text
Destination      Target
10.0.0.0/16      local
0.0.0.0/0        NAT Gateway
```

NAT Gateway는 public subnet에 둔다.

그리고 Elastic IP를 가진다.

구조:

```text
Private Subnet EC2
→ Route Table
→ NAT Gateway in Public Subnet
→ Internet Gateway
→ Internet
```

### NAT Gateway로 들어오는 요청은 가능한가?

NAT Gateway는 private subnet 리소스가 밖으로 나가기 위한 장치다.

외부 사용자가 NAT Gateway를 통해 private EC2에 직접 들어오는 용도가 아니다.

즉:

```text
Private EC2 → Internet
가능

Internet → NAT Gateway → Private EC2
일반적인 서버 공개 용도로 사용하지 않음
```

외부 사용자가 private EC2의 애플리케이션에 접근해야 한다면 보통 ALB를 앞에 둔다.

```text
User
→ ALB in Public Subnet
→ EC2 in Private Subnet
```

## 6. ARP

### ARP가 필요한 이유

IP 주소는 논리 주소다.

하지만 같은 LAN 안에서 실제 프레임을 보낼 때는 MAC 주소가 필요하다.

그래서 IP 주소를 MAC 주소로 바꾸는 과정이 필요하다.

그 역할을 하는 것이 ARP다.

```text
ARP = Address Resolution Protocol
```

예:

```text
내 PC: 192.168.0.10
상대: 192.168.0.20
```

같은 네트워크라면 내 PC는 상대에게 직접 보내야 한다.

하지만 실제 Ethernet frame을 만들려면 상대 MAC 주소가 필요하다.

내 PC는 이렇게 묻는다.

```text
192.168.0.20 가진 사람 MAC 주소 알려줘
```

상대가 응답한다.

```text
192.168.0.20은 aa:bb:cc:dd:ee:ff야
```

그러면 내 PC는 ARP cache에 저장한다.

```text
192.168.0.20 → aa:bb:cc:dd:ee:ff
```

### 다른 네트워크로 갈 때 ARP는 누구에게 하는가?

목적지가 다른 네트워크면 최종 목적지의 MAC을 찾지 않는다.

게이트웨이의 MAC 주소를 찾는다.

예:

```text
내 PC: 192.168.0.10/24
목적지: 8.8.8.8
Gateway: 192.168.0.1
```

`8.8.8.8`은 같은 네트워크가 아니다.

그래서 내 PC는 패킷을 게이트웨이에게 보낸다.

이때 필요한 MAC은 `8.8.8.8`의 MAC이 아니라 `192.168.0.1`의 MAC이다.

```text
ARP: 192.168.0.1의 MAC 주소 알려줘
```

정리:

```text
같은 네트워크 목적지
→ 목적지 IP의 MAC을 ARP로 찾음

다른 네트워크 목적지
→ Gateway IP의 MAC을 ARP로 찾음
```

## 7. DNS 심화

### DNS가 하는 일

DNS는 도메인 이름을 IP 주소나 다른 이름으로 바꿔준다.

```text
api.example.com
→ 203.0.113.10
```

또는 AWS ALB처럼 이름을 또 다른 이름으로 연결하기도 한다.

```text
api.example.com
→ my-alb-123.ap-northeast-2.elb.amazonaws.com
```

### DNS 조회 흐름

도메인 조회는 대략 아래 흐름으로 진행된다.

```text
브라우저 캐시
→ OS 캐시
→ local resolver
→ recursive resolver
→ root DNS
→ TLD DNS
→ authoritative DNS
```

예:

```text
api.example.com
```

흐름:

```text
root DNS
→ .com 담당 TLD DNS 알려줌

.com TLD DNS
→ example.com authoritative DNS 알려줌

example.com authoritative DNS
→ api.example.com 레코드 응답
```

### Recursive Query와 Iterative Query

Recursive Query:

```text
클라이언트가 resolver에게 최종 답을 요청한다.
resolver가 대신 여러 DNS 서버를 찾아다닌다.
```

Iterative Query:

```text
DNS 서버가 최종 답을 모르면 다음에 물어볼 서버를 알려준다.
```

일반 사용자는 보통 recursive resolver에게 묻는다.

예:

```text
내 PC → 8.8.8.8
```

`8.8.8.8` 같은 recursive resolver가 root, TLD, authoritative DNS를 따라가며 답을 찾아준다.

### TTL과 캐시

DNS에는 TTL이 있다.

```text
TTL = Time To Live
```

의미:

```text
이 DNS 응답을 몇 초 동안 캐싱해도 되는가?
```

예:

```text
TTL 300
→ 300초 동안 캐싱 가능
```

도메인 레코드를 바꿨는데 바로 반영되지 않는 이유가 TTL과 캐시다.

운영에서 도메인 변경 전에는 TTL을 미리 낮추는 경우가 있다.

```text
기존 TTL 3600
→ 변경 전 TTL 60으로 낮춤
→ DNS 변경
→ 안정화 후 TTL 다시 올림
```

### DNS 장애 증상

DNS 문제가 있으면 서버까지 요청이 도달하지 않을 수 있다.

증상:

```text
브라우저에서 도메인을 찾을 수 없음
curl에서 Could not resolve host
특정 사용자만 접속 안 됨
일부 지역에서만 다른 IP로 감
도메인 변경 후 이전 서버로 계속 감
```

확인:

```bash
dig api.example.com
nslookup api.example.com
```

봐야 할 것:

```text
원하는 IP나 ALB 주소로 해석되는가?
TTL이 얼마인가?
다른 resolver에서도 같은 결과인가?
```

## 8. TCP 심화

### TCP의 역할

TCP는 신뢰성 있는 연결 지향 통신을 제공한다.

HTTP, HTTPS, SSH, DB 연결은 대부분 TCP 위에서 동작한다.

```text
HTTP  → TCP
HTTPS → TLS → TCP
SSH   → TCP
MySQL → TCP
```

### 3-way handshake

TCP 연결은 보통 3-way handshake로 시작한다.

```text
Client → Server: SYN
Server → Client: SYN-ACK
Client → Server: ACK
```

의미:

```text
SYN
→ 연결 시작 요청

SYN-ACK
→ 요청 받았고 나도 준비됨

ACK
→ 확인함. 이제 데이터 전송 가능
```

### 4-way handshake

TCP 연결 종료는 보통 FIN과 ACK를 주고받는다.

단순화하면:

```text
Client → Server: FIN
Server → Client: ACK
Server → Client: FIN
Client → Server: ACK
```

연결을 양쪽 방향에서 각각 닫는다고 보면 된다.

### TIME_WAIT

연결을 닫은 뒤에도 한쪽은 잠시 TIME_WAIT 상태에 머문다.

이유:

```text
늦게 도착한 패킷이 새 연결에 섞이지 않게 함
마지막 ACK가 유실됐을 때 재전송에 대응함
```

TIME_WAIT 자체는 정상이다.

하지만 너무 많이 쌓이면 아래를 확인한다.

```text
keep-alive 설정
connection pool
짧은 연결을 너무 많이 만드는 구조
클라이언트 timeout
서버 커널 파라미터
```

### Connection Refused와 Timeout

`connection refused`:

```text
목적지 IP까지 갔고,
해당 포트에서 연결을 거절했거나 듣는 프로세스가 없음
```

예:

```text
Nginx → 127.0.0.1:8080
하지만 8080에 backend container 없음
→ connection refused
→ 502 가능
```

`connection timed out`:

```text
패킷을 보냈지만 응답이 오지 않음
방화벽, Security Group, NACL, 라우팅 문제 가능
```

예:

```text
ALB → EC2:80
Security Group이 막음
→ timeout 또는 unhealthy target
```

## 9. UDP

### UDP란?

UDP는 연결을 맺지 않고 데이터를 보내는 프로토콜이다.

TCP와 달리 3-way handshake가 없다.

```text
TCP
→ 연결을 맺고 데이터 전송
→ 신뢰성, 순서 보장, 재전송

UDP
→ 바로 데이터 전송
→ 빠르지만 신뢰성 보장은 애플리케이션이 처리
```

UDP는 아래에 자주 쓰인다.

```text
DNS
DHCP
VoIP
실시간 게임
영상 스트리밍 일부
QUIC / HTTP/3
```

### DNS는 왜 UDP를 많이 쓰는가?

DNS 요청과 응답은 보통 짧다.

연결을 매번 맺는 TCP보다 UDP가 가볍다.

```text
Client → DNS query
DNS server → DNS response
```

다만 DNS가 항상 UDP만 쓰는 것은 아니다.

아래 상황에서는 TCP를 쓰기도 한다.

```text
응답이 큰 경우
Zone transfer
일부 보안/정책 구성
```

## 10. HTTP 심화

### HTTP 요청 구조

HTTP 요청은 크게 세 부분이다.

```text
Start Line
Headers
Body
```

예:

```http
GET /api/users HTTP/1.1
Host: api.example.com
User-Agent: curl/8.0
Accept: application/json
```

의미:

```text
GET
→ method

/api/users
→ path

HTTP/1.1
→ HTTP version

Host
→ 어떤 도메인으로 요청했는지
```

Nginx는 Host와 path를 기준으로 라우팅할 수 있다.

```nginx
server_name api.example.com;

location /api/ {
    proxy_pass http://backend;
}
```

### HTTP 응답 구조

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-cache

{"ok": true}
```

상태 코드는 장애 분석의 첫 단서다.

```text
2xx → 성공
3xx → 리다이렉트
4xx → 클라이언트 요청 문제
5xx → 서버 또는 프록시 문제
```

### HTTP Cache

HTTP Cache는 같은 응답을 매번 서버에서 새로 받지 않고 저장해서 재사용하는 방식이다.

대표 헤더:

```text
Cache-Control
ETag
Last-Modified
Expires
```

예:

```http
Cache-Control: max-age=3600
```

의미:

```text
3600초 동안 캐시된 응답을 사용해도 된다.
```

주의할 점:

```text
정적 파일은 캐시하면 좋다.
사용자별 응답은 잘못 캐시하면 보안 문제가 생긴다.
배포 후 JS/CSS가 예전 버전으로 남는 문제가 캐시 때문에 생길 수 있다.
```

### HTTP/1.1, HTTP/2, HTTP/3

HTTP/1.1:

```text
텍스트 기반
keep-alive 지원
요청/응답 순서 문제와 head-of-line blocking 이슈가 있음
```

HTTP/2:

```text
바이너리 프레이밍
하나의 TCP 연결에서 여러 요청을 multiplexing
헤더 압축
```

HTTP/3:

```text
TCP 대신 QUIC 사용
QUIC은 UDP 위에서 동작
연결 설정 지연 감소
TCP 레벨 head-of-line blocking 완화
```

처음에는 HTTP/1.1 요청 구조와 status code를 먼저 확실히 잡고, 그다음 HTTP/2, HTTP/3로 가면 된다.

## 11. HTTPS / TLS 심화

### HTTPS 구조

HTTPS는 HTTP에 TLS가 붙은 것이다.

```text
HTTPS = HTTP + TLS
```

흐름:

```text
DNS 조회
→ TCP 연결
→ TLS handshake
→ HTTP 요청
→ HTTP 응답
```

TLS 단계에서 실패하면 애플리케이션 로그에는 요청이 안 찍힐 수 있다.

왜냐하면 HTTP 요청이 애플리케이션까지 도달하지 않았기 때문이다.

### TLS가 제공하는 것

```text
암호화
→ 중간에서 내용을 훔쳐봐도 읽기 어렵게 함

무결성
→ 중간에서 데이터가 바뀌었는지 확인

인증
→ 접속한 서버가 진짜 그 도메인의 서버인지 확인
```

### 인증서 검증

브라우저는 서버 인증서를 확인한다.

```text
서버 인증서
→ 중간 인증서
→ 루트 CA
```

확인 항목:

```text
인증서가 만료되지 않았는가?
도메인이 인증서에 포함되어 있는가?
신뢰할 수 있는 CA가 발급했는가?
인증서 체인이 올바른가?
```

### SNI

SNI는 Server Name Indication이다.

TLS handshake 과정에서 클라이언트가 어떤 도메인에 접속하려는지 서버에게 알려주는 기능이다.

왜 필요하냐면 하나의 IP에서 여러 HTTPS 도메인을 서비스할 수 있기 때문이다.

```text
api.example.com
admin.example.com
www.example.com
```

모두 같은 ALB나 Nginx로 들어올 수 있다.

서버는 SNI를 보고 어떤 인증서를 줄지 결정할 수 있다.

### TLS Termination

TLS termination은 HTTPS 연결을 특정 지점에서 끝내는 것이다.

ALB에서 종료:

```text
Client
→ HTTPS
→ ALB
→ HTTP
→ EC2 / Nginx / Backend
```

Nginx에서 종료:

```text
Client
→ HTTPS
→ Nginx
→ HTTP
→ Backend
```

ALB에서 TLS를 종료하면 ACM 인증서 관리가 편하다.

Nginx에서 TLS를 종료하면 서버에서 인증서와 TLS 설정을 직접 관리해야 한다.

### X-Forwarded-Proto

TLS를 ALB나 Nginx에서 종료하고 backend로 HTTP로 넘기면 backend는 자기에게 HTTP 요청이 왔다고 생각할 수 있다.

원래 사용자가 HTTPS로 접속했다는 사실은 헤더로 알려줘야 한다.

```http
X-Forwarded-Proto: https
```

이 헤더 처리가 잘못되면:

```text
HTTPS 리다이렉트 반복
Secure Cookie 문제
OAuth callback URL 문제
백엔드가 http URL 생성
```

## 12. Firewall / Security Group / NACL

### Firewall이 하는 일

Firewall은 네트워크 트래픽을 허용하거나 차단한다.

기준:

```text
출발지 IP
목적지 IP
프로토콜
포트
방향
```

예:

```text
80 from 0.0.0.0/0
443 from 0.0.0.0/0
22 from 내 IP/32
```

의미:

```text
80 HTTP는 인터넷 전체에서 허용
443 HTTPS는 인터넷 전체에서 허용
22 SSH는 내 IP에서만 허용
```

### Security Group

AWS Security Group은 리소스 단위 방화벽이다.

EC2, ALB, RDS 같은 리소스에 붙는다.

특징:

```text
stateful
allow 규칙만 있음
응답 트래픽은 자동 허용
```

예:

```text
ALB Security Group
- inbound 80 from 0.0.0.0/0
- inbound 443 from 0.0.0.0/0

EC2 Security Group
- inbound 80 from ALB Security Group
- inbound 22 from 내 IP/32
```

이 구조에서는 사용자가 EC2에 직접 들어오지 않고 ALB를 통해 들어온다.

```text
User
→ ALB
→ EC2
```

### NACL

NACL은 subnet 단위 방화벽이다.

특징:

```text
stateless
allow와 deny 규칙이 있음
inbound와 outbound를 각각 명시적으로 봐야 함
규칙 번호 순서대로 평가
```

Security Group과 NACL 차이:

```text
Security Group
→ 리소스 단위
→ stateful
→ allow 중심

NACL
→ subnet 단위
→ stateless
→ allow/deny
```

처음에는 Security Group을 먼저 확실히 이해하고, NACL은 subnet 전체에 적용되는 추가 방화벽으로 이해하면 된다.

## 13. 운영 장애 분석 흐름

### 큰 순서

사이트가 안 열릴 때 아래 순서로 좁혀간다.

```text
1. DNS
2. Routing
3. Firewall / Security Group / NACL
4. TCP
5. TLS
6. HTTP
7. Reverse Proxy
8. Container / Application
9. Database / External API
```

### DNS 확인

증상:

```text
도메인을 찾을 수 없음
예전 IP로 접속됨
특정 환경에서만 접속 안 됨
```

확인:

```bash
dig api.example.com
nslookup api.example.com
```

봐야 할 것:

```text
원하는 ALB 또는 IP로 해석되는가?
TTL이 너무 긴가?
resolver마다 결과가 다른가?
```

### Routing 확인

증상:

```text
같은 VPC 내부는 되는데 인터넷이 안 됨
private subnet EC2가 패키지 다운로드를 못 함
ALB target이 unhealthy
```

확인:

```text
Route Table에 0.0.0.0/0 경로가 있는가?
public subnet은 Internet Gateway를 가리키는가?
private subnet은 NAT Gateway를 가리키는가?
VPC local route가 있는가?
```

### Firewall 확인

증상:

```text
포트가 안 열림
connection timeout
ALB health check 실패
SSH 접속 실패
```

확인:

```text
Security Group inbound
Security Group outbound
NACL inbound
NACL outbound
OS firewall
서버 프로세스 listen 여부
```

### TCP 확인

증상:

```text
connection refused
connection timed out
```

확인:

```bash
nc -vz example.com 443
curl -v http://127.0.0.1:8080/health
```

판단:

```text
connection refused
→ 포트에 프로세스가 없거나 거절

connection timed out
→ 방화벽, 라우팅, 네트워크 경로 문제 가능
```

### TLS 확인

증상:

```text
인증서 오류
브라우저 보안 경고
특정 도메인만 HTTPS 실패
```

확인:

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
```

봐야 할 것:

```text
인증서 도메인이 맞는가?
만료되지 않았는가?
인증서 체인이 정상인가?
SNI가 맞는가?
```

### HTTP 확인

증상:

```text
404
405
413
429
500
502
503
504
```

확인:

```bash
curl -v https://api.example.com/health
curl -I https://api.example.com
```

판단:

```text
404
→ path, Host, location, backend route 확인

413
→ request body size 제한 확인

502
→ Nginx upstream 연결 문제 확인

503
→ 사용 가능한 target이 없는지 확인

504
→ backend 응답 지연 확인
```

### Nginx / Container 확인

확인:

```bash
nginx -t
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
docker ps
docker logs backend
docker port backend
```

봐야 할 것:

```text
Nginx 설정 문법이 정상인가?
요청이 access.log에 찍히는가?
error.log에 upstream 오류가 있는가?
active container가 떠 있는가?
Nginx proxy_pass 포트와 container host port가 맞는가?
```

## 14. 지금 흐름에서 우선순위

남은 네트워크를 모두 같은 무게로 볼 필요는 없다.

Nginx, Docker, AWS 배포 흐름과 직접 연결되는 우선순위는 아래가 높다.

```text
1. Routing Table / Default Route
2. Internet Gateway / NAT Gateway
3. Security Group / NACL
4. DNS 장애 분석
5. TCP connection refused / timeout
6. HTTP status code 분석
7. TLS termination / 인증서 / SNI
8. ARP
9. UDP
10. HTTP/2, HTTP/3
```

ARP와 UDP도 중요하지만 지금 당장 배포와 클라우드 운영에서는 라우팅, NAT, 방화벽, DNS, TCP, HTTP/TLS가 더 자주 나온다.

## 최종 정리

```text
Routing Table은 목적지 IP 대역별로 다음 hop을 정하는 규칙표다.
Default Route는 더 구체적인 경로가 없을 때 사용하는 기본 경로이며 보통 0.0.0.0/0으로 표현한다.
AWS Public Subnet과 Private Subnet은 Route Table 차이로 구분된다.
Internet Gateway는 VPC와 인터넷을 연결한다.
NAT Gateway는 private subnet 리소스가 인터넷으로 나갈 수 있게 한다.
ARP는 같은 네트워크 안에서 IP를 MAC 주소로 바꾸는 과정이다.
DNS는 도메인을 IP나 다른 도메인으로 해석하고 TTL과 캐시가 중요하다.
TCP는 연결 지향 통신이며 connection refused와 timeout을 구분해야 한다.
UDP는 연결 없이 빠르게 보내는 프로토콜이며 DNS, 실시간 통신, HTTP/3와 연결된다.
HTTP는 method, path, Host, status code를 기준으로 분석한다.
HTTPS는 HTTP 전에 TLS handshake와 인증서 검증이 필요하다.
Security Group은 리소스 단위 stateful 방화벽이고, NACL은 subnet 단위 stateless 방화벽이다.
장애 분석은 DNS → Routing → Firewall → TCP → TLS → HTTP → Proxy → Application 순서로 좁혀간다.
```
