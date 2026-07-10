# 2026-07-10 AWS 네트워크 심화: VPC, Subnet, Route Table, SG, NACL

## 핵심 관점

AWS 네트워크는 IP, subnet, routing, firewall 개념을 클라우드 리소스로 구현한 것이다.

기본 구조:

```text
VPC
→ Subnet
→ Route Table
→ Internet Gateway / NAT Gateway
→ Security Group / NACL
→ EC2 / ALB / RDS
```

백엔드 배포에서 자주 보는 구조:

```text
User
→ Route 53
→ ALB in Public Subnet
→ EC2 in Private Subnet
→ RDS in Private Subnet
```

## 1. VPC

VPC는 AWS 안에 만드는 가상 네트워크다.

예:

```text
VPC CIDR: 10.0.0.0/16
```

이 VPC 안에서 subnet을 나눈다.

```text
public subnet a:  10.0.1.0/24
public subnet c:  10.0.2.0/24
private subnet a: 10.0.11.0/24
private subnet c: 10.0.12.0/24
```

VPC CIDR은 나중에 VPN, VPC Peering, Transit Gateway를 쓸 때 겹치지 않게 잡는 것이 중요하다.

## 2. Subnet

Subnet은 VPC CIDR을 더 작게 나눈 네트워크 구간이다.

Subnet은 하나의 Availability Zone에 속한다.

예:

```text
ap-northeast-2a public subnet
ap-northeast-2c public subnet
```

고가용성을 위해 보통 최소 2개 AZ에 subnet을 둔다.

```text
ALB
→ 2개 이상의 public subnet에 배치

EC2 Auto Scaling Group
→ 2개 이상의 private subnet에 배치
```

## 3. Public Subnet과 Private Subnet

Subnet이 public인지 private인지는 이름이 아니라 route table로 결정된다.

Public subnet:

```text
0.0.0.0/0 → Internet Gateway
```

Private subnet:

```text
0.0.0.0/0 → NAT Gateway
```

또는 외부로 나가지 않는 subnet:

```text
0.0.0.0/0 경로 없음
```

중요:

```text
Public subnet에 있다고 무조건 인터넷에서 접근 가능한 것은 아니다.
Public IP, Security Group, NACL, 서버 listen 상태도 필요하다.
```

## 4. Route Table

Route Table은 subnet에서 나가는 패킷의 목적지를 보고 어디로 보낼지 결정한다.

기본 local route:

```text
10.0.0.0/16 → local
```

의미:

```text
VPC 내부 대역은 VPC 내부에서 통신한다.
```

Public subnet route table:

```text
Destination   Target
10.0.0.0/16   local
0.0.0.0/0     Internet Gateway
```

Private subnet route table:

```text
Destination   Target
10.0.0.0/16   local
0.0.0.0/0     NAT Gateway
```

## 5. Internet Gateway

Internet Gateway는 VPC와 인터넷을 연결한다.

Public subnet에서 인터넷으로 나가거나, 인터넷에서 public IP를 가진 리소스로 들어올 때 필요하다.

조건:

```text
VPC에 Internet Gateway attach
Route Table에 0.0.0.0/0 → IGW
리소스에 public IP 또는 ALB 같은 public endpoint
Security Group 허용
NACL 허용
```

ALB를 public subnet에 두는 이유:

```text
사용자 인터넷 요청을 받아야 하므로
```

EC2를 private subnet에 두는 이유:

```text
사용자가 EC2에 직접 접근하지 못하게 하고 ALB를 통해서만 접근하게 하려고
```

## 6. NAT Gateway

NAT Gateway는 private subnet 리소스가 인터넷으로 나갈 수 있게 한다.

예:

```text
Private EC2
→ NAT Gateway
→ Internet Gateway
→ Internet
```

용도:

```text
패키지 설치
외부 API 호출
Docker image pull
OS update
```

NAT Gateway는 public subnet에 둔다.

Private subnet route table은 NAT Gateway를 가리킨다.

```text
0.0.0.0/0 → NAT Gateway
```

주의:

```text
NAT Gateway는 외부 사용자가 private EC2로 들어오는 입구가 아니다.
밖으로 나가기 위한 경로다.
```

## 7. Security Group

Security Group은 리소스 단위 방화벽이다.

특징:

```text
stateful
allow 규칙만 존재
응답 트래픽 자동 허용
EC2, ALB, RDS 등에 붙음
```

권장 구조:

```text
ALB SG
- inbound 80 from 0.0.0.0/0
- inbound 443 from 0.0.0.0/0

App EC2 SG
- inbound app port from ALB SG
- inbound 22 from 내 IP/32 또는 Bastion SG

RDS SG
- inbound 3306 from App EC2 SG
```

SG끼리 참조하면 IP가 바뀌어도 구조를 유지할 수 있다.

## 8. NACL

NACL은 subnet 단위 방화벽이다.

특징:

```text
stateless
allow와 deny 규칙 존재
inbound와 outbound를 각각 설정
규칙 번호 순서대로 평가
```

Security Group과 차이:

```text
Security Group
→ 리소스 단위
→ stateful

NACL
→ subnet 단위
→ stateless
```

대부분의 초반 운영에서는 Security Group을 중심으로 보고, NACL은 subnet 전체 차단이나 보안 요구사항이 있을 때 더 자세히 본다.

## 9. ALB와 Target Group

ALB는 L7 로드밸런서다.

```text
Client
→ ALB
→ Target Group
→ EC2 / IP / Lambda
```

구성:

```text
Listener
→ 80, 443 포트에서 요청 수신

Rule
→ Host, Path 조건으로 Target Group 선택

Target Group
→ 트래픽을 받을 대상 묶음

Health Check
→ 대상이 정상인지 확인
```

예:

```text
api.example.com/* → api target group
admin.example.com/* → admin target group
```

## 10. Health Check

ALB Target Group은 health check로 정상 target을 판단한다.

예:

```text
Path: /health
Port: traffic port
Success code: 200
```

실패 원인:

```text
EC2 Security Group이 ALB 요청을 막음
앱이 해당 port에서 listen하지 않음
/health path가 없음
앱 시작이 느림
Nginx가 backend로 proxy_pass 실패
```

Health check 실패 시 ALB는 해당 target으로 트래픽을 보내지 않는다.

## 11. Route 53과 ALB

도메인은 Route 53에서 ALB로 연결할 수 있다.

```text
api.example.com
→ Alias
→ ALB DNS Name
```

ALB는 IP가 바뀔 수 있다.

따라서 ALB IP를 직접 A Record에 넣는 것이 아니라 Alias를 사용한다.

## 12. ACM과 HTTPS

ACM은 AWS Certificate Manager다.

ALB에 HTTPS를 붙일 때 인증서를 ACM에서 발급받아 연결할 수 있다.

구조:

```text
Client
→ HTTPS
→ ALB with ACM certificate
→ HTTP
→ EC2 / Nginx / Backend
```

이 경우 TLS termination은 ALB에서 일어난다.

Backend가 원래 요청이 HTTPS였다는 것을 알아야 하면:

```http
X-Forwarded-Proto: https
```

를 처리해야 한다.

## 13. VPC Endpoint

VPC Endpoint는 인터넷을 거치지 않고 AWS 서비스에 private하게 접근하는 기능이다.

예:

```text
Private EC2
→ VPC Endpoint
→ S3
```

NAT Gateway 없이도 특정 AWS 서비스에 접근할 수 있다.

종류:

```text
Gateway Endpoint
→ S3, DynamoDB

Interface Endpoint
→ PrivateLink 기반 서비스
```

처음에는 NAT Gateway와 VPC Endpoint의 목적 차이만 알아두면 된다.

```text
NAT Gateway
→ 인터넷으로 나가기 위한 경로

VPC Endpoint
→ AWS 서비스에 private하게 접근
```

## 14. 장애 상황별 확인

### EC2가 인터넷으로 나가지 못함

확인:

```text
Subnet route table에 0.0.0.0/0 경로가 있는가?
Public subnet이면 IGW를 가리키는가?
Private subnet이면 NAT Gateway를 가리키는가?
NAT Gateway가 public subnet에 있는가?
Security Group outbound가 허용되어 있는가?
NACL outbound/inbound가 허용되어 있는가?
```

### ALB health check 실패

확인:

```text
Target Group health check path
Target Group port
EC2 Security Group inbound from ALB SG
Nginx 또는 app listen port
서버 내부 curl /health
Nginx error.log
```

### 외부에서 웹 접속 안 됨

확인:

```text
Route 53 레코드
ALB listener 80/443
ALB Security Group inbound
Target Group health
EC2 Security Group
Nginx 또는 app 상태
```

## 최종 정리

```text
VPC는 AWS 안의 가상 네트워크다.
Subnet은 VPC를 AZ 단위로 나눈 네트워크 구간이다.
Public/Private subnet은 route table로 결정된다.
Internet Gateway는 VPC와 인터넷을 연결한다.
NAT Gateway는 private subnet 리소스가 밖으로 나가게 한다.
Security Group은 리소스 단위 stateful 방화벽이다.
NACL은 subnet 단위 stateless 방화벽이다.
ALB는 Listener, Rule, Target Group, Health Check로 구성된다.
Route 53 Alias는 도메인을 ALB에 연결할 때 적합하다.
ACM 인증서를 ALB에 붙이면 HTTPS 운영이 편해진다.
```
