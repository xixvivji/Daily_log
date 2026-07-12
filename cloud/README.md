# Cloud

AWS를 중심으로 cloud infrastructure의 개념, 서비스 선택 기준, architecture와 실제 배포 흐름을 정리하는 공간이다.

## Backend와 연결되는 목표

```text
Spring Boot application 구현
→ Docker image 생성
→ AWS에 compute 구성
→ RDS 연결
→ ALB와 HTTPS 적용
→ monitoring과 scaling 구성
```

서비스 이름을 외우는 것이 아니라 요청과 데이터가 어디를 지나고, 장애가 났을 때 어느 계층을 확인할지 설명하는 것을 목표로 한다.

## 학습 문서 순서

```text
01. Cloud와 AWS 전체 구조
02. AWS Global Infrastructure
03. IAM과 권한 관리
04. EC2와 Compute
05. EBS, S3와 Storage
06. RDS와 Database
07. VPC와 AWS Network
08. ALB와 Auto Scaling
09. Route 53, ACM, CloudFront
10. ECR과 ECS
11. CloudWatch와 운영 Monitoring
12. 고가용성, Backup, Disaster Recovery
13. AWS Security
14. AWS CI/CD 서비스
15. Terraform과 IaC
16. 비용 관리
```

## 지금 먼저 추가할 내용

```text
1. Cloud와 AWS 전체 구조
2. Region, Availability Zone, 계정과 Resource 관계
3. IAM User, Role, Policy
4. EC2 instance, AMI, Security Group, Key Pair
5. Spring Boot를 EC2에 배포하는 전체 흐름
```

AWS Network는 기존 `infrastructure/`의 VPC, Subnet, Route Table 문서를 재사용하고 cloud architecture 관점에서 연결한다.

## 처음에는 뒤로 미룰 내용

```text
EKS와 Kubernetes 운영
Multi-account Landing Zone
Transit Gateway 대규모 설계
Direct Connect
Global multi-region active-active
복잡한 Serverless event architecture
```

기본 배포와 운영을 경험한 뒤 필요할 때 확장한다.
