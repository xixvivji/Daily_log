# 29. Java와 Spring 디자인 패턴

## 디자인 패턴을 배우는 이유

디자인 패턴은 반복해서 나타나는 설계 문제와 그 해결 구조에 붙인 공통 이름이다.

```text
문제 상황
→ 변경되는 부분과 고정된 부분이 섞여 있음

설계 원칙
→ 책임을 나누고 의존 방향을 정함

디자인 패턴
→ 자주 검증된 객체 협력 구조로 문제를 해결
```

패턴의 목적은 class 수를 늘리는 것이 아니다. 변경 이유가 다른 코드를 분리하고, 구현 교체와 확장을 예측 가능한 위치에서 처리하는 것이 목적이다.

패턴 이름을 먼저 정한 뒤 코드에 끼워 맞추면 불필요한 추상화가 생긴다. 먼저 실제 변경 지점, 조건문 증가, 외부 시스템 결합, 중복되는 실행 흐름을 찾고 그 문제에 맞는 패턴을 선택한다.

## 패턴 분류

GoF 디자인 패턴은 크게 세 종류로 분류한다.

```text
생성 패턴
→ 객체를 어떻게 만들 것인가?
→ Factory Method, Abstract Factory, Builder, Singleton

구조 패턴
→ 객체와 객체를 어떻게 연결할 것인가?
→ Adapter, Proxy, Decorator, Facade

행위 패턴
→ 객체가 책임을 어떻게 나누고 협력할 것인가?
→ Strategy, Template Method, Observer,
  Chain of Responsibility, Command, State
```

Spring 자체도 IoC, DI, Proxy, Adapter, Template, Observer 같은 패턴을 조합해 만들어져 있다.

## 먼저 볼 우선순위

| 우선순위 | 패턴 | 백엔드에서 자주 보이는 위치 |
| --- | --- | --- |
| 매우 높음 | Strategy | 정책 교체, 결제·할인·인증 구현 선택 |
| 매우 높음 | Factory | 객체 생성 규칙, 구현체 선택 |
| 매우 높음 | Builder | 복잡한 객체와 테스트 fixture 생성 |
| 매우 높음 | Adapter | 외부 API, DB, Message Broker 경계 |
| 매우 높음 | Proxy | Transaction, Security, Cache, AOP |
| 높음 | Template/Callback | JDBC, Transaction, 반복 실행 흐름 |
| 높음 | Chain of Responsibility | Servlet Filter, Security Filter Chain |
| 높음 | Observer | Spring Event, Domain Event |
| 중간 | Decorator | 기능을 조합하는 wrapper |
| 중간 | Facade | 복잡한 subsystem의 단순 진입점 |
| 중간 | Singleton | Spring Bean scope와 공유 상태 |
| 필요할 때 | Command, State | 작업 객체화, 복잡한 상태 전이 |

## 1. Strategy Pattern

Strategy는 자주 사용되는 핵심 패턴이다.

### 해결하려는 문제

같은 목적의 알고리즘이나 정책이 여러 개 있고 실행 시점에 하나를 선택해야 하는 상황을 생각한다.

```java
public int calculateDiscount(String grade, int price) {
    if (grade.equals("BASIC")) {
        return 0;
    }
    if (grade.equals("VIP")) {
        return price * 10 / 100;
    }
    if (grade.equals("VVIP")) {
        return price * 20 / 100;
    }
    throw new IllegalArgumentException("unsupported grade");
}
```

정책이 추가될 때마다 기존 method를 수정해야 한다. 할인 선택과 할인 계산 책임도 한곳에 섞여 있다.

Strategy는 변하는 알고리즘을 interface 뒤로 분리한다.

```text
Context
→ Strategy를 사용해 전체 흐름 실행

Strategy
→ 교체 가능한 알고리즘 계약

Concrete Strategy
→ 실제 알고리즘 구현
```

### 기본 구조

```java
public interface DiscountPolicy {
    MemberGrade supports();
    Money discount(Money price);
}
```

```java
@Component
public class VipDiscountPolicy implements DiscountPolicy {
    @Override
    public MemberGrade supports() {
        return MemberGrade.VIP;
    }

    @Override
    public Money discount(Money price) {
        return price.percentage(10);
    }
}
```

```java
@Service
public class DiscountService {
    private final Map<MemberGrade, DiscountPolicy> policies;

    public DiscountService(List<DiscountPolicy> policies) {
        this.policies = policies.stream()
            .collect(Collectors.toUnmodifiableMap(
                DiscountPolicy::supports,
                Function.identity()
            ));
    }

    public Money discount(MemberGrade grade, Money price) {
        DiscountPolicy policy = Optional.ofNullable(policies.get(grade))
            .orElseThrow(() -> new IllegalArgumentException(
                "unsupported grade: " + grade
            ));
        return policy.discount(price);
    }
}
```

Spring DI는 모든 `DiscountPolicy` Bean을 `List`로 주입할 수 있다. Context는 concrete class를 직접 만들지 않고 등록된 전략을 사용한다.

### Strategy와 if 문

Strategy를 사용해도 어떤 전략을 선택할지는 결정해야 한다. 조건문이 완전히 사라지는 것이 아니라 선택 책임이 한 곳으로 이동한다.

```text
나쁜 이동
→ 각 Controller와 Service가 같은 switch문을 반복

좋은 이동
→ 전용 resolver가 업무 key와 Strategy mapping을 관리
```

분기가 두 개이고 거의 변하지 않는다면 단순한 `if`가 더 읽기 쉬울 수 있다. 다음 조건이 있을 때 Strategy의 가치가 커진다.

```text
정책이 계속 추가됨
정책별 logic이 길고 독립적임
정책마다 외부 dependency가 다름
정책을 개별 unit test해야 함
실행 시점에 구현을 선택해야 함
```

### Spring에서 보이는 Strategy

```text
PasswordEncoder
→ 암호화 algorithm 전략

AuthenticationProvider
→ 인증 방식 전략

HttpMessageConverter
→ HTTP body 변환 전략

CacheManager
→ Cache 구현 선택

PlatformTransactionManager
→ Transaction 기술별 전략
```

### Strategy 설계 주의점

Strategy interface를 기술적인 method 하나로만 만들지 말고 업무 의도가 드러나게 한다.

```java
// 의미가 약함
interface Processor {
    Object process(Object input);
}

// 업무 의도가 명확함
interface PaymentProcessor {
    PaymentResult pay(PaymentCommand command);
}
```

구현체 선택 key를 임의 문자열로 흩뿌리지 않는다. enum, value object, provider identifier처럼 허용 범위가 명확한 타입을 사용한다.

## 2. Factory Pattern

Factory는 객체 생성의 책임과 규칙을 사용하는 쪽에서 분리한다.

### 생성자 호출이 항상 나쁜 것은 아니다

```java
Money money = new Money(10_000, KRW);
```

생성이 단순하고 유효성 규칙이 생성자에 잘 드러난다면 직접 생성해도 된다. Factory는 다음처럼 생성이 복잡할 때 의미가 있다.

```text
생성할 concrete type을 실행 시점에 선택
여러 객체를 일관된 조합으로 생성
생성 과정에 이름 있는 업무 규칙이 필요
생성 과정이 호출자 여러 곳에 중복
외부 입력을 domain object로 변환
```

### Simple Factory, Factory Method, Abstract Factory

| 구분 | 핵심 | 사용 기준 |
| --- | --- | --- |
| Static/Named Factory | class의 이름 있는 생성 method | 생성 의도를 드러내고 instance 제어 |
| Simple Factory | 한 Factory가 type을 선택해 생성 | 작은 생성 분기를 중앙화 |
| Factory Method | 하위 class나 구현체가 생성 method를 결정 | 상속 기반 framework 확장 |
| Abstract Factory | 연관된 여러 객체 family를 일관되게 생성 | 제품군 전체 교체 |

Simple Factory는 GoF 공식 패턴 이름은 아니지만 실무에서 흔히 사용하는 구조다.

### Named Factory Method

도메인 객체의 생성 의도를 드러낼 때 유용하다.

```java
public class Member {
    private Member(String email, MemberStatus status) {
        this.email = email;
        this.status = status;
    }

    public static Member register(String email) {
        validateEmail(email);
        return new Member(email, MemberStatus.ACTIVE);
    }

    public static Member restore(String email, MemberStatus status) {
        return new Member(email, status);
    }
}
```

```text
new Member(...)
→ parameter만 보고 생성 목적을 알기 어려움

Member.register(...)
→ 신규 가입이라는 생성 의도와 규칙이 드러남
```

### 구현체 선택 Factory

```java
public interface PaymentClient {
    PaymentProvider provider();
    PaymentResult pay(PaymentRequest request);
}
```

```java
@Component
public class PaymentClientFactory {
    private final Map<PaymentProvider, PaymentClient> clients;

    public PaymentClientFactory(List<PaymentClient> clients) {
        this.clients = clients.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentClient::provider,
                Function.identity()
            ));
    }

    public PaymentClient get(PaymentProvider provider) {
        return Optional.ofNullable(clients.get(provider))
            .orElseThrow(() -> new IllegalArgumentException(
                "unsupported provider: " + provider
            ));
    }
}
```

이 Factory는 객체를 매번 `new`로 생성하지 않고 Spring이 생성한 Bean 중 적합한 구현체를 찾아준다. Factory의 핵심은 반드시 새 객체를 만드는 것이 아니라 생성 또는 선택 책임을 감추는 것이다.

### Abstract Factory가 필요한 경우

연관된 구현 묶음이 항상 함께 바뀌어야 할 때 사용한다.

```text
LocalPaymentFactory
→ LocalPaymentClient
→ LocalPaymentVerifier
→ LocalPaymentRefundClient

GlobalPaymentFactory
→ GlobalPaymentClient
→ GlobalPaymentVerifier
→ GlobalPaymentRefundClient
```

객체 하나만 선택하면 Strategy나 Simple Factory면 충분하다. 제품군이 없는데 Abstract Factory를 사용하면 interface와 class만 늘어난다.

### Spring의 Factory 개념

```text
BeanFactory
→ Bean 생성과 조회의 기본 container 계약

FactoryBean<T>
→ 복잡한 객체 T를 만들어 container에 제공하는 Bean

ObjectProvider<T>
→ 필요한 시점에 Bean을 안전하게 조회하거나 선택
```

`ApplicationContext.getBean()`을 business code 곳곳에서 호출하면 Service Locator 형태가 되어 dependency가 숨겨진다. 일반적인 dependency는 생성자 주입으로 명시하고, 동적 조회가 정말 필요한 제한된 경계에서만 provider나 factory를 사용한다.

## 3. Builder Pattern

Builder는 parameter가 많거나 생성 과정이 단계적인 객체를 읽기 쉽게 만든다.

### Telescoping Constructor 문제

```java
new Product("keyboard", 50_000, null, true, false, 0, null);
```

각 parameter의 의미를 호출부에서 알기 어렵고 순서를 바꾸는 실수가 생긴다.

```java
Product product = Product.builder()
    .name("keyboard")
    .price(Money.won(50_000))
    .stock(100)
    .saleEnabled(true)
    .build();
```

### Builder가 책임져야 할 것

Builder는 값만 모으는 것이 아니라 최종 객체가 유효한 상태인지 `build()` 시점에 보장해야 한다.

```java
public final class Product {
    private final String name;
    private final Money price;
    private final int stock;

    private Product(Builder builder) {
        this.name = requireName(builder.name);
        this.price = requirePositive(builder.price);
        this.stock = requireNonNegative(builder.stock);
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String name;
        private Money price;
        private int stock;

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder price(Money price) {
            this.price = price;
            return this;
        }

        public Builder stock(int stock) {
            this.stock = stock;
            return this;
        }

        public Product build() {
            return new Product(this);
        }
    }
}
```

### Builder가 잘 맞는 대상

```text
필드가 많은 immutable response DTO
선택 parameter가 많은 설정 객체
테스트 fixture와 Test Data Builder
여러 단계로 조립되는 복합 객체
```

단순히 필드가 두세 개인 객체라면 constructor나 static factory가 더 명확하다.

### Lombok @Builder 주의점

Lombok은 boilerplate를 줄이지만 유효성 규칙을 자동으로 만들어주지 않는다.

```text
모든 필드를 선택값처럼 보이게 함
필수값 누락을 compile 시점에 막지 못함
Entity의 의미 있는 생성 규칙을 우회할 수 있음
필드명이 바뀌면 호출부가 함께 바뀜
```

JPA Entity에 무조건 `@Builder`를 붙이기보다 업무 생성 method가 Entity의 불변식을 보장하게 하고, Builder는 DTO나 test fixture처럼 적합한 위치에 사용한다.

## 4. Adapter Pattern

Adapter는 서로 다른 interface를 연결한다. 백엔드에서는 외부 시스템을 application의 언어로 바꾸는 경계에 매우 자주 사용한다.

### 해결하려는 문제

결제사의 SDK와 response model을 Service가 직접 사용한다고 가정한다.

```java
TossPaymentResponse response = tossSdk.approve(...);
if (response.getTossResultCode().equals("0000")) {
    // business logic
}
```

Service가 provider의 class, error code와 field 이름을 알게 된다. provider 변경이 business logic까지 전파된다.

### Port와 Adapter 구조

Application이 필요한 계약을 먼저 정의한다.

```java
public interface PaymentPort {
    PaymentResult pay(PaymentCommand command);
    PaymentResult cancel(PaymentCancelCommand command);
}
```

외부 시스템별 Adapter가 계약을 구현한다.

```java
@Component
public class TossPaymentAdapter implements PaymentPort {
    private final TossApiClient client;

    @Override
    public PaymentResult pay(PaymentCommand command) {
        TossPaymentRequest request = TossPaymentMapper.toRequest(command);

        try {
            TossPaymentResponse response = client.pay(request);
            return TossPaymentMapper.toResult(response);
        } catch (TossTimeoutException e) {
            throw new PaymentTemporaryException(e);
        } catch (TossRejectedException e) {
            throw new PaymentRejectedException(e.getCode(), e);
        }
    }
}
```

```text
Application model
→ Adapter가 provider request로 변환
→ 외부 API 호출
→ Adapter가 provider response를 application result로 변환
→ provider error를 application exception으로 변환
```

Adapter는 단순 method 이름 변환을 넘어 외부 시스템의 개념이 내부 domain을 오염시키지 않게 하는 Anti-Corruption Layer 역할을 할 수 있다.

### Spring에서 보이는 Adapter

```text
HandlerAdapter
→ 서로 다른 handler 형태를 DispatcherServlet이 같은 방식으로 실행

JpaRepository 구현 Adapter
→ application의 repository 요구를 JPA로 구현

Message Consumer Adapter
→ Kafka/RabbitMQ message를 application command로 변환

External API Adapter
→ provider DTO와 error를 application model로 변환
```

### Adapter 설계 주의점

```text
provider DTO를 Controller response로 그대로 노출하지 않음
provider error code를 Domain 전체에 퍼뜨리지 않음
Adapter에 핵심 업무 규칙을 넣지 않음
HTTP client와 mapping, timeout 책임을 무한히 한 class에 몰지 않음
```

Adapter는 외부 기술을 숨기지만 외부 시스템의 실제 제약까지 없애지는 못한다. 멱등성 key, timeout, rate limit처럼 application이 알아야 하는 계약은 명시적으로 port에 표현한다.

## 5. Proxy Pattern

Proxy는 실제 객체와 같은 interface를 제공하면서 호출 앞뒤에 접근 제어, 지연 로딩, transaction 같은 기능을 추가한다.

```text
Caller
→ Proxy
→ 부가 처리
→ Target
→ 부가 처리
→ Caller
```

### Proxy 종류

```text
Virtual Proxy
→ 실제 객체 생성을 필요할 때까지 지연

Protection Proxy
→ 권한에 따라 접근 통제

Remote Proxy
→ 원격 객체 호출을 local 객체처럼 표현

Caching Proxy
→ 동일 호출 결과를 cache

AOP Proxy
→ method 호출 전후에 advice 적용
```

### Spring AOP Proxy

```java
@Transactional
public Order createOrder(CreateOrderCommand command) {
    return orderRepository.save(Order.create(command));
}
```

호출자가 실제 `OrderService`를 바로 호출하는 것이 아니라 Spring이 만든 proxy를 호출한다.

```text
Proxy method 진입
→ Transaction 시작
→ 실제 Service method 호출
→ 성공하면 commit, 실패하면 rollback
→ connection 정리
```

같은 원리로 `@Cacheable`, `@Async`, method security와 custom AOP가 적용될 수 있다.

### JDK Dynamic Proxy와 Class 기반 Proxy

```text
JDK Dynamic Proxy
→ interface를 구현한 proxy

Class 기반 Proxy
→ 대상 class를 상속한 proxy
```

구현 방식보다 중요한 것은 외부 호출이 proxy를 지나야 한다는 점이다.

```java
public void outer() {
    inner();
}

@Transactional
public void inner() {
}
```

`outer()`에서 `inner()`를 직접 호출하면 `this.inner()`이므로 proxy를 다시 거치지 않는다. 이를 Self Invocation 문제라고 한다.

해결 방향:

```text
Transaction 경계를 외부에서 호출되는 public method에 둠
서로 다른 transaction 책임을 별도 Bean으로 분리
업무 흐름과 기술 경계를 다시 검토
```

자기 자신을 다시 주입하거나 `AopContext`로 현재 proxy를 꺼내는 방식은 구조를 숨기므로 일반적인 해결책으로 두지 않는다.

### Proxy 설계 주의점

```text
private method는 일반적인 proxy interception 대상이 아님
final method와 final class는 class 기반 proxy에 제약
생성자 내부 호출은 완성된 proxy 호출이 아님
annotation을 붙였다고 모든 호출 경로에서 적용되는 것은 아님
proxy가 감싼 객체의 실제 type과 equals/hashCode 가정을 조심
```

Spring Proxy와 AOP는 [Spring Core 문서](06-spring-core-ioc-di-bean.md), transaction 문제는 [Transaction 문서](11-transaction.md)에서 더 연결해서 본다.

## 6. Template Method와 Callback

Template Method는 전체 algorithm의 뼈대는 부모 class에 두고 일부 단계만 자식이 바꾸게 한다.

### Template Method 구조

```java
public abstract class ImportJob {
    public final ImportResult execute(Path path) {
        validate(path);
        List<Row> rows = read(path);
        List<Row> converted = convert(rows);
        save(converted);
        return summarize(converted);
    }

    protected abstract List<Row> read(Path path);
    protected abstract List<Row> convert(List<Row> rows);

    protected void validate(Path path) {
        // 공통 검증
    }

    protected abstract void save(List<Row> rows);
}
```

```text
고정된 흐름
→ validate → read → convert → save → summarize

변경 지점
→ 파일 형식별 read와 convert
```

### Template Method의 비용

상속을 사용하므로 부모와 자식이 강하게 결합한다.

```text
부모 실행 순서를 이해해야 자식 구현 가능
hook method가 늘어나면 흐름이 복잡
실행 시점에 algorithm 조합을 바꾸기 어려움
상속 계층이 깊어질 수 있음
```

변경 단계를 객체나 함수로 전달하는 Template Callback 방식이 더 유연할 수 있다.

### Template Callback

```java
public <T> T executeInTransaction(Supplier<T> callback) {
    begin();
    try {
        T result = callback.get();
        commit();
        return result;
    } catch (RuntimeException e) {
        rollback();
        throw e;
    } finally {
        cleanup();
    }
}
```

```java
Order order = transactionTemplate.execute(
    status -> orderRepository.save(Order.create(command))
);
```

```text
Template
→ 반복되는 resource 획득, 예외 변환, 정리 흐름 담당

Callback
→ 상황마다 달라지는 핵심 작업만 전달
```

### Spring의 Template

```text
JdbcTemplate
→ Connection, Statement, ResultSet 처리와 예외 변환

TransactionTemplate
→ Transaction 시작, commit, rollback

RedisTemplate
→ Redis serialization과 command 실행

JmsTemplate
→ JMS resource와 message 송수신 흐름
```

Template가 해결하는 핵심은 반복되는 `try-catch-finally`와 resource 관리를 framework가 가져가는 것이다.

## 7. Chain of Responsibility

Chain of Responsibility는 요청을 여러 handler가 순서대로 처리하게 한다. 각 handler는 요청을 처리하고 다음 handler로 넘기거나 chain을 중단한다.

```text
Request
→ Logging Handler
→ Authentication Handler
→ Authorization Handler
→ Controller
```

### 기본 구조

```java
public interface RequestHandler {
    void handle(RequestContext context, HandlerChain chain);
}
```

```java
public class AuthenticationHandler implements RequestHandler {
    @Override
    public void handle(RequestContext context, HandlerChain chain) {
        Authentication authentication = authenticate(context);
        context.setAuthentication(authentication);
        chain.next(context);
    }
}
```

인증에 실패하면 예외를 던지거나 응답을 완성하고 `chain.next()`를 호출하지 않아 흐름을 중단할 수 있다.

### Spring에서 보이는 Chain

```text
Servlet Filter Chain
→ HTTP 요청 전후 처리

Spring Security Filter Chain
→ 인증, 인가, exception translation

HandlerInterceptor Chain
→ Controller 실행 전후 처리

Validation/Processing Pipeline
→ 여러 검증 또는 변환 단계를 순서대로 적용
```

### 순서가 계약이다

Chain에서는 handler 순서가 동작을 바꾼다.

```text
CORS 처리
→ 인증보다 먼저 필요한가?

Exception 변환
→ 예외를 던지는 handler보다 바깥에 있는가?

Logging
→ request body를 먼저 소비하지 않는가?

Authorization
→ Authentication 이후에 실행되는가?
```

`@Order` 숫자만 흩어두기보다 configuration에서 chain 순서를 읽을 수 있게 구성하고 순서가 중요한 흐름은 integration test로 검증한다.

### Chain을 쓰지 말아야 할 때

핵심 업무 흐름을 보이지 않는 handler chain에 숨기면 실행 순서를 찾기 어렵다.

```text
기술적인 request 전처리
→ Chain에 적합

주문 생성 → 결제 → 재고 차감
→ 명시적인 Application Service 흐름이 더 적합
```

## 8. Observer Pattern

Observer는 한 객체의 event를 여러 subscriber가 통지받게 한다. 발행자는 subscriber의 concrete type을 몰라도 된다.

```text
Order
→ OrderCompleted event 발행
→ Point Listener
→ Notification Listener
→ Analytics Listener
```

### Spring Application Event

```java
public record OrderCompletedEvent(
    Long orderId,
    Long memberId,
    Instant occurredAt
) {
}
```

```java
applicationEventPublisher.publishEvent(
    new OrderCompletedEvent(order.id(), order.memberId(), clock.instant())
);
```

```java
@EventListener
public void handle(OrderCompletedEvent event) {
    pointService.earnForOrder(event.orderId(), event.memberId());
}
```

Spring application event listener는 별도 설정이 없다면 같은 process와 호출 thread에서 동기 실행될 수 있다. listener가 느리거나 실패하면 원래 요청의 latency와 성공 여부에 영향을 줄 수 있다.

### Transaction과 Event 시점

```text
Transaction commit 전 listener
→ 같은 transaction에 참여할 수 있음
→ listener 실패가 원 transaction을 rollback시킬 수 있음

AFTER_COMMIT listener
→ commit된 결과를 기준으로 후속 작업
→ 후속 작업 실패를 원 transaction rollback으로 되돌릴 수 없음
```

`@TransactionalEventListener`의 phase를 선택할 때 data가 실제로 commit됐는지와 후속 작업 실패를 어떻게 복구할지 정한다.

### 내부 Event와 외부 Message

```text
Spring Application Event
→ 같은 application process 안의 결합 완화

Kafka/RabbitMQ Message
→ 다른 process와 비동기 통신
```

Application event를 발행했다고 broker에 안전하게 전달되는 것은 아니다. DB 변경과 외부 event 발행의 원자성 문제가 있다면 Transactional Outbox와 consumer idempotency를 사용한다.

### Observer 주의점

```text
listener가 많아지면 전체 실행 흐름을 찾기 어려움
listener 순서에 의존하면 느슨한 결합이라는 장점이 사라짐
같은 event의 중복 처리 가능성을 고려
event 이름은 명령보다 이미 발생한 과거형 사실로 표현
핵심 불변식은 비동기 listener에 맡기지 않음
```

## 9. Decorator Pattern

Decorator는 같은 interface를 구현한 wrapper를 겹겹이 조합해 기능을 추가한다.

```java
public interface NotificationSender {
    void send(Notification notification);
}
```

```java
public class EmailNotificationSender implements NotificationSender {
    @Override
    public void send(Notification notification) {
        // 실제 email 발송
    }
}
```

```java
public class RetryNotificationDecorator implements NotificationSender {
    private final NotificationSender delegate;

    @Override
    public void send(Notification notification) {
        retryTemplate.execute(context -> {
            delegate.send(notification);
            return null;
        });
    }
}
```

```java
NotificationSender sender =
    new MetricsNotificationDecorator(
        new RetryNotificationDecorator(
            new EmailNotificationSender()
        )
    );
```

상속으로 모든 조합을 만들지 않고 object composition으로 기능을 선택적으로 쌓을 수 있다.

Retry Decorator를 적용할 때는 대상 작업이 멱등한지 확인한다. Email이나 외부 결제처럼 부수 효과가 있는 작업을 결과 확인 없이 다시 실행하면 중복 발송이나 중복 처리가 생길 수 있다.

### Decorator와 Proxy 차이

두 패턴 모두 같은 interface를 구현하고 대상 객체를 감쌀 수 있다.

```text
Decorator
→ 기능 조합과 확장이 주목적

Proxy
→ 실제 객체에 대한 접근 통제와 간접 호출이 주목적
```

구조가 비슷하므로 이름보다 설계 의도를 본다.

Decorator를 너무 많이 겹치면 실제 호출 순서를 이해하기 어려워진다. 조합을 configuration 한곳에서 만들고 각 decorator는 하나의 부가 책임에 집중한다.

## 10. Facade Pattern

Facade는 복잡한 subsystem에 단순한 진입 interface를 제공한다.

```text
Controller
→ OrderFacade.placeOrder(command)
→ Member 조회
→ Coupon 확인
→ Stock 예약
→ Payment 요청
→ Order 저장
```

Controller가 여러 Service와 Repository를 직접 조율하는 대신 application use case가 흐름을 제공한다.

```java
@Service
public class OrderFacade {
    public OrderResult placeOrder(PlaceOrderCommand command) {
        // use case 흐름 조율
    }
}
```

Facade는 내부 subsystem의 복잡성을 숨기지만 Domain 규칙을 모두 가져가는 God Service가 되어서는 안 된다.

```text
Facade/Application Service
→ use case 순서와 transaction 조율

Domain Object/Domain Service
→ 주문 가능 여부, 가격 계산, 상태 전이 규칙

Adapter
→ DB와 외부 API 기술 세부사항
```

`Facade`라는 suffix 자체가 좋은 설계를 보장하지 않는다. public method가 너무 많고 모든 domain을 참조한다면 업무 경계가 지나치게 넓은지 확인한다.

## 11. Singleton Pattern과 Spring Singleton Bean

Singleton Pattern은 한 class의 instance가 하나만 존재하도록 생성과 접근을 통제한다.

```java
public final class AppSettings {
    private static final AppSettings INSTANCE = new AppSettings();

    private AppSettings() {
    }

    public static AppSettings getInstance() {
        return INSTANCE;
    }
}
```

하지만 Spring에서는 직접 Singleton 코드를 작성하기보다 container가 Bean scope를 관리한다.

### 차이

```text
GoF Singleton
→ class 자체가 instance 생성과 global 접근을 통제

Spring singleton scope
→ ApplicationContext가 Bean 이름별로 instance 하나를 관리
→ 같은 class도 서로 다른 Bean 이름으로 여러 instance 등록 가능
```

Spring singleton은 JVM 전체에 무조건 하나라는 뜻이 아니다. ApplicationContext가 여러 개거나 application instance가 여러 대면 각각 별도 Bean이 존재한다.

### Thread Safety

singleton Bean 하나가 여러 요청 thread에 공유되므로 mutable 요청 상태를 field에 저장하면 안 된다.

```java
@Service
public class BadOrderService {
    private Long currentMemberId;

    public void order(Long memberId) {
        this.currentMemberId = memberId;
    }
}
```

Service는 가능하면 stateless하게 만들고 요청별 값은 method local variable, parameter와 별도 request scope 객체에 둔다.

Singleton은 편리한 global variable을 만드는 수단이 아니다. 숨겨진 global state는 test 격리, 동시성, 초기화 순서와 dependency 추적을 어렵게 한다.

## 12. Command Pattern

Command는 실행할 요청을 객체로 표현한다.

```java
public record CancelOrderCommand(
    Long orderId,
    Long requesterId,
    String reason
) {
}
```

장점:

```text
요청 data와 실행 시점을 분리
Queue에 저장하거나 나중에 실행 가능
retry, audit, 권한 검사 metadata 결합 가능
use case input을 명확한 type으로 표현
```

CQRS의 Command는 상태를 변경하려는 의도를 나타낸다. GoF Command와 완전히 같은 문맥은 아니지만 요청을 객체화한다는 핵심은 연결된다.

모든 Service method마다 의미 없는 `SomethingCommand`를 만들 필요는 없다. parameter가 많거나 use case 계약을 계층 밖으로 전달하고, message나 batch처럼 실행 시점이 분리될 때 가치가 크다.

## 13. State Pattern

State는 객체 상태에 따라 행동이 달라질 때 상태별 행동을 객체로 분리한다.

```java
public void cancel() {
    switch (status) {
        case CREATED -> status = CANCELED;
        case PAID -> refundAndCancel();
        case SHIPPED -> throw new IllegalStateException("already shipped");
        default -> throw new IllegalStateException("cannot cancel");
    }
}
```

상태와 동작이 계속 늘어나면 `OrderState` 구현체로 전이를 분리할 수 있다.

```text
CreatedState
→ pay, cancel 허용

PaidState
→ ship, refund 허용

ShippedState
→ deliver 허용, cancel 거부
```

State Pattern은 상태가 많고 상태별 동작과 전이 규칙이 복잡할 때 유용하다. 상태가 3~4개이고 전이가 단순하다면 enum과 명시적인 Domain method가 더 읽기 쉽다.

상태 전이는 application memory뿐 아니라 DB transaction과 동시 요청에서도 안전해야 한다. State Pattern만으로 동시성을 해결할 수 없으므로 optimistic lock, conditional update와 업무 idempotency를 함께 고려한다.

## 패턴들이 함께 동작하는 예시

결제 요청 하나에도 여러 패턴이 조합될 수 있다.

```text
Controller
→ PlaceOrderCommand 생성
  Command

OrderFacade.placeOrder
→ 전체 use case 조율
  Facade

PaymentClientFactory
→ provider 구현체 선택
  Factory

PaymentPolicy
→ 결제 방식별 정책 실행
  Strategy

TossPaymentAdapter
→ application model과 Toss API 변환
  Adapter

@Transactional OrderService
→ transaction advice 적용
  Proxy

SecurityFilterChain
→ 인증·인가 handler 순차 실행
  Chain of Responsibility

OrderCompletedEvent
→ 후속 listener 통지
  Observer
```

실제 code에서는 이 이름을 모두 class suffix로 붙일 필요가 없다. 객체의 책임과 협력 구조가 패턴의 의도를 만족하는지가 중요하다.

## 비슷한 패턴 구분

### Strategy와 State

```text
Strategy
→ Context 외부에서 algorithm을 선택
→ 같은 목적의 정책 교체

State
→ 객체 내부 상태 변화에 따라 행동과 다음 상태가 달라짐
→ 상태 전이 자체가 중요
```

### Strategy와 Template Method

```text
Strategy
→ 조합 기반
→ 실행 시점에 구현 교체가 쉬움

Template Method
→ 상속 기반
→ 전체 흐름은 부모가 고정하고 일부 단계만 override
```

### Adapter와 Facade

```text
Adapter
→ 호환되지 않는 interface를 원하는 interface로 변환

Facade
→ 여러 subsystem을 하나의 단순한 진입점 뒤로 숨김
```

### Proxy와 Decorator

```text
Proxy
→ 대상 접근을 통제하거나 간접화

Decorator
→ 동일 계약을 유지하며 기능을 조합해 확장
```

### Factory와 Builder

```text
Factory
→ 무엇을 생성할지와 concrete type 선택에 초점

Builder
→ 복잡한 한 객체를 어떤 단계와 값으로 조립할지에 초점
```

## 패턴 선택 기준

| 문제 신호 | 먼저 검토할 패턴 |
| --- | --- |
| 같은 목적의 조건 분기가 계속 증가 | Strategy |
| 객체 생성 조건과 조립이 여러 곳에 중복 | Factory |
| 생성자 parameter가 많고 선택값이 많음 | Builder |
| 외부 API model이 Domain까지 침투 | Adapter |
| 호출 전후에 공통 기술 기능 필요 | Proxy, Decorator |
| 실행 흐름은 같고 일부 단계만 다름 | Template/Callback |
| 여러 전처리기를 순서대로 통과 | Chain of Responsibility |
| 한 사건 뒤 독립적인 후속 처리 여러 개 | Observer |
| 여러 subsystem 호출을 단순하게 제공 | Facade |
| 상태별 허용 행동과 전이가 복잡 | State |

## 패턴을 적용하기 전에 할 질문

```text
실제로 자주 바뀌는 부분은 어디인가?
변경 이유가 다른 책임이 한 class에 섞여 있는가?
구현체가 정말 둘 이상이거나 교체 가능성이 구체적인가?
단순한 method 분리와 조합으로 충분하지 않은가?
새 interface가 업무 의미를 명확하게 만드는가?
패턴 적용 뒤 호출 흐름을 더 쉽게 추적할 수 있는가?
unit test가 쉬워지는가?
운영 장애 시 실제 구현체와 실행 순서를 찾을 수 있는가?
```

하나라도 답하기 어렵다면 패턴 이름보다 문제 정의를 먼저 다듬는다.

## 자주 하는 실수

```text
구현체가 하나인데 모든 class에 interface 생성
두 줄짜리 생성자를 위해 Factory 계층 여러 개 생성
모든 DTO와 Entity에 Builder 적용
비즈니스 흐름을 Event와 AOP 뒤에 숨김
Strategy 선택을 문자열 Bean 이름에 과하게 의존
Facade가 모든 Domain을 참조하는 God Service가 됨
Singleton Bean field에 요청 상태 저장
외부 provider DTO를 Adapter 밖으로 노출
Chain 순서를 annotation 숫자에만 의존하고 test하지 않음
패턴 class 이름은 있지만 책임 경계는 그대로임
```

패턴을 적용한 결과 파일 수만 늘고 변경 범위, test 가능성, 의존 방향이 나아지지 않았다면 과도한 설계일 가능성이 높다.

## 학습 순서

```text
1. Strategy
→ 다형성과 DI 연결

2. Factory와 Builder
→ 객체 생성 책임 분리

3. Adapter와 Facade
→ application 경계 설계

4. Proxy
→ Spring AOP와 Transaction 이해

5. Template/Callback과 Chain
→ framework 내부 반복 흐름 이해

6. Observer
→ Domain Event와 Message 연계

7. Decorator, Command, State
→ 실제 문제에서 필요할 때 확장
```

## 설명할 때 핵심 문장

```text
디자인 패턴은 반복되는 설계 문제를 해결하는 객체 협력 구조이며, class 수를 늘리는 것이 목적이 아니다.
Strategy는 변하는 정책을 interface 뒤로 분리하고 Spring DI로 구현체를 선택할 수 있게 한다.
Factory는 객체 생성과 구현 선택 책임을 분리하고 Builder는 복잡한 한 객체의 조립 과정을 읽기 쉽게 만든다.
Adapter는 외부 시스템의 모델을 application 계약으로 변환하고 Proxy는 대상 호출 앞뒤에 transaction 같은 기능을 적용한다.
Template과 Callback은 반복 실행 흐름을 재사용하고 Chain은 여러 handler를 순서대로 연결한다.
Observer는 한 사건의 후속 처리를 분리하지만 transaction 시점, 실패와 중복 처리를 함께 설계해야 한다.
패턴은 실제 변경 압력과 복잡성이 있을 때 사용하고 단순한 문제에는 단순한 code를 유지한다.
```

## 공식 참고 자료

- [Spring Framework - IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html)
- [Spring Framework - AOP with Spring](https://docs.spring.io/spring-framework/reference/core/aop.html)
- [Spring Framework - Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction.html)
- [Spring Framework - Application Events](https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html#context-functionality-events)
- [Spring Framework - JDBC Core](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)
- [Spring Framework - Spring MVC DispatcherServlet](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html)
