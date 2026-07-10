# 10. JPA와 Hibernate

## JPA를 알아야 하는 이유

JPA는 Java 객체와 관계형 데이터베이스 테이블을 매핑하기 위한 표준 ORM 기술이다.

ORM은 Object Relational Mapping이다.

```text
Java Object
↔ RDB Table
```

JPA를 쓰면 SQL을 직접 작성하는 양을 줄이고, 객체 중심으로 도메인 모델을 다룰 수 있다.

하지만 JPA를 잘못 쓰면 N+1, 의도치 않은 update, 성능 문제, 트랜잭션 문제를 만들 수 있다.

## JPA와 Hibernate

JPA는 표준 인터페이스다.

Hibernate는 JPA 구현체다.

```text
JPA
→ 표준

Hibernate
→ 구현체
```

Spring Data JPA는 JPA를 더 편하게 쓰게 해주는 Spring 프로젝트다.

```text
Spring Data JPA
→ Repository 추상화 제공
→ 반복 CRUD 코드 감소
```

## Entity

Entity는 DB table과 매핑되는 객체다.

```java
@Entity
public class Member {
    @Id
    @GeneratedValue
    private Long id;

    private String email;
    private String nickname;
}
```

주의:

```text
Entity는 단순 DTO가 아니다.
도메인 상태와 규칙을 가질 수 있다.
```

## EntityManager

EntityManager는 JPA에서 entity를 저장, 조회, 수정, 삭제하는 핵심 객체다.

```text
persist
find
remove
flush
clear
```

Spring Data JPA를 쓰면 직접 EntityManager를 자주 다루지 않아도 되지만, 내부 동작을 이해해야 한다.

## 영속성 컨텍스트

영속성 컨텍스트는 Entity를 관리하는 1차 캐시 공간이다.

중요 기능:

```text
1차 캐시
동일성 보장
변경 감지
쓰기 지연
지연 로딩
```

같은 트랜잭션 안에서 같은 id를 조회하면 같은 객체를 반환할 수 있다.

```text
member1 == member2
```

## 변경 감지

JPA는 영속 상태의 Entity 변경을 감지해 update SQL을 만든다.

```java
Member member = memberRepository.findById(id).orElseThrow();
member.changeNickname("new");
```

명시적으로 save를 호출하지 않아도 트랜잭션 commit 시 update가 발생할 수 있다.

이것이 변경 감지다.

## Flush

Flush는 영속성 컨텍스트의 변경 내용을 DB에 반영하는 과정이다.

주의:

```text
flush는 commit이 아니다.
flush는 SQL을 DB에 보내는 것이고, transaction commit은 별도다.
```

## 지연 로딩

연관된 객체를 실제 사용할 때 조회하는 방식이다.

```java
@ManyToOne(fetch = FetchType.LAZY)
private Team team;
```

장점:

```text
불필요한 조회 감소
```

주의:

```text
트랜잭션 밖에서 접근하면 LazyInitializationException 가능
N+1 문제 가능
```

## N+1 문제

목록을 한 번 조회한 뒤 연관 데이터를 N번 추가 조회하는 문제다.

예:

```text
주문 목록 조회 1번
각 주문의 회원 조회 N번
```

해결:

```text
fetch join
EntityGraph
batch size
DTO projection
```

## Repository

Spring Data JPA Repository는 반복 CRUD 코드를 줄여준다.

```java
public interface MemberRepository extends JpaRepository<Member, Long> {
    Optional<Member> findByEmail(String email);
}
```

메서드 이름으로 query를 만들 수 있다.

복잡한 조회는 QueryDSL, JPQL, native query 등을 고려한다.

## 설명할 때 핵심 문장

```text
JPA는 Java 객체와 RDB 테이블을 매핑하는 ORM 표준이고, Hibernate는 대표적인 구현체다.
영속성 컨텍스트는 Entity를 관리하며 1차 캐시, 변경 감지, 쓰기 지연 같은 기능을 제공한다.
JPA는 편하지만 N+1, 지연 로딩, flush, transaction 경계를 이해하지 못하면 성능과 장애 문제가 생길 수 있다.
```
