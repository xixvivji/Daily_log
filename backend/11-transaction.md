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

## 실제 Transaction 동작 흐름

```text
Controller가 proxy Service 호출
→ TransactionManager가 transaction 시작
→ DB connection 획득
→ Service와 Repository 작업 수행
→ flush로 SQL 실행
→ 정상 종료 시 commit
→ 예외 발생 시 rollback
→ connection 반환
```

`@Transactional` 자체가 SQL을 실행하는 것은 아니다. Spring AOP proxy가 transaction 경계를 만들고 JPA가 persistence context의 변경을 flush한다.

## readOnly Transaction

```java
@Transactional(readOnly = true)
public MemberResponse find(Long id) { ... }
```

읽기 전용 의도를 표시하고 JPA provider나 DB driver가 최적화할 여지를 준다. 하지만 모든 DB에서 쓰기를 물리적으로 차단한다고 가정하면 안 된다. 쓰기 method에는 별도의 `@Transactional`을 적용한다.

class 수준에 `readOnly = true`를 두고 쓰기 method에서 덮어쓰는 패턴을 사용할 수 있다.

## Isolation Level별 현상

```text
Dirty Read
→ 다른 transaction이 아직 commit하지 않은 값을 읽음

Non-repeatable Read
→ 같은 row를 다시 읽었는데 다른 transaction의 commit으로 값이 달라짐

Phantom Read
→ 같은 범위 query를 다시 실행했는데 row가 추가되거나 사라짐

Lost Update
→ 두 transaction이 같은 값을 수정해 한쪽 변경이 덮어써짐
```

격리 수준 이름만으로 모든 동작을 단정하면 안 된다. MVCC와 lock 구현, DB 종류에 따라 실제 동작이 다를 수 있으므로 사용하는 DB 문서와 재현 테스트로 확인한다.

## Propagation 세부 선택

```text
REQUIRED
→ 기존 transaction에 참여, 없으면 생성

REQUIRES_NEW
→ 기존 transaction을 잠시 중단하고 독립 transaction 생성

SUPPORTS
→ 있으면 참여하고 없어도 실행

MANDATORY
→ 기존 transaction이 없으면 예외

NOT_SUPPORTED
→ transaction 없이 실행

NESTED
→ savepoint 기반 중첩 transaction, 지원 여부 확인 필요
```

`REQUIRES_NEW`를 감사 log 저장에 쓰면 본 작업 rollback과 별도로 commit할 수 있지만 connection을 추가로 필요로 하고 전체 원자성은 깨진다. 목적과 장애 시 의미를 먼저 정해야 한다.

## Rollback이 안 되는 대표 상황

```text
같은 객체 내부에서 @Transactional method 호출
Spring Bean이 아닌 객체를 직접 new로 생성
예외를 catch한 뒤 정상 반환
기본 규칙에서 checked exception 발생
transaction method가 실제 proxy 제약을 만족하지 않음
비동기 thread로 작업을 넘김
```

```java
@Transactional
public void createOrder() {
    try {
        payment();
    } catch (RuntimeException e) {
        log.warn("payment failed", e);
        // 예외를 삼키면 method는 정상 종료로 보일 수 있음
    }
}
```

실패를 복구한 것이 아니라면 적절한 예외를 다시 던져 rollback 의도를 유지한다.

## UnexpectedRollbackException

내부 작업이 transaction을 rollback-only로 표시한 뒤 외부 method가 예외를 잡고 정상 종료해도 마지막 commit 시점에 `UnexpectedRollbackException`이 발생할 수 있다.

```text
외부 REQUIRED 시작
→ 내부 REQUIRED 참여
→ 내부 RuntimeException으로 rollback-only
→ 외부에서 예외 catch
→ commit 시도
→ 이미 rollback-only이므로 전체 rollback
```

같은 transaction에 참여한다는 의미를 이해하고 예외 처리와 propagation을 설계해야 한다.

## 외부 API와 Transaction

DB transaction 안에서 결제 API를 호출하면 응답을 기다리는 동안 connection과 lock을 점유할 수 있다. 반대로 DB commit 뒤 외부 호출을 하면 둘을 하나의 원자적 transaction으로 묶을 수 없다.

```text
짧은 동기 작업
→ 외부 호출과 DB 상태 전이를 명확히 나누고 보상 처리 설계

비동기 연계
→ Transactional Outbox로 DB 변경과 event 기록을 같은 transaction에 저장
→ 별도 publisher가 event 전달
```

분산 시스템에서는 로컬 DB transaction만으로 전체 원자성을 보장할 수 없으므로 상태 machine, idempotency, retry, 보상 transaction을 함께 설계한다.

## 설명할 때 핵심 문장

```text
Transaction은 여러 DB 작업을 하나의 작업 단위로 묶어 모두 성공하거나 모두 실패하게 하는 기능이다.
Spring에서는 @Transactional로 트랜잭션 경계를 선언하고, 보통 Service 계층에 둔다.
트랜잭션이 너무 길면 DB connection과 lock을 오래 점유해 성능 문제가 생길 수 있다.
Isolation과 propagation은 동시성 문제와 트랜잭션 전파 방식을 제어한다.
```
