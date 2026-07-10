# 11. Transaction

## Transaction이 필요한 이유

Transaction은 여러 DB 작업을 하나의 작업 단위로 묶는 것이다.

예:

```text
주문 생성
재고 차감
결제 기록 저장
```

이 중 하나만 성공하고 나머지가 실패하면 데이터가 깨진다.

Transaction은 모두 성공하거나 모두 실패하게 만든다.

```text
all or nothing
```

## ACID

트랜잭션의 대표 성질은 ACID다.

```text
Atomicity
→ 원자성. 모두 성공하거나 모두 실패한다.

Consistency
→ 일관성. 트랜잭션 전후 데이터 규칙이 유지된다.

Isolation
→ 격리성. 동시에 실행되는 트랜잭션이 서로 영향을 덜 주도록 한다.

Durability
→ 지속성. commit된 데이터는 유지된다.
```

## @Transactional

Spring에서는 `@Transactional`로 트랜잭션을 적용한다.

```java
@Transactional
public OrderResponse createOrder(OrderRequest request) {
    Order order = orderRepository.save(...);
    stock.decrease(request.quantity());
    return OrderResponse.from(order);
}
```

메서드가 정상 종료되면 commit, RuntimeException이 발생하면 rollback된다.

## Rollback

Spring 기본 rollback 규칙:

```text
RuntimeException
→ rollback

Checked Exception
→ 기본적으로 rollback 안 됨
```

필요하면 설정할 수 있다.

```java
@Transactional(rollbackFor = Exception.class)
```

## Transaction 경계

트랜잭션은 보통 Service 계층에 둔다.

Controller는 HTTP 요청/응답을 처리하고, Service는 비즈니스 작업 단위를 담당하기 때문이다.

```text
Controller
→ Service @Transactional
→ Repository
```

트랜잭션이 너무 길면 문제가 된다.

```text
DB connection 오래 점유
lock 오래 유지
connection pool 고갈
응답 지연
```

외부 API 호출을 트랜잭션 안에서 오래 수행하는 것은 주의해야 한다.

## Isolation Level

Isolation Level은 동시에 실행되는 트랜잭션을 얼마나 격리할지 정한다.

대표 단계:

```text
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

격리 수준이 높을수록 정합성은 강해지지만 성능 비용이 커질 수 있다.

동시성 문제:

```text
Dirty Read
Non-repeatable Read
Phantom Read
Lost Update
```

## Propagation

Propagation은 이미 트랜잭션이 있을 때 새 트랜잭션을 어떻게 처리할지 정한다.

자주 보는 것:

```text
REQUIRED
→ 기존 트랜잭션이 있으면 참여, 없으면 새로 생성

REQUIRES_NEW
→ 항상 새 트랜잭션 생성
```

기본은 REQUIRED다.

## Self Invocation 문제

같은 클래스 내부에서 `@Transactional` 메서드를 직접 호출하면 프록시를 거치지 않아 트랜잭션이 적용되지 않을 수 있다.

```java
public void outer() {
    inner();
}

@Transactional
public void inner() {
}
```

Spring AOP 기반 동작을 이해해야 이 문제를 설명할 수 있다.

## 설명할 때 핵심 문장

```text
Transaction은 여러 DB 작업을 하나의 작업 단위로 묶어 모두 성공하거나 모두 실패하게 하는 기능이다.
Spring에서는 @Transactional로 트랜잭션 경계를 선언하고, 보통 Service 계층에 둔다.
트랜잭션이 너무 길면 DB connection과 lock을 오래 점유해 성능 문제가 생길 수 있다.
Isolation과 propagation은 동시성 문제와 트랜잭션 전파 방식을 제어한다.
```
