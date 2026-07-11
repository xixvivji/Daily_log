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

## Test Double 종류

```text
Dummy
→ 전달만 하고 실제로 사용하지 않는 객체

Stub
→ 정해진 응답을 반환

Fake
→ 단순하지만 실제로 동작하는 구현, in-memory repository 등

Mock
→ 호출 여부와 인자를 검증

Spy
→ 실제 객체 동작을 사용하면서 일부 호출을 관찰하거나 대체
```

모든 의존성을 mock으로 만들면 테스트가 구현 순서에 묶일 수 있다. 결과 상태를 검증할 수 있으면 상태 기반 검증을 우선하고, 외부 메시지 발행처럼 상호작용 자체가 계약일 때 호출을 검증한다.

## AssertJ로 의도를 드러내기

```java
assertThat(result.email()).isEqualTo("a@test.com");
assertThatThrownBy(() -> member.changeNickname(""))
    .isInstanceOf(IllegalArgumentException.class)
    .hasMessageContaining("nickname");
```

한 테스트에는 하나의 행동과 관련 결과를 검증한다. assertion 개수 자체보다 실패했을 때 어떤 규칙이 깨졌는지 바로 알 수 있는지가 중요하다.

## Service 단위 테스트

```java
@ExtendWith(MockitoExtension.class)
class MemberServiceTest {
    @Mock MemberRepository memberRepository;
    @InjectMocks MemberService memberService;

    @Test
    void duplicateEmailCannotBeRegistered() {
        when(memberRepository.existsByEmail("a@test.com")).thenReturn(true);

        assertThatThrownBy(() -> memberService.create(request()))
            .isInstanceOf(DuplicateEmailException.class);

        verify(memberRepository, never()).save(any());
    }
}
```

Service test는 비즈니스 분기와 협력 객체 호출을 빠르게 확인한다. JPA mapping이나 transaction rollback처럼 Spring이 제공하는 동작은 통합 테스트에서 별도로 검증한다.

## Controller Test

`@WebMvcTest`와 MockMvc로 HTTP 계약을 검증한다.

```java
mockMvc.perform(post("/api/members")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
            {"email":"invalid","password":""}
            """))
    .andExpect(status().isBadRequest())
    .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));
```

검증 대상은 URL, method, JSON 직렬화, validation, 상태 코드, 오류 형식이다. Service의 세부 비즈니스 규칙까지 Controller test에서 반복하지 않는다.

## Repository Test

Repository test에서는 실제 사용하는 DB와 가능한 한 같은 제품을 Testcontainers로 띄우는 것이 좋다.

```text
Entity column과 constraint
연관관계 mapping
JPQL 또는 QueryDSL 결과
정렬과 pagination
unique 위반
lock과 동시성
```

H2는 빠르지만 실제 MySQL/PostgreSQL과 SQL 문법, lock, timezone, transaction 동작이 다를 수 있다.

## 테스트 Transaction의 함정

`@Transactional` test는 종료 후 rollback되어 격리에 편리하지만, 테스트 method 전체에서 persistence context가 계속 열려 있다.

```text
production
→ transaction 종료 후 lazy relation 접근 시 실패 가능

transactional test
→ test 끝까지 context가 열려 있어 문제를 놓칠 수 있음
```

SQL 실행 여부를 확인하려면 `flush()`와 `clear()`를 명시적으로 호출할 수 있다. DB constraint 위반도 flush 또는 commit 시점까지 드러나지 않을 수 있다.

## Fixture와 Test Data Builder

여러 테스트가 긴 생성자를 반복하면 의미 없는 값 때문에 읽기 어려워진다.

```java
Member member = MemberFixture.activeMember()
    .email("a@test.com")
    .build();
```

fixture는 유효한 기본 객체를 제공하되, 테스트가 중요하게 보는 값은 테스트 본문에 드러나게 한다. 모든 테스트가 하나의 거대한 공용 fixture에 의존하면 모델 변경 시 불필요하게 많은 테스트가 깨질 수 있다.

## 외부 시스템 테스트

외부 API는 단위 테스트에서 fake나 mock server로 대체하고, provider와의 실제 계약은 별도 contract/integration test로 확인한다.

```text
정상 응답
4xx와 5xx
timeout
잘못된 JSON
재시도와 circuit breaker
중복 callback
```

테스트에서 실제 운영 외부 API를 호출하면 느리고 불안정하며 데이터 부수 효과가 생길 수 있다.

## 좋은 테스트 구성

```text
많은 빠른 domain/unit test
필요한 Spring slice test
핵심 흐름의 DB integration test
소수의 end-to-end test
```

coverage 숫자만 높이는 것이 목표는 아니다. 결제 금액 계산, 권한, 상태 전이, transaction, 동시성처럼 실패 비용이 큰 규칙에 더 강한 테스트를 둔다.

## 설명할 때 핵심 문장

```text
테스트는 변경에 대한 안전망이며, 비즈니스 규칙을 자동으로 검증하는 문서 역할도 한다.
Unit Test는 빠르게 작은 로직을 검증하고, Integration Test는 실제 Spring/DB 환경에 가까운 흐름을 검증한다.
테스트는 given-when-then 구조로 읽기 쉽게 작성하고, mock은 필요한 곳에만 사용해야 한다.
```
