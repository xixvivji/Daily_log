# 19. 주문·재고 동시성 실전

## 문제 상황

재고가 1개일 때 두 요청이 동시에 조회할 수 있다.

```text
Transaction A: stock 1 조회
Transaction B: stock 1 조회
Transaction A: 0으로 수정
Transaction B: 0으로 수정
```

두 주문이 성공했지만 재고는 한 번만 감소한 것처럼 보이는 lost update다. Java 코드 한 줄이 맞아도 여러 transaction 사이에서는 안전하지 않을 수 있다.

## 먼저 지켜야 할 불변식

```text
재고는 0보다 작을 수 없다.
한 쿠폰은 한 번만 사용한다.
같은 결제 요청은 한 번만 승인한다.
주문 상태는 허용된 순서로만 변경한다.
```

기술을 고르기 전에 어떤 조건을 반드시 지킬지 정의한다.

## JVM Lock의 한계

```java
public synchronized void decrease(Long productId) { ... }
```

한 JVM 안에서는 직렬화할 수 있지만 application instance가 여러 대면 각 instance가 자기 lock을 가진다. DB를 공유하는 scale-out 환경의 최종 해결책이 아니다.

## Atomic SQL

조건을 update문에 포함할 수 있다.

```sql
UPDATE products
SET stock = stock - :quantity
WHERE id = :id
  AND stock >= :quantity;
```

영향받은 row가 1이면 성공, 0이면 재고 부족이다. 단순한 counter 변경에는 읽고 수정하는 방식보다 효율적이고 안전할 수 있다.

```java
@Modifying(clearAutomatically = true)
@Query("""
    update Product p
       set p.stock = p.stock - :quantity
     where p.id = :id
       and p.stock >= :quantity
    """)
int decreaseStock(Long id, int quantity);
```

Bulk update 뒤 persistence context에 이전 값이 남지 않게 clear 전략을 확인한다.

## 비관적 Lock

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("select p from Product p where p.id = :id")
Optional<Product> findByIdForUpdate(Long id);
```

```text
row lock 획득
→ 재고 확인
→ 차감
→ commit 시 lock 해제
```

장점:

```text
충돌이 잦을 때 결과가 단순함
transaction 안에서 상태를 확인하고 수정 가능
```

단점:

```text
lock 대기와 timeout
deadlock
긴 transaction이 처리량 감소
외부 API를 lock 안에서 호출하면 위험
```

여러 row를 잠글 때 획득 순서를 통일한다.

## 낙관적 Lock

```java
@Version
private Long version;
```

```sql
UPDATE products
SET stock = ?, version = version + 1
WHERE id = ? AND version = ?;
```

다른 transaction이 먼저 변경했다면 update row가 0이 되어 충돌 예외가 발생한다.

적합한 경우:

```text
충돌이 드묾
대기보다 실패 후 재시도가 나음
사용자에게 충돌을 알릴 수 있음
```

재시도는 새 transaction에서 수행하고 횟수와 backoff를 제한한다. 충돌이 매우 많으면 반복 재시도가 DB 부하를 키울 수 있다.

## Unique Constraint

```sql
ALTER TABLE coupon_usages
ADD CONSTRAINT uk_coupon_member UNIQUE (coupon_id, member_id);
```

사전 조회는 사용자 친화적인 오류를 만들지만 race condition을 막지 못한다. DB constraint를 최종 방어선으로 둔다.

## Idempotency Key

```text
POST /orders
Idempotency-Key: request-uuid
```

저장 항목:

```text
사용자와 key
요청 body fingerprint
처리 상태: PROCESSING/SUCCEEDED/FAILED
응답 status와 body
만료 시점
```

같은 key에 다른 body가 오면 거부한다. 첫 요청 처리 중이면 중복 실행하지 않고 완료를 기다리거나 처리 중 응답을 준다.

## 분산 Lock

Redis 등으로 여러 instance 사이 lock을 조정할 수 있다.

```text
lock key 획득 + TTL
→ business transaction 실행
→ 소유자 token을 확인해 lock 해제
```

주의:

```text
작업보다 TTL이 먼저 끝날 수 있음
GC pause와 network partition
failover 중 중복 소유 가능성
lock은 DB transaction과 원자적이지 않음
```

가능하면 DB constraint, atomic update, optimistic/pessimistic lock으로 먼저 해결한다. 분산 lock이 정말 필요한 자원인지와 실패 시 중복 실행을 견딜 수 있는지 확인한다.

## 주문과 결제를 한 Transaction으로 묶을 수 없는 이유

외부 결제사는 로컬 DB transaction에 참여하지 않는다.

```text
DB 주문 저장 성공
결제 API 성공
DB commit 실패
→ 결제만 성공 가능
```

상태 machine과 보상 처리가 필요하다.

```text
PENDING_PAYMENT
→ PAYMENT_APPROVED
→ COMPLETED

실패 시
→ PAYMENT_FAILED 또는 CANCEL_REQUESTED
```

결제 요청에는 idempotency key를 사용하고 callback도 중복 수신을 가정한다.

## 동시성 Test

```java
int requestCount = 100;
ExecutorService pool = Executors.newFixedThreadPool(20);
CountDownLatch ready = new CountDownLatch(requestCount);
CountDownLatch start = new CountDownLatch(1);
CountDownLatch done = new CountDownLatch(requestCount);

for (int i = 0; i < requestCount; i++) {
    pool.submit(() -> {
        ready.countDown();
        start.await();
        try {
            stockService.decrease(productId, 1);
        } finally {
            done.countDown();
        }
        return null;
    });
}

ready.await();
start.countDown();
done.await();
```

같은 test process 안의 thread 수만 늘리는 것으로 production과 완전히 같아지지는 않는다. 실제 DB, 여러 application instance, lock timeout과 retry를 포함한 integration/load test가 필요하다.

검증:

```text
최종 stock
성공 주문 수
중복 결제·쿠폰 row 수
lock 대기 시간
deadlock과 timeout 수
retry 성공·실패 수
```

## 선택 기준

```text
단순 수량 조건 변경 → Atomic SQL
중복 생성 방지       → Unique Constraint
충돌 드묾            → Optimistic Lock
충돌 잦고 작업 짧음  → Pessimistic Lock
중복 HTTP 재시도     → Idempotency Key
여러 system 작업     → 상태 machine, Outbox, 보상 처리
```

## 설명할 때 핵심 문장

```text
동시성 문제는 여러 transaction이 같은 상태를 읽고 수정할 때 발생한다.
JVM lock은 여러 instance를 보호하지 못하므로 DB constraint와 transaction 전략이 필요하다.
락을 선택하기 전에 지켜야 할 불변식, 충돌 빈도, 재시도 가능성, lock 유지 시간을 먼저 본다.
```
