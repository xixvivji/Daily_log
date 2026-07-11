# 02. Java와 객체지향

## 객체지향이 필요한 이유

객체지향은 현실의 개념이나 비즈니스 개념을 객체로 나누고, 각 객체가 자기 책임을 가지도록 설계하는 방식이다.

백엔드에서 객체지향이 중요한 이유는 비즈니스 규칙을 코드로 표현해야 하기 때문이다.

예:

```text
회원은 닉네임을 변경할 수 있다.
주문은 결제 완료 후 취소할 수 있다.
쿠폰은 만료일이 지나면 사용할 수 없다.
```

이런 규칙을 단순히 절차적으로 흩뿌리면 유지보수가 어려워진다.

객체지향은 데이터와 행동을 함께 묶어 규칙을 표현할 수 있게 한다.

## 클래스와 객체

클래스는 객체를 만들기 위한 설계도다.

객체는 클래스를 기반으로 실제 생성된 인스턴스다.

```java
public class Member {
    private String email;
    private String nickname;

    public void changeNickname(String nickname) {
        this.nickname = nickname;
    }
}
```

```text
Member class
→ 회원이라는 개념의 설계도

new Member()
→ 실제 회원 객체
```

## 캡슐화

캡슐화는 객체의 내부 상태를 외부에서 마음대로 바꾸지 못하게 하고, 정해진 메서드를 통해서만 변경하게 하는 것이다.

나쁜 예:

```java
member.nickname = "";
```

좋은 예:

```java
member.changeNickname("jiwon");
```

메서드 안에서 규칙을 강제할 수 있다.

```java
public void changeNickname(String nickname) {
    if (nickname == null || nickname.isBlank()) {
        throw new IllegalArgumentException("nickname is required");
    }
    this.nickname = nickname;
}
```

캡슐화의 목적은 단순히 `private`을 붙이는 것이 아니라, 객체의 상태 변경을 객체 스스로 통제하게 하는 것이다.

## 상속

상속은 부모 클래스의 필드와 메서드를 자식 클래스가 물려받는 기능이다.

하지만 실무에서는 무분별한 상속보다 조합을 선호하는 경우가 많다.

상속이 위험한 이유:

```text
부모 변경이 자식에게 영향을 줌
계층이 깊어지면 이해가 어려움
is-a 관계가 아닌데 상속을 쓰기 쉬움
```

상속은 진짜 `is-a` 관계일 때 조심해서 사용한다.

## 다형성

다형성은 같은 인터페이스를 통해 서로 다른 구현체를 사용할 수 있는 성질이다.

```java
public interface DiscountPolicy {
    int discount(int price);
}
```

```java
public class FixedDiscountPolicy implements DiscountPolicy {
    public int discount(int price) {
        return 1000;
    }
}
```

```java
public class RateDiscountPolicy implements DiscountPolicy {
    public int discount(int price) {
        return price / 10;
    }
}
```

서비스는 구현체가 아니라 인터페이스에 의존한다.

```java
public class OrderService {
    private final DiscountPolicy discountPolicy;

    public OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = discountPolicy;
    }
}
```

이 구조는 Spring DI와도 바로 연결된다.

## 추상화

추상화는 복잡한 구현 세부사항을 숨기고 중요한 역할만 드러내는 것이다.

예:

```java
public interface PaymentClient {
    PaymentResult pay(PaymentRequest request);
}
```

서비스는 결제사가 Toss인지 KakaoPay인지 몰라도 된다.

```text
PaymentClient라는 역할에만 의존
구현체는 설정으로 교체 가능
```

## SOLID 간단 정리

SOLID는 객체지향 설계 원칙이다.

```text
SRP
→ 하나의 클래스는 하나의 책임을 가진다.

OCP
→ 확장에는 열려 있고 변경에는 닫혀 있어야 한다.

LSP
→ 자식 타입은 부모 타입을 대체할 수 있어야 한다.

ISP
→ 클라이언트가 사용하지 않는 인터페이스에 의존하지 않게 한다.

DIP
→ 구체 클래스보다 추상화에 의존한다.
```

Spring에서 가장 자주 체감하는 것은 DIP다.

```text
Service가 구현체가 아니라 interface에 의존
구현체 주입은 Spring Container가 담당
```

## 원시 타입과 참조 타입

Java 값은 크게 원시 타입과 참조 타입으로 구분한다.

```text
원시 타입
→ byte, short, int, long, float, double, char, boolean
→ 값 자체를 변수에 저장

참조 타입
→ class, interface, array, enum, record
→ 객체를 가리키는 참조를 변수에 저장
```

메서드에 객체를 전달하면 객체 자체가 복사되는 것이 아니라 참조 값이 복사된다. 따라서 전달받은 객체의 내부 상태를 바꾸면 호출자도 변경된 객체를 보게 된다.

## ==와 equals

참조 타입에서 `==`는 두 변수가 같은 객체를 가리키는지 비교한다. `equals()`는 객체가 논리적으로 같은 값인지 비교하도록 정의할 수 있다.

```java
String a = new String("member");
String b = new String("member");

a == b;       // false: 서로 다른 객체
a.equals(b);  // true: 문자열 값은 같음
```

값 객체는 논리적 동등성을 제대로 표현하도록 `equals()`와 `hashCode()`를 함께 구현해야 한다. 두 객체가 `equals()`로 같다면 같은 `hashCode()`를 반환해야 `HashSet`, `HashMap`이 올바르게 동작한다.

JPA Entity의 동등성은 더 조심해야 한다. DB 생성 식별자는 저장 전에는 `null`이고 저장 후에 생기므로, 무조건 모든 필드나 생성 ID만으로 자동 구현하면 영속화 전후 동작이 달라질 수 있다.

## 불변 객체

불변 객체는 생성 후 내부 상태가 바뀌지 않는 객체다.

```java
public record Money(long amount, String currency) {
    public Money {
        if (amount < 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
    }
}
```

장점:

```text
상태 변화를 추적하기 쉬움
여러 thread에서 공유하기 상대적으로 안전함
Map key나 cache 값으로 쓰기 좋음
생성 시점에 유효성을 보장할 수 있음
```

`final`은 변수에 다른 값을 다시 대입하지 못하게 할 뿐, 참조 대상 객체의 내부까지 자동으로 불변으로 만들지는 않는다.

## enum과 record

`enum`은 제한된 값 집합과 그 값에 관련된 행위를 표현한다.

```java
public enum OrderStatus {
    CREATED, PAID, CANCELED
}
```

문자열로 상태를 관리하면 오타와 허용되지 않은 값이 들어갈 수 있다. `enum`을 사용하면 컴파일 시점 타입 검사를 받을 수 있다.

`record`는 주로 불변 데이터 묶음을 간결하게 표현한다. 생성자, 접근자, `equals()`, `hashCode()`, `toString()`이 자동 생성되므로 요청·응답 DTO와 값 객체에 유용하다. JPA Entity는 프록시와 기본 생성자, 변경 감지 요구사항 때문에 일반적으로 record로 만들지 않는다.

## 객체지향 설계에서 자주 하는 실수

```text
모든 Service마다 의미 없는 interface 생성
getter와 setter만 있는 Entity 작성
한 메서드가 검증, 저장, 외부 호출을 모두 처리
상속을 코드 재사용 수단으로만 사용
DTO와 Entity를 같은 객체로 사용
기술 이름을 도메인 모델에 직접 노출
```

추상화는 구현체가 실제로 교체되거나, 외부 시스템과의 경계를 격리하거나, 테스트 대역이 필요한 지점에서 의미가 있다. 단순히 클래스마다 인터페이스를 만드는 것은 구조만 늘릴 수 있다.

## 설명할 때 핵심 문장

```text
객체지향은 비즈니스 개념을 객체로 나누고 각 객체가 자기 책임을 가지도록 만드는 방식이다.
캡슐화는 객체 상태를 외부에서 마음대로 바꾸지 못하게 하고, 객체의 메서드를 통해 규칙 있게 변경하게 하는 것이다.
다형성과 추상화는 구현체 교체와 테스트를 쉽게 만들고, Spring DI와 직접 연결된다.
```
