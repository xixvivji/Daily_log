# 15. 백엔드 아키텍처: Layered, DDD, Clean Architecture

## 아키텍처가 필요한 이유

아키텍처는 코드를 어디에 둘지, 의존성을 어떻게 나눌지, 변경에 어떻게 대응할지를 정하는 구조다.

기능이 적을 때는 아무 구조로 작성해도 돌아간다.

하지만 서비스가 커지면 문제가 생긴다.

```text
Controller가 너무 커짐
Service가 모든 일을 함
비즈니스 규칙이 흩어짐
테스트가 어려움
DB 변경이 API까지 영향
외부 API 변경이 도메인 로직까지 영향
```

## Layered Architecture

가장 흔한 구조다.

```text
Controller
→ Service
→ Repository
→ Database
```

역할:

```text
Controller
→ HTTP 요청/응답

Service
→ 비즈니스 흐름

Repository
→ 데이터 접근

Domain / Entity
→ 핵심 데이터와 규칙
```

장점:

```text
이해하기 쉬움
Spring 예제와 잘 맞음
팀원이 익숙함
```

단점:

```text
Service가 커지기 쉬움
Domain이 빈약해지기 쉬움
DB 중심 설계로 흐르기 쉬움
```

## Domain

Domain은 해결하려는 비즈니스 영역이다.

예:

```text
회원
주문
결제
배송
쿠폰
정산
```

Domain 객체는 단순 데이터 보관함이 아니라 규칙을 가질 수 있다.

```java
public void cancel() {
    if (this.status == OrderStatus.DELIVERED) {
        throw new IllegalStateException("delivered order cannot be canceled");
    }
    this.status = OrderStatus.CANCELED;
}
```

## Anemic Domain Model

Anemic Domain Model은 도메인 객체에 데이터만 있고, 비즈니스 로직은 Service에 몰려 있는 구조다.

문제:

```text
Service가 너무 커짐
도메인 규칙이 흩어짐
객체가 자기 상태를 통제하지 못함
```

항상 나쁜 것은 아니지만, 복잡한 비즈니스에서는 도메인 객체가 자기 규칙을 갖는 편이 좋다.

## DDD 기초

DDD는 Domain Driven Design이다.

핵심은 도메인 모델을 중심으로 설계하는 것이다.

중요 개념:

```text
Entity
Value Object
Aggregate
Repository
Domain Service
Bounded Context
```

Entity:

```text
식별자를 가지고 생명주기가 있는 객체
```

Value Object:

```text
식별자보다 값 자체가 중요한 객체
불변으로 만드는 것이 좋음
```

Aggregate:

```text
일관성을 지켜야 하는 도메인 객체 묶음
```

## Clean Architecture 기초

Clean Architecture는 비즈니스 규칙이 프레임워크나 DB에 강하게 의존하지 않게 하는 구조를 지향한다.

핵심 방향:

```text
안쪽: Domain / UseCase
바깥쪽: Web / DB / 외부 API
```

의존성은 안쪽을 향한다.

```text
Controller → UseCase → Domain
Repository 구현체 → Domain이 정의한 interface
```

장점:

```text
테스트 쉬움
외부 기술 교체 쉬움
비즈니스 규칙 보호
```

단점:

```text
구조가 복잡해질 수 있음
작은 프로젝트에는 과할 수 있음
팀 합의가 필요함
```

## Package 구조

계층형:

```text
controller
service
repository
domain
dto
```

도메인 중심:

```text
member
order
payment
coupon
```

서비스가 커질수록 도메인 중심 패키지가 변경 범위를 파악하기 쉬울 수 있다.

## 설명할 때 핵심 문장

```text
아키텍처는 코드의 책임과 의존 방향을 정해 변경에 강한 구조를 만드는 것이다.
Layered Architecture는 Controller, Service, Repository로 책임을 나누는 가장 기본적인 백엔드 구조다.
DDD는 도메인 규칙을 중심으로 모델을 설계하는 접근이고, Clean Architecture는 비즈니스 규칙이 프레임워크와 DB에 강하게 묶이지 않게 하는 구조를 지향한다.
작은 프로젝트에서는 단순한 layered 구조로 시작하고, 복잡도가 커질수록 도메인 중심 설계를 강화하는 것이 현실적이다.
```
