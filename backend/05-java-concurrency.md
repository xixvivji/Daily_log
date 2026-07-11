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

## Java Memory Model

여러 thread가 같은 메모리를 사용할 때는 세 가지를 구분해야 한다.

```text
원자성
→ 연산이 중간에 나뉘지 않고 한 단위로 수행되는가?

가시성
→ 한 thread의 변경을 다른 thread가 언제 볼 수 있는가?

순서성
→ compiler와 CPU의 재배치가 있어도 필요한 실행 순서가 보장되는가?
```

`count++`는 읽기, 증가, 쓰기로 나뉘므로 원자적이지 않다. 한 thread가 값을 변경했다고 다른 thread가 즉시 최신 값을 본다는 보장도 synchronization 없이는 부족할 수 있다.

## volatile

`volatile`은 해당 변수의 읽기와 쓰기에 가시성과 특정 순서 보장을 제공한다.

```java
private volatile boolean running = true;
```

하지만 복합 연산을 원자적으로 만들지는 않는다.

```java
volatile int count;
count++; // 여전히 원자적이지 않음
```

단순 상태 플래그에는 유용하지만 여러 값을 함께 변경하거나 읽기-수정-쓰기가 필요하면 lock이나 atomic 연산이 필요하다.

## Lock과 Deadlock

`ReentrantLock`은 명시적인 lock 획득·해제, 시간 제한, interrupt 가능한 대기 같은 기능을 제공한다.

```java
lock.lock();
try {
    update();
} finally {
    lock.unlock();
}
```

Deadlock은 서로가 가진 lock을 기다리며 영원히 진행하지 못하는 상태다.

```text
Thread A: lock 1 획득 → lock 2 대기
Thread B: lock 2 획득 → lock 1 대기
```

lock 획득 순서를 통일하고, lock 범위를 줄이며, 여러 lock을 동시에 잡는 구조를 피하는 것이 기본 대응이다.

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

`ExecutorService`는 작업 제출과 thread 관리를 분리한다.

```java
ExecutorService executor = Executors.newFixedThreadPool(10);
Future<Member> future = executor.submit(() -> memberClient.find(id));
```

pool 크기는 CPU 작업과 blocking I/O 작업에서 기준이 다르다. queue가 무제한이면 요청이 메모리에 계속 쌓이고, 너무 작으면 처리량이 낮으며, 너무 크면 context switching과 하위 시스템 과부하가 커진다. pool 크기뿐 아니라 queue 크기, 거부 정책, timeout, metric을 함께 설정해야 한다.

## CompletableFuture

`CompletableFuture`는 비동기 결과를 조합할 수 있다.

```java
CompletableFuture<Member> memberFuture =
    CompletableFuture.supplyAsync(() -> memberClient.find(id), executor);

CompletableFuture<List<Order>> orderFuture =
    CompletableFuture.supplyAsync(() -> orderClient.findByMember(id), executor);

MemberSummary summary = memberFuture
    .thenCombine(orderFuture, MemberSummary::new)
    .orTimeout(2, TimeUnit.SECONDS)
    .join();
```

서로 독립적인 I/O를 병렬화할 때 유용하지만, executor를 지정하지 않은 async 메서드는 공용 pool을 사용할 수 있다. timeout, 예외 처리, 취소, thread pool 격리를 설계하지 않으면 장애가 전파될 수 있다.

## Virtual Thread

Virtual Thread는 JVM이 관리하는 가벼운 thread다. blocking I/O가 많은 thread-per-request 코드의 처리량을 높이는 데 유용하다.

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<Member> result = executor.submit(() -> memberClient.find(id));
}
```

Virtual Thread는 작업 자체를 더 빠르게 실행하거나 DB connection 수를 늘려주지 않는다. DB pool이 30개라면 수천 개 virtual thread가 있어도 동시에 수행 가능한 DB 작업은 connection 수에 제한된다. CPU 집약 작업의 속도를 높이기 위한 기능도 아니다.

## 애플리케이션 락과 DB 락

```text
synchronized / ReentrantLock
→ 같은 JVM process 내부 thread 사이에서만 유효

DB pessimistic lock
→ transaction이 row lock을 선점

DB optimistic lock
→ version을 비교해 충돌을 감지

분산 lock
→ 여러 application instance 사이에서 하나의 자원 접근 조정

Unique constraint
→ 최종 데이터 중복을 DB가 거부
```

서버가 여러 대라면 JVM lock만으로 중복 주문이나 쿠폰 사용을 막을 수 없다. 가능한 경우 DB 제약조건을 최종 방어선으로 두고, 충돌 빈도와 처리량에 따라 optimistic lock, pessimistic lock, queue, distributed lock을 선택한다.

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
