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

## 설명할 때 핵심 문장

```text
백엔드 운영은 기능이 배포된 뒤에도 안정적으로 동작하는지 관찰하고 문제를 복구하는 영역이다.
로그는 장애 원인을 추적하는 기록이고, 모니터링은 시스템 상태를 숫자로 보는 것이다.
Cache는 성능을 높이지만 무효화와 데이터 일관성이 중요하다.
Message Queue는 비동기 처리와 시스템 분리에 유용하지만 중복 처리와 재시도 설계가 필요하다.
Batch와 Scheduler는 정기적이고 대량의 작업을 안정적으로 처리하기 위해 사용한다.
```
