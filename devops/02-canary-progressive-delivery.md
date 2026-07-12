# 02. Canary와 Progressive Delivery 실전

전체 전략의 차이와 선택 기준은 [배포 전략 비교](03-deployment-strategies.md)에서 함께 비교한다.

## Canary Deployment란 무엇인가?

새 version에 일부 traffic만 보내 실제 환경에서 검증한 뒤 점진적으로 비율을 높이는 전략이다.

```text
v1 99% / v2 1%
→ v1 95% / v2 5%
→ v1 80% / v2 20%
→ v1 50% / v2 50%
→ v1 0%  / v2 100%
```

목표는 배포 자체가 아니라 문제가 있을 때 영향받는 사용자와 요청의 범위를 제한하는 것이다.

## Progressive Delivery

Software를 배포한 뒤 metric, 승인, 사용자 segment를 기준으로 노출 범위를 점진적으로 확대하는 운영 방식이다.

```text
Artifact 배포
→ 소량 traffic
→ 자동 분석
→ 승인 또는 중단
→ traffic 확대
→ 전체 전환
```

Canary와 Feature Flag를 함께 사용할 수 있다.

```text
Canary
→ 새 binary와 infrastructure 안정성 검증

Feature Flag
→ 특정 기능의 사용자 공개 제어
```

## Canary와 A/B Testing 차이

```text
Canary
→ 안정성 검증
→ error, latency, resource, business failure 관찰

A/B Testing
→ 제품 가설과 사용자 행동 비교
→ conversion, retention 같은 실험 metric 관찰
```

트래픽을 나눈다는 구현은 비슷하지만 성공 기준이 다르다.

## Canary에 필요한 조건

```text
v1과 v2를 동시에 운영 가능
traffic 비율 또는 사용자 segment routing 가능
version별 metric과 log 구분
충분한 요청 표본
자동 또는 명시적 중단 절차
DB/API/message 하위 호환성
```

Metric에 version label이 없으면 전체 오류율만 보여 Canary 문제를 찾기 어렵다.

## 단계 설계

예시:

```text
0. 내부 synthetic test
1. 직원 계정 또는 test tenant
2. 1% traffic, 10분
3. 5% traffic, 20분
4. 20% traffic, 30분
5. 50% traffic, 30분
6. 100% 전환
7. 이전 version 관찰 후 제거
```

고정 비율과 시간은 예시일 뿐이다. Traffic 양, 장애 영향, daily pattern과 필요한 통계 신뢰도로 정한다.

## Metric Gate

### 기술 Metric

```text
Request error rate
HTTP 5xx
p50/p95/p99 latency
CPU와 memory
GC pause
Pod restart/OOM
Thread/connection pool
DB query와 lock
외부 API timeout
```

### Business Metric

```text
로그인 성공률
주문 성공률
결제 승인률
회원가입 완료율
message 처리 성공률
```

HTTP 200이어도 주문이 중복되거나 금액 계산이 틀리면 기술 metric만으로 잡기 어렵다.

## Baseline 비교

Canary 절대값뿐 아니라 같은 시간의 stable version과 비교한다.

```text
Canary error rate: 1.2%
Stable error rate: 0.1%
→ 상대적으로 큰 회귀
```

Traffic 특성이 다르면 단순 비교가 왜곡된다. 같은 endpoint, Region, AZ, 사용자 특성을 가능한 한 맞춘다.

## Low Traffic 문제

1% traffic이 시간당 요청 5건이면 오류가 없어도 안전하다는 증거가 부족하다.

대응:

```text
최소 request count 조건
단계 유지 시간 연장
synthetic traffic 추가
위험 낮은 cohort를 더 크게 선택
peak 시간과 off-peak 시간 모두 관찰
```

시간만 기다리는 것이 아니라 표본 수와 중요 transaction 통과 여부를 본다.

## ALB Weighted Target Group

ALB listener rule에서 여러 target group에 weight를 줄 수 있다.

```text
stable target group weight: 95
canary target group weight: 5
```

Weight는 상대 비율이다.

```text
10 : 10 → 약 50% : 50%
10 : 20 → 약 33% : 67%
```

중요한 제약:

```text
Canary target group이 비었거나 unhealthy여도
ALB가 자동으로 stable target group에 전부 failover하지 않을 수 있음
```

따라서 health 상태를 monitoring하고 automation이 weight를 0으로 되돌려야 한다.

## Stickiness

기본 weighted routing에서는 같은 사용자가 매 요청마다 다른 target group으로 갈 수 있다.

```text
첫 요청 v2
다음 요청 v1
```

사용자 flow가 version에 고정되어야 한다면 target group stickiness를 사용할 수 있다. 하지만 stickiness는 실제 비율, cookie, CORS와 장애 전환에 영향을 준다.

State를 server local session에 두는 구조 자체도 개선 대상이다.

## Header와 사용자 기반 Canary

```text
X-Canary: true
특정 internal user
특정 tenant
특정 Region
특정 account ID hash
```

비율 routing보다 재현이 쉽고 위험이 낮은 사용자부터 검증할 수 있다.

개인정보 기반 segment와 실험은 정책과 동의를 확인한다. Header는 외부 사용자가 임의로 보낼 수 있으므로 edge에서 신뢰할 수 있게 설정한다.

## Argo Rollouts 예시

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: member-api
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause:
            duration: 10m
        - setWeight: 20
        - pause:
            duration: 20m
        - setWeight: 50
        - pause: {}
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
```

마지막 빈 `pause`는 수동 promotion을 기다리는 단계로 사용할 수 있다.

## Analysis Template 개념

```text
Prometheus query
→ Canary 5xx 비율
→ Stable 대비 latency
→ 주문 성공률

조건 통과
→ 다음 단계 promotion

조건 실패
→ rollout abort와 traffic 복구
```

Metric query 오류와 monitoring 장애를 성공으로 간주할지 실패로 간주할지 정책이 필요하다.

## Promotion, Pause, Abort

```text
Promotion
→ 다음 traffic 단계로 이동

Pause
→ 관찰 또는 승인 대기

Abort
→ Canary traffic 제거, stable 유지
```

Abort 후에도 이미 Canary가 DB나 message에 남긴 부수 효과는 사라지지 않는다. Application rollback과 data recovery는 별도다.

## Auto Scaling 상호작용

Canary replica가 1개인데 weight가 20%라면 해당 Pod가 과부하될 수 있다.

```text
Traffic weight
Canary replica 수
Pod request/limit
HPA metric과 반응 시간
Load Balancer target 수
```

를 함께 변경한다. Stable과 Canary의 instance type과 resource 설정이 다르면 version 비교가 왜곡된다.

## DB와 Event 호환성

Canary도 v1/v2가 동시에 실행되므로 Rolling과 같은 Expand-Contract가 필요하다.

```text
새 column 추가 후 양쪽 version이 사용 가능
Event field는 추가 중심으로 변경
Consumer가 모르는 field를 무시
Cache key/serialization version 관리
```

Canary가 새 형식 message를 발행해 v1 consumer를 깨뜨리면 작은 HTTP traffic 비율보다 영향이 커질 수 있다.

## Side Effect가 있는 Shadow와 차이

Shadow traffic은 요청을 복제하되 사용자 응답에는 Canary 결과를 사용하지 않는다.

```text
조회 요청
→ 비교적 안전하게 복제 가능

결제/주문/메일 발송
→ 그대로 복제하면 중복 부수 효과
```

Shadow 환경에서는 write를 차단하거나 별도 sandbox dependency를 사용한다.

## Canary 중단 기준 예시

```text
최소 1,000 requests 이후
Canary 5xx > 1%
또는 Stable 대비 error rate 3배 초과
또는 p95 latency 30% 증가
또는 주문 성공률 2%p 감소
또는 OOM/restart 발생
→ 자동 Abort
```

실제 threshold는 서비스 SLO와 평소 변동성으로 정한다. 너무 민감하면 정상 변동에도 중단되고 너무 느슨하면 사용자 피해를 막지 못한다.

## 관측성 설계

모든 signal에 version을 연결한다.

```text
service=member-api
version=2.0.0
deployment=canary
region=ap-northeast-2
```

Metric tag에 user ID나 request ID를 넣어 cardinality를 폭증시키지 않는다. 개별 요청은 trace와 log로 찾는다.

## Canary 배포 Pipeline

```text
Build immutable image
→ Unit/Integration/Security test
→ Staging deploy
→ Production Canary 생성
→ Readiness 통과
→ 1% traffic
→ 자동 Analysis
→ 단계별 Promotion
→ 100% 전환
→ Stable version 관찰 후 제거
```

## 자주 발생하는 실패

```text
Metric에 version label이 없음
Traffic이 적어 검증되지 않음
Canary instance 수보다 weight가 큼
Health Check는 성공하지만 business 기능 실패
Sticky session 때문에 비율 왜곡
Autoscaling 차이로 성능 비교 왜곡
DB migration이 v1과 비호환
Abort했지만 message/data 부수 효과가 남음
Canary target unhealthy인데 weight가 유지됨
```

## Canary Checklist

```text
영향 범위를 줄일 routing 방법이 있는가?
최소 표본 수와 단계 시간이 정의됐는가?
Stable과 Canary metric을 분리해 비교하는가?
기술 metric과 business metric이 모두 있는가?
자동 abort와 수동 override가 있는가?
v1/v2 DB·API·Event가 호환되는가?
Weight와 replica capacity가 맞는가?
Abort 후 data recovery 절차가 있는가?
```

## 공식 참고 자료

- [Argo Rollouts Canary](https://argo-rollouts.readthedocs.io/en/stable/features/canary/)
- [ALB Weighted Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-action-types.html)
- [ALB Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)

## 설명할 때 핵심 문장

```text
Canary는 일부 traffic에 새 version을 노출하고 metric을 확인하며 점진적으로 확대해 장애 영향 범위를 줄이는 전략이다.
Canary의 핵심은 traffic 비율이 아니라 version별 관측성, 충분한 표본, 자동 중단 기준과 하위 호환성이다.
ALB나 Argo Rollouts로 routing을 구현할 수 있지만 unhealthy Canary의 weight 제거와 data 부수 효과 복구는 별도 automation이 필요하다.
```
