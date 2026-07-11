# 14. 백엔드 운영: Logging, Monitoring, Cache, MQ, Batch

## 운영 관점이 필요한 이유

백엔드는 기능 구현만으로 끝나지 않는다.

운영 환경에서는 아래를 계속 봐야 한다.

```text
서버가 살아 있는가?
응답이 느려지지 않았는가?
에러가 증가하지 않았는가?
DB connection이 부족하지 않은가?
외부 API가 실패하지 않는가?
배치가 정상 완료됐는가?
```

## Logging

로그는 장애 분석의 핵심 자료다.

좋은 로그:

```text
언제 발생했는지
어떤 요청인지
어떤 사용자나 resource인지
어떤 에러인지
추적 가능한 trace id가 있는지
```

나쁜 로그:

```text
민감 정보 출력
의미 없는 메시지
너무 많은 debug 로그
예외 stack trace 누락
```

로그 레벨:

```text
ERROR
WARN
INFO
DEBUG
TRACE
```

## Monitoring

모니터링은 시스템 상태를 숫자로 보는 것이다.

주요 지표:

```text
request count
latency
error rate
CPU
memory
GC
thread pool
connection pool
DB query time
```

대표 관점:

```text
RED
→ Rate, Error, Duration

USE
→ Utilization, Saturation, Errors
```

## Health Check

운영 환경에서는 health check endpoint가 필요하다.

```text
/actuator/health
```

사용처:

```text
ALB Target Group
Kubernetes readinessProbe
배포 스크립트
모니터링 시스템
```

단순히 서버 process가 떠 있는 것과 서비스가 정상인 것은 다르다.

## Cache

Cache는 자주 조회되는 데이터를 빠르게 반환하기 위해 사용한다.

예:

```text
상품 상세
카테고리 목록
설정 정보
토큰 검증 결과
```

장점:

```text
응답 속도 개선
DB 부하 감소
```

주의:

```text
캐시 무효화
데이터 불일치
TTL 설정
캐시 장애 시 fallback
```

대표 도구:

```text
Local Cache
Redis
```

## Message Queue

Message Queue는 작업을 비동기로 처리하기 위해 사용한다.

예:

```text
주문 완료 이벤트
이메일 발송
알림 발송
외부 시스템 연동
로그 처리
```

장점:

```text
요청 응답 시간 단축
시스템 간 결합도 감소
재시도 처리 가능
트래픽 완충
```

주의:

```text
중복 메시지
순서 보장
재시도
dead letter queue
idempotency
```

## Batch와 Scheduler

Batch는 대량 데이터를 정해진 단위로 처리하는 작업이다.

Scheduler는 특정 시간이나 주기마다 작업을 실행한다.

예:

```text
매일 정산
만료 쿠폰 처리
휴면 회원 전환
통계 생성
외부 데이터 동기화
```

주의:

```text
중복 실행 방지
실패 재처리
처리량
lock
부분 실패
```

## 구조화 Logging과 Correlation ID

문자열 log만 남기기보다 검색 가능한 key-value 형태를 사용한다.

```json
{
  "level": "ERROR",
  "traceId": "4bf92f...",
  "memberId": 10,
  "orderId": 31,
  "event": "PAYMENT_FAILED",
  "errorCode": "PROVIDER_TIMEOUT"
}
```

요청 진입 시 correlation/trace ID를 만들거나 전달받아 MDC에 넣으면 같은 요청의 여러 log를 연결할 수 있다. thread pool이나 비동기 작업으로 넘어갈 때 MDC가 자동 전파되는지는 별도로 확인해야 한다.

비밀번호, access token, card 번호, session ID, 개인정보는 logging하지 않는다. 필요한 식별자는 masking하거나 내부 ID를 사용한다.

## Metric, Log, Trace의 차이

```text
Metric
→ 전체 상태와 추세를 숫자로 빠르게 탐지

Log
→ 개별 event의 상세 내용 확인

Trace
→ 한 요청이 여러 서비스와 DB를 거친 시간과 호출 관계 추적
```

장애 대응은 보통 alert로 이상을 탐지하고 metric으로 범위를 좁힌 뒤 trace와 log로 원인을 찾는다.

## SLI, SLO, Alert

```text
SLI
→ 실제 측정 지표, 성공률과 latency 등

SLO
→ 일정 기간 달성하려는 목표, 예: 월간 성공률 99.9%

SLA
→ 고객과 약속한 계약 수준과 위반 결과
```

CPU가 높다는 사실보다 사용자가 실제로 겪는 error rate와 latency가 더 직접적인 서비스 지표다. 순간 spike마다 alert하면 피로도가 높아지므로 지속 시간, 영향 범위, error budget 소진 속도를 반영한다.

## Cache Pattern

```text
Cache Aside
→ cache 조회
→ miss면 DB 조회
→ cache 저장

Write Through
→ 쓰기를 cache와 원본 저장소에 함께 반영

Write Behind
→ cache에 먼저 쓰고 원본 저장소에 비동기 반영
```

Cache Aside가 흔하지만 DB 수정 후 cache 삭제에 실패하면 오래된 값이 남을 수 있다. 삭제 순서, event 기반 무효화, 짧은 TTL, 허용 가능한 불일치 시간을 함께 정한다.

## Cache Stampede와 장애

인기 key가 만료되는 순간 많은 요청이 동시에 DB로 가는 현상을 cache stampede라고 한다.

```text
TTL에 작은 random 값 추가
한 요청만 값을 갱신하도록 lock
만료 전 background refresh
오래된 값을 잠시 반환하는 stale 전략
```

Redis가 느려졌을 때 모든 요청이 기다리며 application thread를 소진하지 않도록 짧은 timeout, fallback, circuit breaker를 설계한다. cache는 성능 최적화 수단이지 새로운 단일 장애 지점이 되어서는 안 된다.

## Message 전달 보장

```text
At-most-once
→ 최대 한 번, 손실될 수 있지만 중복은 줄어듦

At-least-once
→ 성공할 때까지 재전달 가능, 중복 처리 대비 필요

Exactly-once
→ 제한된 범위와 조건에서만 가능하며 전체 외부 부수 효과까지 자동 보장하지 않음
```

실무 consumer는 같은 message를 여러 번 받아도 결과가 한 번 처리한 것과 같도록 멱등하게 만든다.

```text
eventId unique 저장
업무 key에 unique constraint
현재 상태를 확인한 뒤 허용된 전이만 수행
처리 결과 저장
```

## Retry와 DLQ

```text
일시적 오류
→ timeout, 일시적인 5xx
→ 지수 backoff와 jitter를 적용해 제한적으로 retry

영구 오류
→ validation 실패, 존재하지 않는 resource
→ 반복 retry 대신 실패 처리
```

최대 재시도 후에도 실패한 message는 DLQ로 보내 원인과 재처리 절차를 관리한다. DLQ는 실패를 숨기는 쓰레기통이 아니라 alert, 분석, 수정, replay 정책이 있는 운영 queue다.

## Transactional Outbox

DB commit과 message publish를 따로 수행하면 둘 중 하나만 성공할 수 있다.

```text
하나의 DB transaction
→ 주문 저장
→ outbox event 저장
→ commit

별도 publisher
→ 미발행 outbox 조회
→ broker 전송
→ 발행 완료 표시
```

Outbox는 event 유실 가능성을 줄이지만 중복 발행 가능성은 남으므로 consumer 멱등성이 필요하다.

## 외부 API 장애 격리

```text
Timeout
→ 무한정 기다리지 않음

Retry
→ 일시적 실패만 제한적으로 재시도

Circuit Breaker
→ 실패가 계속될 때 빠르게 차단

Bulkhead
→ thread pool과 connection을 분리해 한 외부 시스템 장애가 전체로 번지는 것을 제한

Rate Limit
→ 허용량을 넘는 호출 제어
```

재시도는 하위 시스템 부하를 키울 수 있다. 호출 계층마다 각각 세 번 재시도하면 요청 하나가 많은 하위 요청으로 증폭될 수 있으므로 한 지점에서 전체 retry budget을 관리한다.

## Batch 재시작 가능성

큰 batch는 chunk 단위로 읽고 처리하고 쓴다. 실패 지점부터 재시작할 수 있도록 job 실행 상태와 checkpoint를 저장한다.

```text
같은 job 중복 실행 방지
item 단위 멱등성
skip과 retry 기준
부분 성공 결과 확인
처리량과 DB 부하 제한
실패 알림과 수동 재처리 절차
```

여러 instance에서 scheduler가 동시에 실행될 수 있으므로 단순 `@Scheduled`만으로 단일 실행이 보장된다고 가정하면 안 된다.

## 설명할 때 핵심 문장

```text
백엔드 운영은 기능이 배포된 뒤에도 안정적으로 동작하는지 관찰하고 문제를 복구하는 영역이다.
로그는 장애 원인을 추적하는 기록이고, 모니터링은 시스템 상태를 숫자로 보는 것이다.
Cache는 성능을 높이지만 무효화와 데이터 일관성이 중요하다.
Message Queue는 비동기 처리와 시스템 분리에 유용하지만 중복 처리와 재시도 설계가 필요하다.
Batch와 Scheduler는 정기적이고 대량의 작업을 안정적으로 처리하기 위해 사용한다.
```
