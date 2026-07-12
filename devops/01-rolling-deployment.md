# 01. Rolling Deployment 실전

전체 전략의 차이와 선택 기준은 [배포 전략 비교](03-deployment-strategies.md)에서 함께 비교한다.

## Rolling Deployment란 무엇인가?

실행 중인 instance나 container를 한 번에 모두 교체하지 않고 일정 개수씩 새 버전으로 바꾸는 배포 전략이다.

```text
v1 v1 v1 v1
→ v2 v1 v1 v1
→ v2 v2 v1 v1
→ v2 v2 v2 v1
→ v2 v2 v2 v2
```

새 버전과 이전 버전이 동시에 traffic을 처리하는 시간이 존재한다.

## Rolling을 기본 전략으로 쓰는 이유

```text
전체 환경 두 벌이 필요하지 않음
일시적인 추가 resource만으로 무중단 가능
Kubernetes와 ECS가 기본 기능으로 지원
교체 속도와 가용성을 parameter로 조절 가능
```

하지만 새 버전이 일부 사용자에게 바로 노출되고 rollback도 교체 과정이 필요하므로 Canary나 Blue/Green과 위험 제어 방식이 다르다.

## 필요한 전제

```text
동시에 여러 instance가 실행됨
Load Balancer 또는 Service가 healthy instance에만 routing
application이 instance local state에 의존하지 않음
v1과 v2가 같은 DB/API/message를 함께 사용할 수 있음
readiness와 graceful shutdown이 정확함
```

단일 instance에서는 하나를 내리고 하나를 올리므로 일반적인 Rolling의 가용성 장점을 얻기 어렵다.

## Kubernetes RollingUpdate

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: member-api
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: member-api
  template:
    metadata:
      labels:
        app: member-api
    spec:
      containers:
        - name: member-api
          image: example/member-api:2.0.0
          ports:
            - containerPort: 8080
```

## maxSurge

원래 replica보다 추가로 생성할 수 있는 Pod 수 또는 비율이다.

```text
replicas: 4
maxSurge: 1
→ 배포 중 최대 5개 Pod 가능
```

값이 크면 새 Pod를 병렬로 많이 띄워 배포가 빨라질 수 있지만 CPU와 memory 여유가 필요하다.

## maxUnavailable

배포 중 사용할 수 없어도 되는 Pod 수 또는 비율이다.

```text
replicas: 4
maxUnavailable: 0
→ 기존 capacity를 줄이지 않고 새 Pod가 ready된 뒤 이전 Pod 종료
```

값이 크면 resource 여유가 적어도 교체할 수 있지만 요청 처리 capacity가 감소할 수 있다.

## Capacity 계산

```text
replicas 10
maxSurge 20%
maxUnavailable 10%

최대 실행 수 → 12개
최소 available → 9개
```

설정값뿐 아니라 cluster에 실제 새 Pod를 배치할 CPU와 memory가 있는지 확인한다. 여유가 없으면 새 Pod가 Pending이고 기존 Pod도 종료하지 못해 배포가 멈출 수 있다.

## Readiness Probe

새 Pod가 traffic을 받을 준비가 됐는지 판단한다.

```yaml
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

Process가 실행됐다는 것과 요청을 정상 처리할 준비가 됐다는 것은 다르다.

```text
Spring Context 초기화
DB connection 준비
필수 cache/config loading
HTTP port listen
```

준비되지 않았는데 readiness가 성공하면 배포 중 5xx가 발생한다. 반대로 일시적인 외부 dependency 실패를 너무 엄격하게 연결하면 모든 Pod가 traffic에서 제외될 수 있다.

## Startup과 Liveness

```text
startupProbe
→ 시작이 느린 application에 초기화 시간 제공

livenessProbe
→ 복구 불가능한 상태인지 판단하고 재시작

readinessProbe
→ 현재 traffic 수신 가능 여부 판단
```

DB가 잠깐 느리다는 이유로 liveness가 실패하면 모든 Pod가 동시에 재시작되는 장애가 생길 수 있다.

## Graceful Shutdown

이전 Pod를 traffic에서 제외했다고 진행 중 요청이 즉시 끝나는 것은 아니다.

```text
Pod 종료 시작
→ readiness false
→ Service endpoint에서 제거
→ 새 요청 중단
→ 진행 중 요청 완료 대기
→ application 종료
```

```yaml
terminationGracePeriodSeconds: 30
containers:
  - name: member-api
    lifecycle:
      preStop:
        exec:
          command: ["sh", "-c", "sleep 5"]
```

`preStop` sleep만 복사해서 쓰기보다 endpoint 전파 지연, request 최대 처리 시간과 Spring graceful shutdown 설정을 함께 맞춘다.

## Connection Draining

Load Balancer가 target을 deregister한 뒤 일정 시간 기존 connection과 요청을 처리하게 한다.

주의 대상:

```text
긴 HTTP 요청
WebSocket
SSE
gRPC stream
대용량 upload/download
```

종료 유예 시간이 너무 짧으면 배포 때 connection reset이 발생하고, 너무 길면 배포와 scale-in이 느려진다.

## ECS Rolling Update

ECS는 `minimumHealthyPercent`와 `maximumPercent`로 배포 중 task 수를 제어한다.

```text
desiredCount: 4
minimumHealthyPercent: 100
maximumPercent: 200

최소 healthy task → 4
최대 running task → 8
```

`maximumPercent`가 낮고 cluster capacity가 부족하면 새 task를 먼저 시작할 수 없으며, `minimumHealthyPercent` 때문에 기존 task도 중지하지 못해 배포가 정체될 수 있다.

Deployment Circuit Breaker를 사용하면 새 task가 steady state에 도달하지 못하는 배포를 실패로 표시하고 마지막 완료 배포로 rollback하도록 구성할 수 있다.

## Version 동시 운영

Rolling 중에는 다음 조합이 모두 가능해야 한다.

```text
v1 client → v2 server
v2 client → v1 server
v1 consumer와 v2 producer
v2 consumer와 v1 producer
v1/v2 application → 같은 DB schema
```

## DB Expand-Contract

하위 호환 schema 변경 방법이다.

```text
1. Expand
→ 새 column/table 추가
→ 기존 column 유지

2. Migrate
→ 새 application이 old/new schema 모두 처리
→ 기존 data backfill

3. Switch
→ 모든 instance가 새 schema 사용

4. Contract
→ 이전 column과 compatibility code 제거
```

배포와 동시에 column rename/delete를 하면 아직 실행 중인 v1이 실패할 수 있다.

## Session, Cache, File

```text
Session
→ Redis/Spring Session 또는 stateless 구조

Cache
→ v1/v2가 같은 key와 serialization을 이해하는가?

File
→ Pod local disk가 아니라 공유 object storage 사용
```

Java class를 그대로 Redis에 직렬화하면 version 변경 중 역직렬화 오류가 날 수 있다. Versioned schema나 JSON compatibility를 고려한다.

## Message Consumer Rolling

HTTP server뿐 아니라 Kafka/RabbitMQ consumer도 Rolling 대상이다.

```text
처리 중 message ack 전에 종료
→ redelivery 가능

새 event field 추가
→ v1 consumer도 읽을 수 있어야 함

consumer group rebalance
→ 일시적인 처리 지연
```

Consumer는 idempotent하고 shutdown 시 polling을 멈춘 뒤 처리 중 message와 offset/ack를 정리해야 한다.

## Rollback

Kubernetes:

```bash
kubectl rollout status deployment/member-api
kubectl rollout history deployment/member-api
kubectl rollout undo deployment/member-api
```

Rollback도 이전 image로 다시 Rolling하는 과정이다. 이미 새 version이 DB data를 비호환 형태로 변경했으면 application rollback만으로 복구되지 않는다.

## 자동 실패 판단

```text
새 Pod가 Ready되지 않음
Deployment progress deadline 초과
5xx 증가
p95/p99 latency 증가
Pod restart와 OOM 증가
DB connection/lock 증가
business success rate 감소
```

Kubernetes 기본 Deployment는 application metric을 보고 자동 rollback하는 progressive delivery controller가 아니다. CI/CD나 Argo Rollouts 같은 도구와 metric gate를 연결해야 한다.

## 자주 발생하는 실패

```text
latest tag 재사용으로 어떤 image인지 불명확
resource 부족으로 새 Pod Pending
readiness가 너무 빨리 성공
graceful shutdown 없이 진행 중 요청 종료
DB schema가 v1과 비호환
새 version이 message schema 변경
config/secret 누락
rollback image가 registry에서 삭제됨
```

## Rolling 배포 Checklist

```text
Immutable image tag 또는 digest인가?
새 version이 old schema와 호환되는가?
readiness가 실제 traffic 준비를 검증하는가?
종료 유예와 connection draining이 맞는가?
maxSurge만큼 resource 여유가 있는가?
PDB와 node disruption이 배포를 막지 않는가?
배포 metric과 alert가 준비됐는가?
rollback image와 절차가 검증됐는가?
```

## 공식 참고 자료

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Amazon ECS Rolling Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html)
- [ECS Deployment Circuit Breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)

## 설명할 때 핵심 문장

```text
Rolling Deployment는 여러 instance를 일정 수씩 교체해 추가 resource를 줄이면서 무중단을 목표로 하는 전략이다.
배포 중 v1과 v2가 동시에 실행되므로 DB, API, cache, message schema가 양방향 호환되어야 한다.
안전한 Rolling은 maxSurge 설정보다 readiness, capacity, graceful shutdown, connection draining과 metric 기반 실패 판단이 중요하다.
```
