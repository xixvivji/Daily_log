# 02. AWS Global Infrastructure

## 왜 알아야 하는가?

Region과 AZ 선택은 resource 이름을 고르는 작업이 아니다.

```text
사용자 latency
법적 data 위치
서비스와 기능 제공 여부
비용
가용성
재해 복구
```

이 기준을 결정한다.

## Region

Region은 특정 지리 영역의 독립적인 AWS infrastructure 집합이다.

```text
서울 Region
→ ap-northeast-2

도쿄 Region
→ ap-northeast-1
```

대부분의 resource와 data는 사용자가 선택한 Region에 생성된다. 다른 Region resource를 자동으로 함께 조회하거나 복제한다고 가정하면 안 된다.

## Region 선택 기준

```text
Latency
→ 주요 사용자와 가까운가?

Compliance
→ data residency와 규제 요구를 만족하는가?

Service Availability
→ 필요한 AWS 서비스와 instance type이 제공되는가?

Cost
→ 같은 서비스도 Region별 가격 차이가 있는가?

Disaster Recovery
→ 보조 Region 전략이 필요한가?
```

개발팀과 가까운 Region보다 실제 사용자와 업무 규정이 우선일 수 있다.

## Availability Zone

AZ는 Region 안에서 다른 AZ의 장애 영향을 줄이도록 설계된 하나 이상의 data center 집합이다.

```text
Region
├─ Availability Zone A
├─ Availability Zone B
└─ Availability Zone C
```

AZ들은 low-latency network로 연결되지만 물리적으로 격리되어 있다. AZ 사이 traffic에도 비용과 latency가 발생할 수 있다.

## AZ Name과 AZ ID

`ap-northeast-2a` 같은 AZ name은 account마다 같은 물리 위치를 뜻하지 않을 수 있다. Cross-account에서 같은 물리 AZ를 맞춰야 하면 AZ ID를 확인한다.

```text
AZ Name → account에 표시되는 이름
AZ ID   → 물리 AZ를 일관되게 식별
```

## Subnet과 AZ

Subnet은 하나의 AZ에 속한다.

```text
VPC 10.0.0.0/16
├─ public-a  10.0.1.0/24 → AZ A
├─ public-b  10.0.2.0/24 → AZ B
├─ private-a 10.0.11.0/24 → AZ A
└─ private-b 10.0.12.0/24 → AZ B
```

Multi-AZ application을 만들려면 여러 AZ에 subnet을 준비하고 compute를 실제로 분산한다.

## Single-AZ와 Multi-AZ

Single-AZ:

```text
비용과 구성이 단순
학습·개발 환경에 적합
해당 AZ 장애 시 서비스 중단 가능
```

Multi-AZ:

```text
AZ 장애 시 다른 AZ에서 처리 가능
Load Balancer와 compute 분산 필요
Database failover 구성 필요
비용과 운영 복잡도 증가
```

ALB만 여러 AZ에 두고 application은 한 AZ에만 두면 application AZ 장애를 견디지 못한다.

## Multi-AZ 요청 흐름

```text
사용자
→ Route 53
→ ALB: AZ A / AZ B
→ Application: AZ A / AZ B
→ RDS Multi-AZ
```

Health Check가 실패한 target으로 traffic을 보내지 않아야 하고, application session과 file을 local instance에만 저장하지 않아야 한다.

## Edge Location

Edge Location은 사용자 가까이에서 DNS, CDN, 보안과 같은 edge service를 제공하는 지점이다.

```text
Route 53 DNS
CloudFront CDN
AWS WAF 연계
```

Region에 application이 있고 Edge에서 cache된 정적 content를 제공하면 사용자 latency와 origin traffic을 줄일 수 있다.

Edge Location은 일반 EC2를 배치하는 AZ와 같은 개념이 아니다.

## Regional Edge Cache와 Origin

```text
사용자
→ CloudFront Edge
→ Regional Cache 계층
→ S3 또는 ALB Origin
```

실제 동작과 지원 범위는 CloudFront 설정에 따라 다르지만 핵심은 사용자 가까운 cache가 origin 요청을 줄이는 것이다.

## Local Zone과 Outposts

```text
Local Zone
→ 특정 대도시 가까이 compute/storage 일부를 확장해 낮은 latency 제공

Outposts
→ AWS infrastructure와 service를 customer on-premises 위치에 배치
```

일반적인 웹 백엔드 첫 배포에는 필요하지 않다. 매우 낮은 latency, data locality, hybrid 요구가 있을 때 검토한다.

## Global Service와 Regional Service

```text
IAM
→ account 전체에서 사용하는 global 성격

EC2, RDS, VPC, ALB
→ Region 선택 필요

Subnet, EC2, EBS
→ 특정 AZ와 연결

S3
→ bucket Region 선택, AZ 하나에 직접 귀속되지 않음

Route 53
→ global DNS service
```

Console에서 Region을 바꿨는데 EC2가 사라져 보이는 이유는 다른 Region의 resource 목록을 보고 있기 때문이다.

## 고가용성과 재해 복구

```text
High Availability
→ 주로 같은 Region의 여러 AZ로 일상 장애 대응

Disaster Recovery
→ Region 전체 또는 큰 사고에 대비한 복구 전략
```

Multi-Region은 비용과 data consistency, DNS 전환, 배포, secret, monitoring이 모두 복잡해진다. 요구되는 RTO와 RPO가 없으면 필요 이상으로 구성하지 않는다.

```text
RTO
→ 장애 후 서비스를 복구해야 하는 목표 시간

RPO
→ 허용 가능한 data 손실 시점
```

## Multi-Region 기본 Pattern

```text
Backup and Restore
→ 평소 비용 낮음, 복구 시간 길 수 있음

Pilot Light
→ 핵심 data와 최소 component 유지

Warm Standby
→ 축소된 서비스가 보조 Region에서 실행

Active-Active
→ 여러 Region이 동시에 traffic 처리
→ 가장 복잡하고 비용이 큼
```

처음에는 Multi-AZ를 정확히 구성하고 backup 복구를 검증하는 것이 우선이다.

## Region 간 Data 이동

다른 Region으로 data가 자동 복제되지 않는 서비스를 구분한다.

```text
S3 Cross-Region Replication
RDS cross-Region read replica 또는 snapshot copy
ECR replication
DynamoDB Global Tables
```

각 기능은 지연, 비용, encryption key, failover 절차가 다르다.

## 장애 Scenario

### EC2 한 대 장애

```text
Auto Scaling이 새 instance 생성
ALB Health Check가 비정상 target 제외
```

### AZ 장애

```text
다른 AZ의 application target으로 traffic
RDS Multi-AZ failover
```

### Region 장애

```text
별도 Region resource와 data가 준비되어 있어야 함
DNS 또는 global traffic 전환
```

각 단계는 자동이 아닐 수 있으므로 실제 failover test와 runbook이 필요하다.

## Architecture Checklist

```text
Resource가 어느 Region과 AZ에 있는가?
한 AZ에만 의존하는 component가 있는가?
AZ별 subnet CIDR이 겹치지 않는가?
Load Balancer에 여러 AZ가 연결됐는가?
State가 instance local disk에만 있는가?
Database backup과 restore를 test했는가?
Region 선택 이유와 data 위치 요구가 문서화됐는가?
Cross-AZ/Region 비용을 확인했는가?
```

## 공식 참고 자료

- [AWS Regions and Availability Zones](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)
- [AWS Organizations Multi-account Best Practices](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices.html)

## 설명할 때 핵심 문장

```text
Region은 지리적 배포 단위이고 AZ는 Region 안의 장애 격리 단위다.
고가용성은 여러 AZ에 component를 실제로 분산하고 traffic과 data failover를 구성해야 얻을 수 있다.
Edge Location은 사용자 가까이에서 DNS와 CDN 기능을 제공하며 일반 AZ와 역할이 다르다.
```
