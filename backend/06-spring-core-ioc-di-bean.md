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

## 설명할 때 핵심 문장

```text
Spring Core의 핵심은 객체 생성과 의존관계 관리를 Spring Container가 담당하게 하는 것이다.
IoC는 객체 제어권이 개발자 코드에서 Spring으로 넘어간 것이고, DI는 필요한 의존 객체를 외부에서 주입받는 방식이다.
Bean은 Spring Container가 생성하고 관리하는 객체이며, 기본적으로 singleton으로 관리되기 때문에 상태를 함부로 가지면 안 된다.
```
