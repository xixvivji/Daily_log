# 22. 외부 API 연동과 장애 격리

## 외부 호출의 실패 지점

```text
DNS 실패
TCP connection 실패
TLS handshake 실패
connection pool 대기
request write timeout
response timeout
4xx/5xx
잘못된 JSON
부분 응답
상대 시스템 과부하
```

`외부 API 오류` 하나로 묶지 말고 어느 단계가 실패했는지 구분한다.

## Client 경계

```java
public interface PaymentClient {
    PaymentResult approve(PaymentRequest request);
}
```

Infrastructure adapter가 HTTP DTO, 인증 header, status mapping을 담당하고 Service는 provider-specific JSON을 알지 않게 한다.

```text
Domain/Application DTO
↔ Adapter mapping
↔ Provider HTTP DTO
```

## Timeout

Timeout 없는 외부 호출은 요청 thread와 connection을 무한정 점유할 수 있다.

```text
Connect Timeout
→ 연결 수립 제한

Response Timeout
→ 응답 시작 또는 전체 처리 제한

Read Timeout
→ data read 대기 제한

Pool Acquire Timeout
→ connection 대여 대기 제한
```

상위 API deadline보다 하위 timeout의 합이 짧아야 실패를 처리하고 응답할 시간이 남는다.

## Retry

Retry 후보:

```text
일시적인 connection reset
짧은 network timeout
일부 502/503/504
429와 Retry-After
```

Retry하지 않을 것:

```text
일반적인 400 validation 오류
인증·권한 오류
이미 처리됐는지 모르는 non-idempotent 요청
영구적인 business rejection
```

Exponential backoff와 jitter로 여러 client의 동시 재시도를 분산한다. 요청 한 번이 여러 계층에서 각각 retry되면 호출 수가 곱으로 증가하므로 retry 책임을 한 계층에 둔다.

## Idempotency

결제 승인처럼 응답을 받기 전에 connection이 끊기면 server가 처리했는지 알 수 없다.

```text
Client-generated idempotency key
Provider에 같은 key 전달
로컬 요청과 결과 저장
조회 API로 최종 상태 확인
```

Retry 가능 여부는 HTTP method 이름보다 provider 계약과 idempotency 보장으로 판단한다.

## Circuit Breaker

```text
CLOSED
→ 정상 호출, 실패율 측정

OPEN
→ 호출을 빠르게 거부해 장애 격리

HALF_OPEN
→ 제한된 시험 호출로 복구 확인
```

Circuit Breaker는 상대를 복구시키는 기능이 아니라 실패 중인 dependency에 계속 매달리지 않도록 한다. 너무 작은 표본과 임계값은 정상 변동에도 circuit을 열 수 있다.

## Bulkhead

외부 결제 API가 느릴 때 모든 Tomcat thread와 HTTP connection을 차지하면 회원 조회까지 느려진다.

```text
외부 system별 connection pool
동시 호출 수 제한
별도 thread pool 또는 semaphore
queue 길이 제한
```

자원을 분리해 한 dependency 장애가 전체 application으로 번지는 것을 줄인다.

## Rate Limiter

Provider quota와 내부 보호를 위해 호출량을 제한한다.

```text
사용자별
API key별
endpoint별
전체 provider별
```

429 응답과 `Retry-After`를 처리하고 무제한 local queue에 요청을 쌓지 않는다.

## Fallback

좋은 fallback:

```text
상품 추천 실패 시 추천 영역 생략
환율 조회 실패 시 명시된 제한 시간 내 최근 값 사용
```

위험한 fallback:

```text
권한 service 실패 시 모두 허용
결제 확인 실패를 결제 성공으로 처리
오래된 재고를 현재 재고처럼 반환
```

Fallback은 기능 의미와 stale 허용 시간을 명확히 해야 한다.

## Resilience4j 예시

```java
@TimeLimiter(name = "payment")
@CircuitBreaker(name = "payment", fallbackMethod = "fallback")
@Retry(name = "payment")
public CompletableFuture<PaymentResult> approve(PaymentRequest request) {
    return CompletableFuture.supplyAsync(() -> paymentClient.approve(request));
}
```

Annotation 적용 순서, async executor, timeout 취소가 실제 network call을 중단하는지 확인한다. Library default를 그대로 쓰지 말고 provider SLO와 트래픽으로 설정한다.

## Error Mapping

```text
Provider 400 → 내부 INVALID_PAYMENT_REQUEST
Provider 401 → credential/configuration 장애, client에 그대로 노출하지 않음
Provider 409 → 중복 또는 상태 충돌
Provider 429 → rate limited
Provider 5xx/timeout → PAYMENT_PROVIDER_UNAVAILABLE
```

Provider response body와 credential을 그대로 log하지 않는다.

## Transaction 경계

외부 호출을 긴 DB transaction 안에 두면 connection과 lock을 오래 점유한다.

```text
로컬 상태 PENDING 저장
→ transaction commit
→ 외부 승인 호출
→ 결과를 새 transaction에서 반영
```

중간 실패를 허용하는 상태 machine과 재처리 job이 필요하다. 단순히 `@Transactional` 하나로 외부 시스템까지 원자적으로 만들 수 없다.

## Test

Mock server로 다음을 재현한다.

```text
정상 2xx와 JSON
4xx/5xx
느린 응답과 timeout
connection reset
잘못된 body
retry 후 성공
circuit open/half-open
중복 idempotency key
```

## Monitoring

```text
provider별 request rate
status와 error type
p50/p95/p99 latency
timeout/retry 횟수
circuit state
bulkhead rejected call
connection pool pending
fallback 사용량
```

## 공식 참고 자료

- [Resilience4j Retry](https://resilience4j.readme.io/docs/retry)
- [Resilience4j Getting Started](https://resilience4j.readme.io/docs/getting-started)

## 설명할 때 핵심 문장

```text
외부 API는 반드시 실패한다고 가정하고 timeout, 제한적 retry, idempotency, circuit breaker와 bulkhead를 설계한다.
Retry는 일시적이고 안전한 요청에만 적용하며 여러 계층의 중첩 retry를 피한다.
```
