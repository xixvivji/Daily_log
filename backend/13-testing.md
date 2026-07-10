# 13. 테스트

## 테스트가 필요한 이유

테스트는 코드가 의도대로 동작하는지 자동으로 확인하는 장치다.

백엔드에서 테스트가 중요한 이유:

```text
변경에 대한 안전망
버그 조기 발견
리팩토링 가능
비즈니스 규칙 문서화
배포 전 검증
```

테스트가 없으면 기능을 바꿀 때마다 사람이 모든 흐름을 수동 확인해야 한다.

## 테스트 종류

```text
Unit Test
Integration Test
Slice Test
End-to-End Test
```

Unit Test:

```text
작은 단위의 로직 검증
빠름
외부 의존성 최소화
```

Integration Test:

```text
Spring Context, DB, 외부 구성까지 포함해 검증
느리지만 실제 환경에 가까움
```

Slice Test:

```text
Controller, Repository 등 특정 계층만 잘라서 테스트
```

## JUnit

JUnit은 Java 테스트 프레임워크다.

```java
@Test
void changeNickname() {
    Member member = new Member("a@test.com", "old");

    member.changeNickname("new");

    assertThat(member.getNickname()).isEqualTo("new");
}
```

테스트 이름은 무엇을 검증하는지 드러나야 한다.

## Given When Then

테스트는 보통 세 단계로 읽기 좋게 만든다.

```text
given
→ 준비

when
→ 실행

then
→ 검증
```

예:

```java
// given
Member member = new Member("a@test.com", "old");

// when
member.changeNickname("new");

// then
assertThat(member.getNickname()).isEqualTo("new");
```

## Mockito

Mockito는 mock 객체를 만들어 의존성을 대체할 때 사용한다.

```java
when(memberRepository.findById(1L)).thenReturn(Optional.of(member));
```

주의:

```text
mock을 과하게 쓰면 구현 세부사항에 강하게 묶인 테스트가 된다.
비즈니스 규칙은 가능하면 순수 객체 테스트로 검증하는 것이 좋다.
```

## Spring Boot Test

`@SpringBootTest`는 Spring Context를 띄워 테스트한다.

장점:

```text
실제 Bean 설정 검증 가능
통합 흐름 검증 가능
```

단점:

```text
느림
테스트 범위가 커짐
실패 원인 파악이 어려울 수 있음
```

## WebMvcTest

Controller 계층 테스트에 사용한다.

```java
@WebMvcTest(MemberController.class)
```

검증:

```text
URL mapping
request validation
response status
response body
exception handler
```

## DataJpaTest

JPA repository 테스트에 사용한다.

```java
@DataJpaTest
```

검증:

```text
Entity mapping
Repository query
JPA 동작
```

## Testcontainers

실제 DB와 비슷한 환경을 Docker container로 띄워 테스트할 수 있다.

장점:

```text
H2와 실제 DB 차이 줄임
실제 MySQL/PostgreSQL 기반 테스트 가능
CI에서도 재현 가능
```

## 설명할 때 핵심 문장

```text
테스트는 변경에 대한 안전망이며, 비즈니스 규칙을 자동으로 검증하는 문서 역할도 한다.
Unit Test는 빠르게 작은 로직을 검증하고, Integration Test는 실제 Spring/DB 환경에 가까운 흐름을 검증한다.
테스트는 given-when-then 구조로 읽기 쉽게 작성하고, mock은 필요한 곳에만 사용해야 한다.
```
