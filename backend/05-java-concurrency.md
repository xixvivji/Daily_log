# 05. Java 동시성

## 동시성을 알아야 하는 이유

백엔드 서버는 여러 요청을 동시에 처리한다.

사용자가 한 명만 접속하는 것이 아니라 여러 사용자가 동시에 API를 호출한다.

```text
사용자 A → 주문 생성
사용자 B → 주문 생성
사용자 C → 결제 요청
```

따라서 Java 백엔드에서는 thread, race condition, thread-safe 개념을 알아야 한다.

## Process와 Thread

Process는 실행 중인 프로그램이다.

Thread는 process 안에서 실행되는 작업 흐름이다.

```text
Process
├─ Thread 1
├─ Thread 2
└─ Thread 3
```

Spring Boot 애플리케이션도 하나의 process로 실행되고, 내부에서 여러 thread가 요청을 처리한다.

## 요청과 Thread

전통적인 Spring MVC는 요청 하나를 thread 하나가 처리하는 모델에 가깝다.

```text
HTTP Request
→ Tomcat Thread Pool
→ Controller
→ Service
→ Repository
→ Response
```

동시에 요청이 많이 들어오면 thread pool의 thread들이 요청을 나눠 처리한다.

## Race Condition

Race condition은 여러 thread가 공유 데이터를 동시에 변경해서 결과가 꼬이는 문제다.

예:

```java
stock = stock - 1;
```

이 코드는 단순해 보이지만 내부적으로는 여러 단계다.

```text
현재 stock 읽기
1 감소
감소된 값 저장
```

두 thread가 동시에 실행하면 재고가 잘못 줄어들 수 있다.

## Thread-Safe

Thread-safe는 여러 thread가 동시에 접근해도 안전하다는 뜻이다.

안전하지 않은 예:

```java
private int count = 0;

public void increase() {
    count++;
}
```

`count++`는 원자적이지 않다.

대안:

```text
synchronized
Lock
AtomicInteger
ConcurrentHashMap
DB lock
분산 lock
```

## synchronized

`synchronized`는 한 번에 하나의 thread만 특정 영역에 들어오게 한다.

```java
public synchronized void increase() {
    count++;
}
```

장점:

```text
간단함
공유 자원 보호 가능
```

단점:

```text
성능 저하 가능
lock 범위가 크면 병목
분산 서버 여러 대에서는 JVM 내부 lock만으로 부족
```

## Atomic

AtomicInteger는 원자적 연산을 제공한다.

```java
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();
```

단순 counter에는 유용하지만 복잡한 비즈니스 트랜잭션을 모두 해결하지는 못한다.

## Thread Pool

Thread를 요청마다 계속 새로 만들면 비용이 크다.

Thread Pool은 미리 thread를 만들어두고 재사용한다.

```text
요청 들어옴
→ thread pool에서 thread 할당
→ 요청 처리
→ thread 반납
```

Tomcat도 thread pool을 사용한다.

thread pool이 고갈되면 요청이 대기하거나 timeout이 발생할 수 있다.

## Blocking I/O

Spring MVC + JDBC/JPA 구조는 대부분 blocking I/O다.

DB 응답을 기다리는 동안 thread가 대기한다.

```text
Thread
→ DB Query
→ 응답 대기
→ 결과 처리
```

DB가 느려지면 thread가 오래 점유되고, 결국 thread pool이 고갈될 수 있다.

## 실무에서 자주 보는 동시성 문제

```text
동시 주문으로 재고가 음수가 됨
중복 쿠폰 사용
중복 결제 요청
동일 요청 재시도로 데이터 중복 생성
thread pool 고갈
connection pool 고갈
static mutable state로 인한 데이터 꼬임
```

해결은 상황에 따라 다르다.

```text
DB unique constraint
transaction isolation
pessimistic lock
optimistic lock
idempotency key
message queue
distributed lock
```

## 설명할 때 핵심 문장

```text
백엔드 서버는 여러 요청을 동시에 처리하므로 thread와 동시성 문제를 이해해야 한다.
Race condition은 여러 thread가 공유 상태를 동시에 변경하면서 결과가 꼬이는 문제다.
Thread-safe한 구조를 만들려면 공유 mutable state를 줄이고, 필요한 경우 lock, atomic, DB constraint, transaction을 사용해야 한다.
Spring MVC에서는 요청을 처리하는 thread pool과 DB connection pool이 병목 지점이 될 수 있다.
```
