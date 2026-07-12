# 01. Cloud와 AWS 전체 구조

## Cloud란 무엇인가?

Cloud Computing은 compute, storage, database, network 같은 IT resource를 필요할 때 API로 생성하고 사용량에 따라 비용을 지불하는 방식이다.

```text
On-Premises
→ 직접 서버와 network 장비 구매
→ data center 공간, 전원, 냉각, 교체까지 직접 관리

Cloud
→ provider가 물리 infrastructure 운영
→ 사용자는 account 안에서 논리 resource 생성
→ API, Console, CLI, IaC로 관리
```

Cloud를 단순히 다른 회사 컴퓨터를 빌리는 것으로만 보면 부족하다. 빠른 provisioning, API 기반 자동화, managed service, 탄력적 확장이 핵심이다.

## Cloud의 주요 특성

```text
On-Demand
→ 필요한 시점에 resource 생성

Elasticity
→ traffic에 따라 확장과 축소

Measured Usage
→ 사용 시간, 요청, 저장량, 전송량 등으로 비용 계산

Resource Pooling
→ provider infrastructure를 여러 customer가 논리적으로 분리해 사용

API-Driven
→ 사람이 console에서 클릭한 작업도 내부적으로 API 호출
```

resource를 빨리 만들 수 있다는 것은 잘못 만든 resource와 비용도 빨리 증가할 수 있다는 뜻이다. 권한, tag, budget, IaC와 삭제 정책이 필요하다.

## IaaS, PaaS, SaaS

```text
IaaS
→ VM, network, disk 같은 기반 resource 제공
→ EC2, EBS, VPC

PaaS / Managed Platform
→ application 실행 환경과 운영 기능 제공
→ Elastic Beanstalk, App Runner 등

Managed Service
→ 특정 middleware나 database 운영 일부를 provider가 담당
→ RDS, ElastiCache, MSK

SaaS
→ 완성된 software를 서비스로 사용
→ email, collaboration tool 등
```

AWS 서비스는 책임 범위가 서로 다르다. EC2에서는 OS patch를 사용자가 관리하지만 더 managed된 서비스에서는 provider가 더 많은 계층을 담당한다.

## AWS Account

AWS Account는 resource, 권한, quota, 비용의 중요한 경계다.

```text
AWS Account
├─ IAM identity와 policy
├─ Region별 resource
├─ Billing과 Cost
├─ Service Quota
└─ CloudTrail audit event
```

작은 학습 환경은 한 account로 시작할 수 있지만 production과 development를 account로 분리하면 권한, 비용, quota, 장애 영향을 격리하기 쉽다.

Root user는 account 생성 시 만들어지는 최고 권한 identity다. 일상 작업에 사용하지 않고 MFA를 적용하며 root access key를 만들지 않는 것이 기본이다.

## Resource란 무엇인가?

AWS에서 생성하고 관리하는 대상이다.

```text
EC2 instance
S3 bucket
RDS database
VPC
Subnet
Security Group
IAM Role
Load Balancer
```

많은 resource는 ARN으로 식별할 수 있다.

```text
arn:partition:service:region:account-id:resource
```

서비스마다 ARN 구조와 region/account 포함 여부가 다를 수 있다.

## Region과 Availability Zone

```text
Region
→ 독립된 지리적 AWS infrastructure 영역
→ ap-northeast-2 같은 code 사용

Availability Zone
→ Region 내부의 격리된 infrastructure 위치
→ 한 Region에 여러 AZ 존재
```

Region은 latency, 규제, 서비스 제공 여부와 비용에 영향을 준다. AZ를 여러 개 사용하면 한 AZ 장애에 대한 가용성을 높일 수 있다.

```text
Region: ap-northeast-2
├─ AZ A
├─ AZ B
└─ AZ C
```

Multi-AZ라고 자동으로 가용해지는 것은 아니다. application, load balancer, database, subnet을 여러 AZ에 배치하고 상태와 traffic이 실제로 전환되는지 확인해야 한다.

## Resource 범위

AWS resource는 scope가 다르다.

```text
Global 성격
→ IAM, Route 53 같은 서비스의 일부 기능

Regional
→ VPC, RDS, ALB 등

Availability Zone 범위
→ Subnet, EC2 instance, EBS volume 등
```

EBS volume과 EC2 instance를 연결하려면 일반적으로 같은 AZ에 있어야 한다. S3 bucket은 특정 Region에 만들지만 AZ 하나에 직접 속하지 않는다.

## AWS 핵심 서비스 지도

```text
Identity
→ IAM, IAM Identity Center, Organizations

Compute
→ EC2, Lambda, ECS, EKS

Storage
→ S3, EBS, EFS

Database
→ RDS, Aurora, DynamoDB, ElastiCache

Network
→ VPC, Subnet, Route Table, IGW, NAT Gateway

Traffic
→ ALB, NLB, Route 53, CloudFront

Security
→ KMS, Secrets Manager, WAF, GuardDuty

Operations
→ CloudWatch, CloudTrail, Config, Systems Manager

Messaging
→ SQS, SNS, EventBridge, MSK, Amazon MQ
```

처음부터 모든 서비스를 공부할 필요는 없다. Spring Boot 배포 기준으로 IAM, EC2, VPC, EBS/S3, RDS, ALB, Route 53, ACM, CloudWatch를 먼저 연결한다.

## Shared Responsibility Model

```text
AWS: Security OF the Cloud
→ data center, 물리 hardware, 기반 network, virtualization 계층

Customer: Security IN the Cloud
→ IAM 권한, data, OS와 application, Security Group, 암호화 설정
```

서비스 형태에 따라 경계가 달라진다.

```text
EC2
→ 사용자가 guest OS patch, middleware, application 관리

RDS
→ AWS가 database infrastructure와 일부 patch/backup 기능 제공
→ 사용자는 account, schema, query, network access, data 보호 관리

S3
→ AWS가 storage infrastructure 운영
→ 사용자는 bucket policy, object 권한, lifecycle, data 관리
```

Managed Service를 쓰면 책임이 사라지는 것이 아니라 관리 대상의 위치가 달라진다.

## Control Plane과 Data Plane

```text
Control Plane
→ resource 생성, 수정, 삭제, 설정
→ EC2 RunInstances, Security Group 변경

Data Plane
→ 생성된 resource가 실제 traffic과 data를 처리
→ EC2의 HTTP 요청, S3 object GET
```

IAM과 CloudTrail을 볼 때 어떤 API action이 control plane 변경인지, application data access인지 구분하면 감사와 장애 분석이 쉬워진다.

## Console, CLI, SDK, IaC

```text
Management Console
→ 사람이 browser로 조작, 학습과 확인에 편함

AWS CLI
→ terminal에서 API 호출, 반복 작업 자동화

AWS SDK
→ application code에서 AWS API 사용

Infrastructure as Code
→ Terraform, CloudFormation, CDK 등으로 resource 선언과 변경 이력 관리
```

처음에는 Console로 구조를 확인하되 같은 환경을 반복 생성해야 하면 IaC로 이동한다.

## Tag

```text
Name=member-api-prod
Environment=prod
Service=member
Owner=backend-team
CostCenter=study
```

Tag는 검색, 비용 분류, 자동화와 권한 조건에 사용할 수 있다. 생성 후 이름을 기억하는 수준이 아니라 조직 전체 naming/tagging 규칙을 정한다.

## Spring Boot 기본 배포 Architecture

```text
사용자
→ Route 53
→ ALB
→ Public Subnet의 Load Balancer
→ Private Subnet의 EC2/ECS Application
→ Private Subnet의 RDS
```

학습 초기에는 단일 EC2에 배포해 전체 흐름을 이해한 뒤 ALB, private subnet, multi-AZ로 확장한다.

```text
1단계: EC2 + Public IP + Spring Boot
2단계: Nginx 또는 ALB + HTTPS
3단계: RDS 분리
4단계: Private Subnet과 NAT
5단계: Auto Scaling 또는 ECS
6단계: Monitoring, Backup, IaC
```

## Cloud 비용의 기본

비용은 instance 가격만 보면 안 된다.

```text
Compute 실행 시간
Storage 용량과 IOPS
Database instance와 backup
Load Balancer 시간과 처리량
NAT Gateway 시간과 data 처리
Internet data transfer
Log 저장과 조회
Public IPv4
```

학습 resource는 사용 후 중지 또는 삭제하고 Budget과 비용 알림을 먼저 설정한다. EC2를 중지해도 EBS, Elastic IP, snapshot 같은 resource 비용이 남을 수 있다.

## 첫 학습 환경 Checklist

```text
Root user MFA
일상 작업용 identity 구성
Budget과 비용 알림
기본 Region 결정
CloudTrail 확인
Naming과 Tag 규칙
불필요한 access key 생성 금지
resource 생성 후 삭제 절차 확인
```

## 흔한 오해

```text
Cloud면 자동으로 무중단이다.
→ 여러 AZ와 복구 구성을 직접 설계해야 함

Private Subnet이면 모든 공격에서 안전하다.
→ IAM, application 취약점, outbound, data 보호가 여전히 필요

Managed Service면 운영할 것이 없다.
→ 설정, 용량, backup, monitoring, 비용은 관리해야 함

Auto Scaling이면 느린 query도 해결된다.
→ database와 downstream 병목은 별도
```

## 공식 참고 자료

- [AWS Account](https://docs.aws.amazon.com/accounts/latest/reference/accounts-welcome.html)
- [AWS Shared Responsibility Model](https://docs.aws.amazon.com/whitepapers/latest/aws-risk-and-compliance/shared-responsibility-model.html)
- [AWS Regions](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)

## 설명할 때 핵심 문장

```text
Cloud는 IT resource를 API로 필요할 때 생성하고 탄력적으로 사용하는 운영 방식이다.
AWS Account는 resource, 권한, 비용과 quota의 중요한 경계이고 Region과 AZ는 위치와 장애 격리 단위다.
AWS가 물리 infrastructure를 운영해도 고객은 IAM, network 설정, application과 data 보안을 책임진다.
```
