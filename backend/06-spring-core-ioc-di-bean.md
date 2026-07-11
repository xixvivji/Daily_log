# 06. Spring Core: IoC, DI, Bean

## Spring Core가 중요한 이유

Spring의 핵심은 객체를 직접 만들고 연결하는 일을 개발자가 모두 하지 않아도 되게 하는 것이다.

즉 Spring은 객체 생성, 의존관계 연결, 생명주기 관리를 담당한다.

핵심 개념:

```text
IoC
DI
Bean
ApplicationContext
Component Scan
Configuration
```

## IoC

IoC는 Inversion of Control이다.

제어의 역전이라는 뜻이다.

일반 Java 코드에서는 객체를 직접 생성한다.

```java
OrderService service = new OrderService(new OrderRepository());
```

Spring에서는 객체 생성과 주입을 Spring Container가 담당한다.

```text
개발자
→ 객체 설계

Spring Container
→ 객체 생성
→ 의존관계 주입
→ 생명주기 관리
```

제어권이 개발자 코드에서 프레임워크로 넘어갔기 때문에 IoC라고 한다.

## DI

DI는 Dependency Injection이다.

객체가 필요한 의존 객체를 직접 만들지 않고 외부에서 주입받는 방식이다.

나쁜 예:

```java
public class OrderService {
    private final OrderRepository repository = new OrderRepository();
}
```

좋은 예:

```java
public class OrderService {
    private final OrderRepository repository;

    public OrderService(OrderRepository repository) {
        this.repository = repository;
    }
}
```

장점:

```text
구현체 교체 쉬움
테스트 쉬움
객체 간 결합도 감소
Spring이 의존관계 관리 가능
```

## Bean

Bean은 Spring Container가 관리하는 객체다.

```java
@Service
public class OrderService {
}
```

`@Service`가 붙은 클래스는 component scan을 통해 Bean으로 등록될 수 있다.

대표 stereotype:

```text
@Component
@Controller
@RestController
@Service
@Repository
```

## ApplicationContext

ApplicationContext는 Spring Container다.

역할:

```text
Bean 생성
Bean 조회
의존관계 주입
환경 설정 관리
이벤트 발행
메시지 처리
```

Spring Boot 애플리케이션이 시작될 때 ApplicationContext가 만들어지고 Bean들이 등록된다.

## Component Scan

Component Scan은 특정 패키지 아래에서 `@Component` 계열 애노테이션이 붙은 클래스를 찾아 Bean으로 등록한다.

```java
@SpringBootApplication
public class Application {
}
```

`@SpringBootApplication` 안에는 component scan 설정이 포함되어 있다.

일반적으로 main class가 있는 패키지 하위가 scan 대상이다.

## @Configuration과 @Bean

직접 Bean을 등록할 수도 있다.

```java
@Configuration
public class AppConfig {
    @Bean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
```

언제 쓰는가:

```text
외부 라이브러리 객체를 Bean으로 등록
생성 로직이 필요한 객체 등록
설정 값 기반으로 객체 생성
```

## Bean Scope

기본 Bean scope는 singleton이다.

```text
Spring Container 안에서 하나의 Bean instance를 공유
```

주의:

```text
Singleton Bean에 mutable state를 두면 동시성 문제가 생길 수 있다.
```

나쁜 예:

```java
@Service
public class OrderService {
    private Long currentUserId;
}
```

요청마다 달라지는 상태를 singleton Bean 필드에 저장하면 안 된다.

## 생성자 주입을 권장하는 이유

Spring에서는 생성자 주입을 기본 선택으로 두는 것이 좋다.

```java
@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

```text
필수 의존성을 객체 생성 시점에 보장
필드를 final로 만들 수 있음
Spring 없이도 생성자를 호출해 단위 테스트 가능
의존성이 너무 많아진 설계 문제를 쉽게 발견
```

필드 주입은 코드가 짧지만 컨테이너 밖에서 객체를 만들기 어렵고 필수 의존성이 드러나지 않는다. 선택 의존성이 꼭 필요할 때는 setter나 명시적인 설정 방식을 검토할 수 있다.

## 같은 타입의 Bean이 여러 개일 때

하나의 interface를 구현한 Bean이 여러 개면 Spring은 어떤 객체를 주입할지 결정할 수 없다.

```text
@Primary
→ 같은 타입 중 기본 Bean 지정

@Qualifier("tossPaymentClient")
→ 이름으로 주입 대상 지정

Map<String, PaymentClient>
→ 모든 구현체를 전략 목록으로 주입
```

구현체 선택이 비즈니스 규칙이라면 `if`를 여러 Service에 흩뜨리지 말고 전략을 선택하는 별도 객체에 모은다.

## Bean 생명주기

일반적인 singleton Bean은 대략 다음 순서로 준비된다.

```text
Bean definition 등록
→ 객체 생성
→ 의존관계 주입
→ BeanPostProcessor 전처리
→ 초기화 callback
→ BeanPostProcessor 후처리 및 proxy 생성 가능
→ 사용
→ ApplicationContext 종료 시 소멸 callback
```

초기화와 종료 작업은 `@PostConstruct`, `@PreDestroy` 또는 `@Bean(initMethod, destroyMethod)` 등으로 정의할 수 있다.

```java
@PostConstruct
void initialize() {
    client.connect();
}

@PreDestroy
void close() {
    client.close();
}
```

외부 연결처럼 실패하거나 오래 걸리는 작업을 초기화 단계에서 수행하면 애플리케이션 시작 자체가 실패하거나 느려질 수 있다는 점도 고려한다.

## 순환 참조

```text
OrderService → PaymentService
PaymentService → OrderService
```

생성자 주입에서 이런 구조는 두 객체 중 무엇을 먼저 만들지 결정할 수 없다. `@Lazy`로 억지로 풀기 전에 책임이 뒤섞였는지, 공통 로직을 별도 객체나 domain service로 분리해야 하는지 확인한다.

순환 참조는 단순 DI 설정 문제가 아니라 두 컴포넌트의 경계가 명확하지 않다는 신호인 경우가 많다.

## Spring AOP와 Proxy

AOP는 여러 기능에 반복되는 부가 로직을 핵심 로직과 분리하는 방식이다.

```text
핵심 로직
→ 주문 생성, 회원 수정, 결제 처리

부가 로직
→ transaction, logging, authorization, cache, retry
```

Spring AOP는 주로 대상 Bean을 감싼 proxy를 컨테이너에 등록한다.

```text
호출자
→ Proxy
→ transaction 시작
→ 실제 Service 메서드
→ commit 또는 rollback
```

interface가 있으면 JDK dynamic proxy를 사용할 수 있고, class 기반 proxy에는 CGLIB 방식이 사용된다. 구현 방식보다 중요한 점은 호출이 Spring이 만든 proxy를 지나야 advice가 실행된다는 것이다.

```java
public void outer() {
    inner(); // this.inner()와 같아서 proxy를 다시 거치지 않음
}

@Transactional
public void inner() { }
```

method를 별도 Bean으로 분리하거나 transaction 경계를 외부에서 호출되는 public method에 두어 해결한다. `@Transactional`, `@Async`, `@Cacheable`처럼 proxy에 의존하는 기능을 사용할 때 공통으로 확인해야 한다.

## 조건부 Bean 등록

Spring Boot 자동 설정은 다음 조건에 따라 Bean을 등록하거나 물러난다.

```text
classpath에 특정 class가 있는가?
사용자가 같은 종류의 Bean을 직접 등록했는가?
특정 property가 설정되었는가?
특정 profile이 활성화되었는가?
```

이 원리를 알면 starter를 추가했을 때 어떤 Bean이 자동 생성되는지, 직접 등록한 Bean 때문에 자동 설정이 제외됐는지 추적할 수 있다.

## 설명할 때 핵심 문장

```text
Spring Core의 핵심은 객체 생성과 의존관계 관리를 Spring Container가 담당하게 하는 것이다.
IoC는 객체 제어권이 개발자 코드에서 Spring으로 넘어간 것이고, DI는 필요한 의존 객체를 외부에서 주입받는 방식이다.
Bean은 Spring Container가 생성하고 관리하는 객체이며, 기본적으로 singleton으로 관리되기 때문에 상태를 함부로 가지면 안 된다.
```
