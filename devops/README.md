# DevOps

Build, Test, 배포, infrastructure 변경과 운영 관측을 자동화하는 방법을 정리하는 공간이다.

DevOps를 특정 도구 이름이 아니라 개발 변경을 빠르고 안전하게 production까지 전달하고 복구하는 과정으로 본다.

## 영역 구분

```text
Backend
→ application 기능과 business logic

Infrastructure
→ network, server, proxy, container 기반

Cloud
→ AWS resource와 managed service

DevOps
→ CI/CD, IaC, 배포 자동화, monitoring, 운영 절차
```

## 학습 문서 순서

```text
01. DevOps와 Software Delivery 전체 구조
02. Git Branch, Pull Request, Release 전략
03. Gradle Build와 Artifact
04. Docker Image Build와 Registry
05. GitHub Actions CI
06. CD와 환경별 배포
07. Secret과 Configuration 관리
08. Terraform과 IaC
09. Monitoring, Logging, Alert
10. Blue/Green, Rolling, Canary 자동화
11. Kubernetes 기본 운영
12. Kubernetes 배포와 Network
13. Redis 운영
14. Kafka와 RabbitMQ 운영
15. Incident Response와 Runbook
16. 비용과 운영 효율
```

## Kafka와 RabbitMQ의 위치

```text
backend/21-messaging-outbox.md
→ Producer, Consumer, Event, Idempotency, Outbox

devops의 Messaging 운영 문서
→ Broker, Partition, Replica, Queue, Storage, Lag, Monitoring, Upgrade
```

사용 방법과 운영 방법을 분리해 중복을 줄인다.

## 지금 먼저 추가할 내용

Cloud에서 Spring Boot를 한 번 수동 배포한 다음 아래 순서로 진행한다.

```text
1. Gradle test와 build 자동화
2. Docker image build
3. GitHub Actions CI
4. ECR push와 EC2 또는 ECS 배포
5. Health Check와 실패 rollback
6. CloudWatch 또는 Prometheus metric 연결
7. Terraform으로 resource 재현
```

수동 배포 과정을 모른 채 자동화부터 만들면 실패 지점을 이해하기 어렵다. 한 번 수동으로 성공한 절차를 반복 가능하게 자동화한다.

## 현재 작성 완료

```text
01. Rolling Deployment 실전
02. Canary와 Progressive Delivery 실전
```

기존 단일 EC2 Blue/Green 사례와 함께 비교하고, 이후 CI/CD와 Monitoring 문서에서 자동 promotion과 rollback으로 연결한다.
