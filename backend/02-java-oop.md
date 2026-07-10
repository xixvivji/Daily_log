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

## 설명할 때 핵심 문장

```text
객체지향은 비즈니스 개념을 객체로 나누고 각 객체가 자기 책임을 가지도록 만드는 방식이다.
캡슐화는 객체 상태를 외부에서 마음대로 바꾸지 못하게 하고, 객체의 메서드를 통해 규칙 있게 변경하게 하는 것이다.
다형성과 추상화는 구현체 교체와 테스트를 쉽게 만들고, Spring DI와 직접 연결된다.
```
