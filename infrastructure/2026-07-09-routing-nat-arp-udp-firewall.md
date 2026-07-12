# 2026-07-09 Routing, NAT, ARP, UDP, Firewall 심화

## 문서 범위

이 문서는 다른 전용 문서와 겹치지 않는 네트워크 전달 핵심을 묶는다.

```text
Routing
→ 목적지까지 어느 경로로 보낼지 결정

ARP
→ 같은 LAN에서 다음 장비의 MAC 주소 확인

NAT
→ packet의 IP 주소와 port 변환

UDP
→ 연결 설정 없이 datagram 전달

Firewall
→ packet 또는 connection 허용 여부 결정
```

다음 내용은 별도 문서에서 다룬다.

- [IP, Subnet Mask, CIDR](2026-07-08-ip-subnet-mask-cidr.md)
- [TCP 심화](2026-07-10-tcp-deep-dive.md)
- [DNS 심화](2026-07-10-dns-deep-dive.md)
- [HTTP와 HTTPS 심화](2026-07-10-http-https-deep-dive.md)
- [AWS Network 심화](2026-07-10-aws-network-deep-dive.md)
- [네트워크 장애 분석](2026-07-10-network-troubleshooting-practice.md)

## 1. Routing

Routing은 목적지 IP로 packet을 보내기 위해 다음 hop과 network interface를 선택하는 과정이다.

```text
목적지 IP 확인
→ routing table에서 가장 구체적인 경로 검색
→ next hop 또는 직접 연결 network 결정
→ 해당 interface로 packet 전송
```

대표 routing table:

```text
Destination       Gateway         Interface
192.168.0.0/24    directly        en0
10.0.0.0/8        192.168.0.2     en0
0.0.0.0/0         192.168.0.1     en0
```

목적지가 `192.168.0.20`이면 직접 연결 경로를 사용한다. `10.20.30.40`이면 `192.168.0.2`로 보내고, 어느 경로에도 해당하지 않으면 default route를 사용한다.

### Longest Prefix Match

여러 route가 일치하면 CIDR prefix가 가장 긴, 즉 가장 구체적인 경로를 선택한다.

```text
0.0.0.0/0
10.0.0.0/8
10.10.0.0/16
10.10.20.0/24
```

목적지 `10.10.20.15`에는 네 경로가 모두 일부 일치하지만 `/24`가 선택된다.

### Default Route

`0.0.0.0/0`은 모든 IPv4 목적지와 일치하는 가장 넓은 경로다.

```text
내 subnet 경로 없음
더 구체적인 route 없음
→ default gateway로 전달
```

default route가 없으면 같은 network 밖으로 packet을 보낼 수 없다. route가 있어도 gateway까지 도달할 수 없으면 전송은 실패한다.

### Routing과 HTTP Routing의 차이

```text
Network routing
→ IP와 CIDR 기준
→ router, host routing table, AWS route table

HTTP routing
→ Host, path, header, method 기준
→ Nginx, ALB, Ingress, API Gateway
```

둘 다 대상을 선택하지만 판단 계층과 입력값이 다르다.

## 2. ARP

Ethernet LAN에서 실제 frame을 보내려면 다음 장비의 MAC 주소가 필요하다. ARP는 IPv4 주소에 대응하는 MAC 주소를 찾는다.

같은 subnet으로 보낼 때:

```text
내 IP: 192.168.0.10
상대 IP: 192.168.0.20

ARP: 192.168.0.20의 MAC 주소는 누구인가?
응답: 192.168.0.20은 aa:bb:cc:dd:ee:ff다
```

다른 subnet으로 보낼 때는 최종 목적지의 MAC 주소가 아니라 gateway의 MAC 주소를 찾는다.

```text
IP destination: 8.8.8.8
Ethernet destination: 192.168.0.1 gateway의 MAC
```

router를 지날 때 IP destination은 계속 최종 목적지를 가리키지만, Ethernet frame의 source와 destination MAC은 hop마다 바뀐다.

### ARP Cache

매번 broadcast하면 비효율적이므로 확인한 mapping을 일정 시간 cache한다.

```bash
arp -a
```

ARP 문제의 대표 증상:

```text
같은 subnet의 특정 host만 통신 불가
중복 IP 때문에 MAC mapping이 계속 변경
gateway ARP 응답을 받지 못함
오래된 ARP cache가 잘못된 장비를 가리킴
```

ARP는 IPv4 LAN의 개념이다. IPv6에서는 Neighbor Discovery가 비슷한 역할을 한다.

## 3. NAT와 Port Translation

NAT는 packet header의 source 또는 destination IP를 바꾸는 기술이다. 일반적인 가정용 router와 cloud NAT Gateway는 private source IP를 외부 통신 가능한 주소로 변환한다.

```text
내부 요청
192.168.0.10:53000 → 203.0.113.10:443

NAT 이후
198.51.100.20:62001 → 203.0.113.10:443
```

NAT 장비는 mapping을 기억한다.

```text
198.51.100.20:62001
↔ 192.168.0.10:53000
```

응답이 돌아오면 mapping을 이용해 내부 host로 전달한다. 여러 내부 host가 하나의 public IP를 공유하려면 port까지 함께 변환하는 PAT 또는 NAPT가 사용된다.

### SNAT와 DNAT

```text
SNAT
→ source address 변경
→ private host의 outbound internet 접근

DNAT
→ destination address 변경
→ public address로 온 요청을 내부 server에 전달
```

Docker의 host port mapping도 destination 변환 관점으로 볼 수 있다.

```text
host 8080 요청
→ container 172.17.0.2:8080
```

### NAT가 보안 장비는 아니다

외부에서 내부 주소를 직접 지정하기 어렵게 만들 수 있지만, NAT 자체의 목적은 주소 변환이다. 접근 통제는 Security Group, NACL, host firewall 같은 정책으로 명시해야 한다.

### AWS NAT Gateway

private subnet instance가 internet으로 나가야 하지만 internet에서 직접 들어오는 연결은 받지 않게 할 때 사용한다.

```text
Private instance
→ private subnet route table
→ NAT Gateway
→ Internet Gateway
→ Internet
```

NAT Gateway는 public subnet에 위치하고 Elastic IP를 사용한다. private subnet의 `0.0.0.0/0` route가 NAT Gateway를 가리켜야 한다.

## 4. UDP

UDP는 TCP처럼 connection을 먼저 만들지 않고 datagram을 보낸다.

```text
TCP
→ handshake
→ 순서, 재전송, 흐름 제어 제공

UDP
→ handshake 없음
→ protocol 자체는 전달, 순서, 중복 제거를 보장하지 않음
```

UDP가 아무 기능도 없다는 뜻은 아니다. application protocol이 필요한 신뢰성과 재전송을 직접 구현할 수 있다.

대표 사용:

```text
DNS query
실시간 음성과 영상
게임 state update
QUIC와 HTTP/3의 transport 기반
```

DNS도 응답이 크거나 zone transfer가 필요하면 TCP를 사용할 수 있다. “DNS는 항상 UDP”라고 외우면 안 된다.

UDP 장애 확인:

```bash
nc -uv example.com 53
sudo tcpdump -n udp
```

UDP에는 TCP의 `connection refused`, handshake 상태만으로 판단하는 방법을 그대로 적용할 수 없다. 요청과 응답 packet을 직접 관찰하거나 application timeout을 확인해야 한다.

## 5. Firewall, Security Group, NACL

Firewall은 source, destination, protocol, port, connection state 등을 기준으로 traffic을 허용하거나 차단한다.

```text
source IP
destination IP
TCP 또는 UDP
source port
destination port
connection state
```

### Stateful과 Stateless

Stateful firewall은 허용된 요청의 connection state를 기억하고 응답 traffic을 자동으로 허용할 수 있다.

Stateless firewall은 inbound와 outbound를 각각 평가하므로 양방향 규칙을 모두 고려해야 한다.

AWS 기준:

```text
Security Group
→ instance 또는 network interface 단위
→ stateful
→ allow rule만 사용

NACL
→ subnet 단위
→ stateless
→ allow와 deny rule 사용
→ 낮은 rule number부터 평가
```

### 공개 Port 판단

```text
80, 443
→ 공개 web service라면 internet 허용 가능

22
→ SSH 원격 관리 port
→ 0.0.0.0/0 공개보다 관리 IP, VPN, SSM 사용 권장

3306, 5432
→ DB port
→ application Security Group에서만 접근 허용
```

SSH는 암호화된 원격 shell, file transfer, port forwarding을 제공한다. 터널링에 사용할 수 있지만 22번 port 자체를 단순히 “터널링 port”라고 부르는 것은 부정확하다.

## 6. 계층을 연결한 요청 흐름

```text
1. application이 목적지 IP와 port 결정
2. host routing table이 next hop 선택
3. ARP로 같은 LAN의 next-hop MAC 확인
4. firewall이 packet 허용 여부 판단
5. NAT 경로라면 IP와 port 변환
6. router가 다음 network로 전달
7. 목적지에서 reverse path를 통해 응답
```

웹 요청에서는 그 위에 TCP, TLS, HTTP가 이어진다.

```text
Routing/ARP
→ TCP connection
→ TLS handshake
→ HTTP request
→ reverse proxy routing
→ application
```

## 7. 장애 분석 순서

```text
1. 목적지 IP와 subnet이 맞는가?
2. routing table에 더 구체적인 route가 있는가?
3. default route와 next hop이 정상인가?
4. 같은 LAN이면 ARP mapping이 만들어지는가?
5. NAT mapping과 return path가 존재하는가?
6. firewall의 inbound와 outbound가 허용되는가?
7. TCP인지 UDP인지에 맞는 방식으로 확인했는가?
```

명령어 예시:

```bash
ip route
route -n get 8.8.8.8
arp -a
traceroute example.com
nc -vz example.com 443
sudo tcpdump -nn host 203.0.113.10
```

운영체제에 따라 지원하는 option과 명령어가 다르므로 결과의 의미를 중심으로 본다.

## 최종 정리

```text
Routing은 다음 경로를 선택한다.
ARP는 IPv4 LAN에서 next-hop MAC을 찾는다.
NAT는 IP와 port를 변환하며 firewall과 목적이 다르다.
UDP는 connection 없이 datagram을 전달한다.
Firewall은 명시적인 traffic 허용 정책을 적용한다.
```

이 개념들은 따로 움직이지 않는다. 실제 packet 한 개가 routing, ARP, firewall, NAT를 차례로 거친 뒤 TCP·TLS·HTTP 같은 상위 protocol 처리로 이어진다.
