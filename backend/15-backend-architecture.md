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

## Layer 사이의 의존 방향

단순 Layered Architecture에서도 각 계층이 아무 방향으로 참조하면 책임 분리가 무너진다.

```text
Web → Application → Domain
Infrastructure → Application/Domain이 정의한 port
```

Controller는 HTTP DTO를 application command로 변환하고 use case를 호출한다. Application Service는 흐름과 transaction을 조율한다. Domain은 핵심 규칙을 실행한다. Infrastructure는 JPA, Redis, 외부 API 구현을 제공한다.

작은 CRUD에서는 Entity와 JPA model을 하나로 사용해도 현실적이다. 규칙이 복잡해져 persistence 요구사항이 domain model을 왜곡하기 시작하면 분리를 검토한다.

## Package by Layer와 Package by Feature

계층 중심:

```text
controller/
service/
repository/
dto/
```

기능 중심:

```text
member/
  controller/
  service/
  repository/
  domain/
order/
payment/
```

기능 중심 구조는 한 기능 변경에 관련된 파일을 가까이 두고 다른 기능의 내부 구현을 숨기기 쉽다. 프로젝트가 커질수록 기능별 최상위 package와 그 내부의 필요한 계층을 조합하는 방식이 관리하기 편하다.

## Application Service와 Domain Service

```text
Application Service
→ use case 순서 조율
→ repository와 외부 port 호출
→ transaction 경계

Domain Service
→ 특정 Entity 하나에 자연스럽게 속하지 않는 핵심 도메인 규칙
→ 가능하면 기술 의존성 없음
```

모든 로직을 `MemberService`, `OrderService`에 넣으면 Service가 거대해진다. 반대로 단순한 field 변경까지 무조건 Domain Service로 분리하면 모델이 잘게 찢어진다.

## Aggregate와 일관성 경계

Aggregate는 한 transaction에서 일관성을 지켜야 하는 객체 묶음이고 Aggregate Root가 외부 접근 지점이다.

```text
Order Aggregate
→ Order root
→ OrderLine children
```

외부 객체는 `OrderLine`을 직접 저장하거나 수정하기보다 `Order`의 method를 통해 변경한다. 다른 Aggregate는 객체 참조 대신 ID로 연결하면 한 Aggregate를 로딩할 때 거대한 객체 graph가 따라오는 것을 줄일 수 있다.

Aggregate를 너무 크게 잡으면 lock 범위와 transaction 비용이 커지고, 너무 작게 잡으면 지켜야 할 규칙이 여러 transaction에 흩어진다. 실제 비즈니스 불변식이 동시에 지켜져야 하는 범위를 기준으로 정한다.

## Domain Event

Domain Event는 도메인에서 이미 발생한 중요한 사실을 표현한다.

```text
OrderCompleted
PaymentApproved
MemberWithdrawn
```

event 이름은 명령이 아니라 과거형 사실로 표현하는 편이 명확하다. 같은 process 안의 event listener도 transaction 성공 전후 어느 시점에 실행되는지 확인해야 한다. 다른 시스템으로 전달한다면 Outbox와 consumer idempotency가 필요하다.

## Hexagonal Architecture

Hexagonal Architecture는 application core와 외부 세계를 port와 adapter로 연결한다.

```text
Inbound Adapter
→ REST Controller, message consumer, batch job

Inbound Port
→ application use case interface

Application / Domain
→ 핵심 규칙

Outbound Port
→ repository, payment client interface

Outbound Adapter
→ JPA repository 구현, HTTP client, Redis
```

Clean Architecture와 용어는 다르지만 핵심은 비슷하다. 비즈니스 규칙이 DB나 web framework를 직접 의존하지 않고 외부 기술이 안쪽에서 정의한 계약을 구현하게 한다.

## Modular Monolith

하나의 배포 단위를 유지하면서 내부를 독립적인 업무 module로 나누는 구조다.

```text
member module
order module
payment module
```

각 module은 공개 API만 노출하고 다른 module의 repository나 Entity를 직접 참조하지 않게 한다. microservice보다 배포와 transaction이 단순하면서도 경계를 연습할 수 있다.

module 사이 결합이 낮고 독립 배포 필요성이 실제로 생겼을 때 일부를 service로 분리하기가 쉬워진다.

## 구조 선택 기준

```text
단순 CRUD와 작은 팀
→ 기능 중심 package를 사용한 Layered Architecture

복잡한 상태 전이와 규칙
→ rich domain model, Aggregate, Domain Service 강화

외부 시스템과 저장 기술이 많음
→ port와 adapter로 경계 분리

업무 영역은 크지만 독립 배포 필요가 낮음
→ Modular Monolith 고려

팀과 배포가 실제로 독립적이고 확장 요구가 다름
→ Microservice 검토
```

Architecture는 directory 이름이 아니라 의존성 규칙이다. `domain` package를 만들었다고 DDD가 되는 것도 아니고 interface를 많이 만들었다고 Clean Architecture가 되는 것도 아니다.

## Overengineering 신호

```text
구현체가 하나뿐인데 모든 class에 의미 없는 interface가 있음
DTO 변환 계층이 너무 많아 한 field 추가에 많은 파일 수정
단순 CRUD가 여러 use case와 command 객체로 과도하게 분리
경계 규칙을 자동 test하지 않아 package만 복잡함
미래 가능성만으로 microservice를 먼저 분리
```

필요한 복잡성을 숨기지 말되 문제보다 구조가 더 복잡해지지 않도록 한다. 현재 변경 비용과 실패 위험을 줄이는 최소한의 구조에서 시작하고 실제 압력이 생길 때 확장한다.

## 설명할 때 핵심 문장

```text
아키텍처는 코드의 책임과 의존 방향을 정해 변경에 강한 구조를 만드는 것이다.
Layered Architecture는 Controller, Service, Repository로 책임을 나누는 가장 기본적인 백엔드 구조다.
DDD는 도메인 규칙을 중심으로 모델을 설계하는 접근이고, Clean Architecture는 비즈니스 규칙이 프레임워크와 DB에 강하게 묶이지 않게 하는 구조를 지향한다.
작은 프로젝트에서는 단순한 layered 구조로 시작하고, 복잡도가 커질수록 도메인 중심 설계를 강화하는 것이 현실적이다.
```
