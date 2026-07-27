# 04. Amazon ECS와 ALB 배포 실전

Amazon ECS에서 HTTP/HTTPS application을 운영할 때의 구조와 Rolling, Blue/Green, Canary 배포를 ALB traffic 흐름을 중심으로 정리한다.

## 전체 구조

```text
Client
→ Route 53 Alias
→ Public Subnet의 Internet-facing ALB
→ HTTPS Listener :443 / ACM Certificate
→ Listener Rule
→ Target Group
→ Private Subnet의 ECS Task
→ RDS, ElastiCache, 외부 API
```

ALB는 둘 이상의 public subnet에, ECS Task는 보통 private subnet에 둔다. Fargate Task가 ECR image pull, CloudWatch Logs 전송, 외부 API 호출을 하려면 NAT Gateway 또는 필요한 VPC endpoint가 있어야 한다. ALB에서 Task로 가는 요청은 NAT가 아니라 VPC 내부 경로를 사용한다.

## ECS 핵심 Resource

### Cluster

Service와 Task가 실행되는 논리적 경계다. Fargate에서 server를 직접 관리하지 않아도 Task가 어느 Cluster에 속하는지는 명확하다.

### Task Definition

Container 실행 명세이자 revision이 있는 template이다.

```text
image URI와 digest/tag
CPU와 memory
container port
environment와 secret
log driver와 health check
Task Execution Role과 Task Role
network mode
```

수정하면 새 revision이 생긴다. 기존 Task가 자동으로 바뀌는 것은 아니며 Service를 새 revision으로 update해야 배포가 시작된다.

### Task와 Service

Task는 Task Definition revision을 실제로 실행한 instance다. Service는 원하는 Task 수를 유지하고 배포, load balancer 등록, 장애 복구를 담당한다.

```text
desiredCount: 4
→ 정상 Task 4개 유지
→ Task가 죽으면 새 Task 시작
→ 새 Task Definition으로 Service update 시 배포 시작
```

Service Auto Scaling은 `desiredCount`를 조절하고 ECS scheduler가 실제 Task 수를 맞춘다.

## ECS와 ALB 연결 관계

```text
ALB
└─ Listener :443
   └─ Rule: host=api.example.com, path=/api/*
      └─ Forward Action
         └─ Target Group
            ├─ 10.0.1.21:8080
            ├─ 10.0.2.34:8080
            └─ 10.0.1.57:8080
```

ECS Service에 Target Group ARN, container name, container port를 지정하면 ECS가 Task 시작과 종료에 맞춰 target 등록과 해제를 관리한다.

ALB가 매 요청마다 ECS API로 Task를 조회하는 구조가 아니다. ECS가 Task endpoint를 Target Group에 등록하고, ALB는 그중 healthy target으로 요청을 보낸다.

## ALB 구성 요소

### Load Balancer와 Listener

ALB는 여러 AZ의 subnet에 연결되는 Layer 7 진입점이다. Listener는 protocol과 port를 정의한다.

```text
Listener :80
→ HTTPS :443 redirect

Listener :443
→ ACM certificate로 TLS termination
→ Listener Rule 평가
```

### Listener Rule

요청 조건과 action을 연결하고 priority 순서로 평가한다.

```text
Host api.example.com + Path /members/*
→ member-api Target Group

Host api.example.com + Path /orders/*
→ order-api Target Group
```

### Target Group

실제 traffic을 받을 target 집합과 health 정책을 가진다.

```text
target type
protocol / port
health check path와 threshold
deregistration delay
stickiness
```

Fargate와 `awsvpc` network mode에서는 각 Task가 ENI와 private IP를 가지므로 target type을 `ip`로 설정해야 한다. `instance`는 EC2 instance 자체를 target으로 등록하는 방식이라 `awsvpc` Task와 맞지 않는다.

서비스마다 고유 Target Group을 사용하는 것이 안전하다. 여러 Service가 하나를 공유하면 한 Service의 배포 중 target 등록과 해제가 다른 Service에 영향을 줄 수 있다.

## 요청이 Task까지 가는 과정

```text
1. Client가 api.example.com 조회
2. Route 53 Alias가 ALB를 가리킴
3. ALB :443 Listener가 TLS 종료
4. Listener Rule이 host와 path 조건 평가
5. Forward Action이 Target Group 선택
6. ALB가 healthy Task IP:port 선택
7. Task Security Group을 통과해 container port로 전달
8. 응답이 ALB를 거쳐 Client로 반환
```

ALB DNS name은 고정 IP를 보장하지 않는다. Route 53에서는 ALB IP를 직접 기록하지 말고 Alias로 연결한다.

## Security Group 설계

```text
ALB Security Group
inbound 443 ← client CIDR
outbound 8080 → ECS Task Security Group

ECS Task Security Group
inbound 8080 ← ALB Security Group
outbound 443 → 필요한 endpoint
outbound DB port → DB Security Group

RDS Security Group
inbound 3306/5432 ← ECS Task Security Group
```

Task port를 인터넷 전체에 열 필요가 없다. Health Check도 ALB에서 Task로 들어오므로 Task SG가 ALB SG의 container port 접근을 허용해야 한다.

## Health Check 세 계층

### Container Health Check

Task Definition에 정의하며 container 내부에서 command를 실행한다. ECS가 container 자체 상태를 판단하는 signal이다.

### ALB Target Group Health Check

ALB가 network를 통해 Task endpoint를 호출한다. 실제 traffic 경로의 port, SG, application 응답을 함께 검증하며 healthy target에만 정상적으로 traffic을 보낸다.

### ECS Service 배포 판단

Load Balancer를 쓰고 container health check도 정의했다면 ECS는 container health와 Target Group health를 모두 통과해야 Task를 healthy capacity로 센다.

`healthCheckGracePeriodSeconds`는 시작이 느린 application의 초기 실패를 ECS가 일정 시간 무시하게 한다. Health Check 자체를 끄는 값은 아니며 너무 길면 실제 실패 발견도 늦어진다.

```text
liveness
→ process가 복구 불가능하게 멈췄는가?

readiness
→ 지금 신규 요청을 받을 준비가 됐는가?
```

Readiness에서 모든 외부 dependency를 필수 검사하면 일시적 DB 장애가 모든 Task를 동시에 target에서 제거하는 연쇄 장애를 만들 수 있다. 신규 요청 처리에 정말 필수인 조건만 선택한다.

새 target은 첫 성공 health check 후 healthy가 될 수 있다. 이미 unhealthy였던 target의 회복에는 configured healthy threshold가 적용되므로 두 경우를 구분한다.

## Rolling Deployment

```text
v1 Task 4개
→ v2 Task 시작
→ container와 ALB health 통과
→ v1 Task deregister와 종료
→ 반복
→ v2 Task 4개
```

```text
desiredCount: 4
minimumHealthyPercent: 100
maximumPercent: 200
```

배포 중 최소 healthy Task는 4개, 최대 running Task는 8개다. Fargate quota 또는 EC2 cluster capacity에 여유가 있어야 새 Task를 먼저 시작할 수 있다.

Deployment Circuit Breaker와 rollback을 활성화하면 새 배포가 steady state에 도달하지 못할 때 마지막 완료 배포로 돌아가게 할 수 있다. DB나 message가 비호환으로 바뀌었다면 application rollback만으로 data를 복구할 수 없다.

Rolling은 보통 같은 Target Group에서 v1과 v2가 잠시 공존한다. ALB weight로 버전별 비율을 제어하는 Canary와 다르다.

## ALB Weighted Target Groups

하나의 Listener Rule forward action에 여러 Target Group과 weight를 지정할 수 있다.

```text
stable Target Group weight: 90
canary Target Group weight: 10

90 : 10 → 약 90% : 10%
1 : 1   → 약 50% : 50%
10 : 20 → 약 33% : 67%
```

Weight는 상대값이다. 이 기능은 traffic 분배 mechanism일 뿐 완전한 배포 controller는 아니다.

```text
새 Task set 생성
health 확인
weight 단계 변경
metric 판정
실패 시 weight 복구
이전 Task 종료
```

이 작업은 별도 automation 또는 ECS/CodeDeploy managed deployment가 담당해야 한다. Target Group 하나가 비었거나 unhealthy여도 ALB가 그 weight를 다른 Target Group으로 자동 재분배하지 않을 수 있으므로 automation이 배포를 중단하고 weight를 복원해야 한다.

## ECS Canary 구조

```text
Stable/Blue Target Group
→ 현재 production Task

Canary/Green Target Group
→ 새 Task Definition revision의 Task

ALB Listener Rule
→ 두 Target Group 사이 traffic weight 변경
```

```text
100% Stable / 0% Green
→ 90% Stable / 10% Green
→ 관찰
→ 0% Stable / 100% Green
→ bake time
→ 이전 Task 종료
```

Canary가 항상 1%, 5%, 10%, 25%, 50%의 다단계를 지원한다고 단정하면 안 된다. Controller와 deployment configuration에 따라 단계 수가 다르다.

## 현재 선택 가능한 ECS 배포 방식

AWS에는 이름이 비슷한 방식이 공존하므로 deployment controller와 strategy를 같이 확인해야 한다.

### ECS Rolling Update

```text
deployment controller: ECS
strategy: ROLLING
```

한 Service의 Task를 점진 교체하는 일반적인 기본 방식이다.

### ECS Native Blue/Green, Linear, Canary

```text
deployment controller: ECS
strategy: BLUE_GREEN | LINEAR | CANARY
```

현재 ECS가 service revision, lifecycle stage, traffic shifting과 bake time을 직접 관리할 수 있다. ALB/NLB 또는 Service Connect에서는 managed traffic shifting을 구성할 수 있다.

Native Canary는 작은 비율을 Green으로 보낸 뒤 configured canary bake time 동안 관찰하고 나머지를 전환하는 2단계다.

```text
Step 1: configured percentage를 Green으로 이동
→ canary bake time 동안 검증
Step 2: Green 100%로 이동
→ final bake time과 cleanup
```

Lifecycle hook에 Lambda validation을 연결하거나 pause hook으로 승인을 기다릴 수 있다. CloudWatch alarm도 rollback 판단에 사용한다.

### CodeDeploy 기반 ECS Blue/Green

```text
deployment controller: CODE_DEPLOY
CodeDeploy Application + Deployment Group + AppSpec
```

기존에 널리 사용된 방식이다. CodeDeploy가 replacement Task Set을 만들고 두 Target Group 사이 production traffic을 전환한다.

```text
CodeDeployDefault.ECSCanary10Percent5Minutes
→ 10% 전환 → 5분 대기 → 나머지 90% 전환

CodeDeployDefault.ECSCanary10Percent15Minutes
→ 10% 전환 → 15분 대기 → 나머지 90% 전환

CodeDeployDefault.ECSLinear10PercentEvery1Minutes
→ 1분마다 10%씩 전환
```

필요 resource:

```text
CodeDeploy Application과 Deployment Group
두 Target Group
Production Listener와 선택적 Test Listener
AppSpec file
CodeDeploy Service Role
CloudWatch Alarm
선택적 lifecycle hook Lambda
```

CodeDeploy에서 Blue/Green은 두 환경을 운용하는 큰 배포 model이고 Canary, Linear, All-at-once는 production traffic 이동 방식이다. 따라서 AWS 문맥에서는 `Blue/Green과 Canary 중 하나만 선택한다`고 단순화하면 안 된다.

## Native ECS와 CodeDeploy 비교

| 구분 | ECS Native | CodeDeploy 기반 |
|---|---|---|
| Controller | `ECS` | `CODE_DEPLOY` |
| 시작 | ECS Service revision update | CodeDeploy deployment 생성 |
| 설정 중심 | ECS deployment configuration | Deployment Group + AppSpec |
| Traffic 전략 | Blue/Green, Linear, Canary | All-at-once, Linear, Canary |
| 검증 확장 | ECS lifecycle hook | CodeDeploy lifecycle hook |
| 운영 범위 | ECS에서 통합 관리 | CodeDeploy resource와 권한도 관리 |

새 구조에서는 Native 전략 지원 범위를 먼저 검토하고 기존 pipeline 호환, 필요한 hook, IaC 지원을 기준으로 선택한다. 기존 CodeDeploy Service는 controller 값만 바꿔 전환하면 안 되며 listener rule, 두 Target Group과 초기 weight를 포함한 migration이 필요하다.

## Production Listener와 Test Listener

```text
Production Listener :443
→ 실제 사용자 traffic

Test Listener :8443 또는 별도 rule
→ Green Task validation traffic
```

Test Listener로 production 전환 전에 Green smoke test를 수행할 수 있다. Port는 인터넷 전체가 아니라 CI runner나 운영 network만 접근하도록 제한한다. Test 통과만으로 실제 부하와 data 분포까지 검증되지는 않으므로 Canary metric gate는 여전히 필요하다.

## Canary 용량과 Stickiness

Traffic weight가 작아도 Green Task 한 개로 충분하다고 단정할 수 없다.

```text
peak traffic: 2,000 RPS
Canary weight: 10%
예상 traffic: 약 200 RPS
Task 안전 처리량: 80 RPS
→ 최소 3개 + 장애 여유
```

Weight는 장기적인 요청 분배의 근사값이다. WebSocket, 긴 connection, stickiness, 처리 시간 차이로 실제 load는 달라진다.

Weighted routing만 쓰면 한 사용자의 연속 요청이 v1과 v2로 갈릴 수 있다. Target Group stickiness는 이를 완화하지만 실제 비율 수렴, cookie, CORS, 장애 전환에 영향을 준다. Session을 Task memory에 저장해 stickiness로 버티기보다 stateless token이나 외부 session store를 사용한다.

특정 내부 사용자나 tenant는 host, path, HTTP header, source IP 조건의 별도 Rule로 보낼 수 있다. 외부 client가 임의로 보낼 수 있는 `X-Canary` header를 신뢰하려면 앞단 proxy가 검증 후 설정해야 한다.

## 관측성과 자동 중단 기준

ALB 전체 metric만 보면 Stable과 Canary를 구분하기 어렵다. Target Group, service revision, Task Definition 또는 application version별 signal을 분리한다.

```text
ALB/Target Group
→ RequestCount, Target 5xx, TargetResponseTime
→ HealthyHostCount / UnHealthyHostCount

ECS
→ running/pending Task, CPU/memory
→ lifecycle, rollback, stopped Task reason

Application
→ version별 error rate와 latency
→ DB timeout, 핵심 business 성공률
→ log와 trace의 version attribute
```

```text
최소 1,000 requests 이후
Canary 5xx > 1%
또는 Stable 대비 error rate 3배 초과
또는 p95 latency 30% 증가
또는 핵심 transaction 성공률 2%p 감소
또는 healthy Canary target이 최소 수 미만
→ 중단 후 Stable traffic 복구
```

시간만 기다리지 말고 최소 표본 수도 함께 본다.

## Connection Draining과 Graceful Shutdown

```text
1. 신규 traffic 대상에서 제외
2. 진행 중 요청 완료
3. application graceful shutdown
4. ECS stop timeout 안에 종료
5. 초과 시 강제 종료
```

ALB deregistration delay, ECS container stop timeout, application shutdown timeout을 서로 맞춘다. 긴 HTTP 요청, upload/download, WebSocket, SSE, gRPC stream과 message consumer는 별도 검증이 필요하다.

## DB와 Event 호환성

Rolling, Blue/Green, Canary 모두 v1과 v2가 동시에 실행될 수 있다.

```text
Expand → 새 column/table 추가, 기존 구조 유지
Migrate → 양쪽 version이 읽을 수 있게 backfill
Switch → 모든 workload가 새 구조 사용
Contract → 이전 구조와 compatibility code 제거
```

Canary traffic이 10%여도 새 version이 공용 DB나 event를 기존 consumer가 읽지 못하는 형태로 바꾸면 영향은 10%에 머물지 않는다. Rollback은 traffic과 application을 되돌릴 뿐 이미 발생한 결제, message, schema, data mutation을 취소하지 않으므로 data recovery runbook이 필요하다.

## 자주 발생하는 장애

### Target unhealthy

```text
Task가 RUNNING인가?
Application이 0.0.0.0:containerPort에 listen하는가?
containerName/containerPort mapping이 맞는가?
awsvpc Target Group이 ip type인가?
ALB SG → Task SG가 허용됐는가?
Health path와 success code가 맞는가?
grace period가 충분한가?
ALB subnet이 Task AZ를 포함하는가?
```

`localhost`에만 bind한 application은 Task ENI로 들어오는 ALB 요청을 받지 못한다.

### ALB 502 / 503 / 504

```text
502
→ target connection reset, port/protocol 불일치, 종료 중 연결 단절

503
→ usable healthy target 없음, 빈 Target Group에 weight 유지

504
→ DB/외부 API 지연, pool 고갈, ALB timeout 초과
```

### 배포가 멈춤

```text
Fargate quota 또는 EC2 capacity 부족
maximumPercent만큼 새 Task를 띄울 여유 없음
image pull, secret, IAM 실패
container 또는 ALB health 실패
CloudWatch alarm
Green steady state 실패
Auto Scaling과 deployment 동시 진행
```

ECS Service event, stopped Task reason, Target Health reason code, application log, ALB metric 순으로 확인한다.

## 구축 순서

```text
1. VPC와 public/private subnet
2. ALB와 Security Group
3. Target Group: ip type, app port, health path
4. HTTPS Listener와 ACM certificate
5. Task Execution Role과 Task Role
6. Task Definition
7. ECS Service와 Target Group mapping
8. desiredCount만큼 healthy target 확인
9. Route 53 Alias
10. log, metric, alarm, autoscaling
11. Rolling 또는 managed traffic strategy
12. rollback과 data recovery 훈련
```

## IAM Role 구분

```text
Task Execution Role
→ ECR image pull, CloudWatch Logs, startup secret

Task Role
→ application의 S3, SQS, DynamoDB 접근

ECS Service-linked/Infrastructure Role
→ target 등록·해제와 managed traffic shifting

CodeDeploy Service Role
→ CodeDeploy 방식의 listener와 ECS 제어
```

## 운영 Checklist

```text
[Network]
ALB가 필요한 AZ의 public subnet에 있는가?
Task에 필요한 outbound 경로가 있는가?
ALB SG와 Task SG가 최소 권한으로 연결됐는가?

[ECS/ALB]
Image가 immutable tag 또는 digest인가?
Execution Role과 Task Role이 분리됐는가?
awsvpc/Fargate Target Group이 ip type인가?
서비스별 Target Group을 분리했는가?
health와 graceful shutdown 설정이 맞는가?

[Deployment]
Controller와 strategy를 정확히 구분했는가?
Canary weight와 Green capacity가 맞는가?
version별 기술·business metric이 있는가?
자동 alarm, rollback, 수동 override가 있는가?
DB/API/Event가 v1/v2에 호환되는가?
data recovery 절차가 있는가?
```

## 설명할 때 핵심 문장

```text
ECS Service는 원하는 수의 Task를 유지하고 Task 시작과 종료에 맞춰 endpoint를 ALB Target Group에 등록하거나 해제한다.

Fargate는 awsvpc mode로 Task마다 ENI와 IP를 가지므로 Target Group target type으로 ip를 사용한다.

Rolling은 보통 같은 Target Group에서 Task를 점진 교체하고, Canary는 Stable과 Green Target Group 사이 traffic weight를 조절한다.

ALB weighted routing만으로 완전한 Canary가 되지는 않으며 Task 생성, health 검증, metric 판정, promotion, rollback을 맡을 controller가 필요하다.

ECS Native Canary와 CodeDeploy 기반 ECS Blue/Green의 Canary configuration이 공존하므로 controller와 strategy를 함께 확인해야 한다.
```

## 공식 참고 자료

- [Amazon ECS Service Load Balancing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html)
- [Application Load Balancer for Amazon ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/alb.html)
- [Amazon ECS Service Definition Parameters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service_definition_parameters.html)
- [Optimize Load Balancer Health Checks for ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/load-balancer-healthcheck.html)
- [Amazon ECS Deployment Controllers and Strategies](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_service-options.html)
- [Amazon ECS Canary Deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/canary-deployment.html)
- [Amazon ECS Blue/Green Deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-blue-green.html)
- [CodeDeploy Blue/Green Deployments for Amazon ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)
- [ALB Weighted Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-action-types.html)

