# 2026-07-10 DNS 심화: Resolver, Record, TTL, Route 53

## 핵심 관점

DNS는 도메인 이름을 실제 접속 대상으로 바꿔주는 시스템이다.

```text
api.example.com
→ IP 주소
또는
→ ALB DNS name
```

서버와 애플리케이션이 정상이어도 DNS가 잘못되면 사용자는 접속하지 못한다.

DNS를 볼 때 핵심 질문은 아래다.

```text
도메인이 어떤 대상으로 해석되는가?
그 응답은 어디에서 온 것인가?
TTL 때문에 캐시가 남아 있는가?
Route 53 레코드 타입이 적절한가?
ALB를 IP로 직접 연결하고 있지는 않은가?
```

## 1. DNS가 필요한 이유

사용자는 IP 주소보다 도메인을 사용한다.

```text
https://api.example.com
```

브라우저는 이 도메인으로 바로 서버에 연결하지 못한다.

먼저 DNS를 통해 접속할 주소를 알아내야 한다.

```text
api.example.com
→ DNS 조회
→ 203.0.113.10
→ TCP 연결
→ TLS handshake
→ HTTP 요청
```

AWS ALB를 쓰는 경우:

```text
api.example.com
→ my-alb-123.ap-northeast-2.elb.amazonaws.com
→ ALB가 관리하는 IP들
```

## 2. DNS 조회 흐름

DNS 조회는 여러 캐시와 서버를 거친다.

```text
브라우저 캐시
→ OS 캐시
→ hosts 파일
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
→ .com TLD DNS 위치 알려줌

.com TLD DNS
→ example.com authoritative DNS 위치 알려줌

example.com authoritative DNS
→ api.example.com 레코드 응답
```

일반 사용자는 이 과정을 직접 하지 않는다.

대부분 recursive resolver가 대신 처리한다.

```text
Google DNS: 8.8.8.8
Cloudflare DNS: 1.1.1.1
ISP DNS
회사 내부 DNS
```

## 3. Recursive Query와 Iterative Query

Recursive Query:

```text
클라이언트가 resolver에게 최종 답을 요청한다.
resolver가 root, TLD, authoritative DNS를 따라가며 대신 답을 찾는다.
```

Iterative Query:

```text
DNS 서버가 최종 답을 모르면 다음에 물어볼 DNS 서버를 알려준다.
```

일반적으로:

```text
내 PC → recursive resolver
recursive resolver → root/TLD/authoritative DNS
```

라고 이해하면 된다.

## 4. Authoritative DNS

Authoritative DNS는 특정 도메인에 대한 최종 권한을 가진 DNS 서버다.

예:

```text
example.com의 DNS 설정을 Route 53 Hosted Zone에서 관리
```

그러면 Route 53의 authoritative DNS가 `example.com`의 최종 답을 가진다.

```text
api.example.com → ALB
www.example.com → CloudFront
```

DNS 문제를 볼 때는 recursive resolver가 캐시한 값과 authoritative DNS의 원본 값이 다를 수 있다는 점을 기억해야 한다.

## 5. Record Type

### A Record

A Record는 도메인을 IPv4 주소로 연결한다.

```text
api.example.com → 203.0.113.10
```

고정 IP를 가진 서버에 연결할 때 사용할 수 있다.

단, ALB는 IP가 바뀔 수 있으므로 ALB IP를 A Record에 직접 넣는 방식은 적절하지 않다.

### AAAA Record

AAAA Record는 도메인을 IPv6 주소로 연결한다.

```text
api.example.com → 2001:db8::1
```

IPv6를 사용할 때 필요하다.

### CNAME

CNAME은 도메인을 다른 도메인 이름으로 연결한다.

```text
www.example.com → example.com
```

또는:

```text
app.example.com → my-service.vendor.com
```

주의:

```text
CNAME은 루트 도메인 apex에 쓰기 어렵거나 제한되는 경우가 많다.
example.com 같은 apex에는 Route 53 Alias를 자주 쓴다.
```

### MX Record

MX Record는 메일 서버를 지정한다.

```text
example.com → mail server
```

웹 서비스 접속과는 직접 관련이 적지만 도메인 운영에서 중요하다.

### TXT Record

TXT Record는 텍스트 값을 저장한다.

자주 쓰이는 곳:

```text
도메인 소유권 검증
SPF
DKIM
DMARC
서비스 인증
```

## 6. Route 53 Alias

Route 53 Alias는 AWS 리소스에 도메인을 연결할 때 자주 사용한다.

예:

```text
api.example.com
→ Alias
→ ALB
```

장점:

```text
ALB IP가 바뀌어도 Route 53이 알아서 처리
apex domain에도 사용 가능
AWS 리소스와 자연스럽게 연결
```

예:

```text
example.com
→ Alias
→ CloudFront
```

또는:

```text
api.example.com
→ Alias
→ ALB
```

## 7. TTL

TTL은 Time To Live다.

DNS 응답을 얼마나 오래 캐시해도 되는지 나타낸다.

```text
TTL 300
→ 300초 동안 캐시 가능
```

TTL이 길면:

```text
DNS 서버 부하 감소
응답 속도 개선
변경 반영이 늦음
```

TTL이 짧으면:

```text
변경 반영이 빠름
DNS 조회가 더 자주 발생
```

운영에서 도메인을 옮기기 전에는 TTL을 미리 낮추는 경우가 많다.

```text
변경 하루 전 TTL 3600 → 60
DNS 변경
정상 확인
TTL 다시 300 또는 3600
```

## 8. DNS Propagation

DNS propagation은 DNS 변경이 여러 resolver 캐시에 퍼지는 과정을 말한다.

정확히는 DNS가 중앙에서 전파된다기보다, 각 resolver 캐시가 TTL에 따라 갱신되는 것이다.

그래서 사용자마다 다른 결과를 볼 수 있다.

```text
사용자 A resolver: 새 IP
사용자 B resolver: 이전 IP 캐시
```

증상:

```text
내 컴퓨터에서는 새 서버로 접속
다른 사람은 예전 서버로 접속
회사망에서는 안 됨
모바일망에서는 됨
```

## 9. DNS 장애 유형

### Could not resolve host

도메인을 IP로 바꾸지 못한 상황이다.

원인:

```text
도메인 오타
레코드 없음
Hosted Zone 설정 오류
네임서버 위임 오류
resolver 장애
```

확인:

```bash
dig api.example.com
nslookup api.example.com
```

### NXDOMAIN

도메인이 존재하지 않는다는 응답이다.

원인:

```text
레코드가 없음
도메인 이름 오타
Hosted Zone이 잘못됨
네임서버 위임이 안 됨
```

### SERVFAIL

DNS 서버가 응답을 처리하지 못한 상태다.

원인:

```text
authoritative DNS 문제
DNSSEC 문제
resolver 문제
```

### 이전 IP로 접속됨

DNS 캐시 가능성이 높다.

확인:

```text
TTL
브라우저 캐시
OS 캐시
recursive resolver 캐시
```

## 10. Route 53에서 확인할 것

Route 53을 사용할 때 봐야 할 것:

```text
Hosted Zone이 올바른 도메인인가?
도메인 등록기관의 NS가 Route 53 NS로 위임되어 있는가?
A, CNAME, Alias 레코드가 올바른가?
ALB를 Alias로 연결했는가?
TTL이 의도한 값인가?
public hosted zone과 private hosted zone을 혼동하지 않았는가?
```

Public Hosted Zone:

```text
인터넷에서 조회 가능한 DNS 영역
```

Private Hosted Zone:

```text
VPC 내부에서만 조회 가능한 DNS 영역
```

Private Hosted Zone에만 레코드를 만들면 인터넷 사용자에게는 조회되지 않는다.

## 11. DNS 확인 명령어

기본 조회:

```bash
dig api.example.com
```

특정 resolver로 조회:

```bash
dig @8.8.8.8 api.example.com
dig @1.1.1.1 api.example.com
```

레코드 타입 지정:

```bash
dig api.example.com A
dig api.example.com CNAME
dig example.com NS
dig example.com MX
```

짧게 출력:

```bash
dig +short api.example.com
```

추적:

```bash
dig +trace api.example.com
```

## 12. DNS와 장애 분석

사이트가 안 열릴 때 DNS부터 볼지 판단하는 기준:

```text
브라우저가 도메인을 찾을 수 없다고 함
curl에서 Could not resolve host
특정 네트워크에서만 다른 IP로 감
도메인 변경 직후 문제 발생
Route 53 레코드 변경 직후 문제 발생
```

DNS가 정상이라면 그다음은 TCP 연결을 본다.

```text
DNS 조회 성공
→ IP 또는 ALB 확인
→ TCP 80/443 연결 확인
→ TLS 확인
→ HTTP status 확인
```

## 최종 정리

```text
DNS는 도메인을 IP 또는 다른 도메인으로 해석한다.
recursive resolver는 클라이언트 대신 최종 답을 찾아준다.
authoritative DNS는 도메인의 원본 레코드를 가진다.
A Record는 IPv4, AAAA는 IPv6, CNAME은 다른 도메인 이름을 가리킨다.
Route 53 Alias는 ALB, CloudFront 같은 AWS 리소스 연결에 적합하다.
TTL 때문에 DNS 변경은 즉시 모든 사용자에게 반영되지 않을 수 있다.
DNS 장애는 NXDOMAIN, SERVFAIL, 캐시 문제, 네임서버 위임 오류로 나눠 볼 수 있다.
```
