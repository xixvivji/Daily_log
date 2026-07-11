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

## Entity 생명주기

```text
비영속(transient)
→ Java 객체지만 persistence context가 관리하지 않음

영속(managed)
→ persistence context가 관리하고 변경 감지 대상

준영속(detached)
→ 한때 관리됐지만 context에서 분리됨

삭제(removed)
→ 삭제 예약 상태
```

Repository에서 조회한 Entity라도 transaction이 끝나면 보통 준영속 상태가 된다. 변경 감지는 영속 상태와 transaction 안에서 이루어져야 한다.

## 식별자 생성 전략

```text
IDENTITY
→ DB auto increment 사용

SEQUENCE
→ DB sequence 사용

TABLE
→ 별도 table로 sequence 흉내

UUID
→ 애플리케이션 또는 DB에서 UUID 생성
```

전략은 insert 시점, batch insert 가능 여부, index 크기와 분산 환경에 영향을 준다. 식별자는 단순 타입 선택이 아니라 DB와 쓰기 패턴을 함께 보고 결정한다.

## 연관관계 Mapping

```java
@Entity
public class Order {
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "member_id", nullable = false)
    private Member member;
}
```

DB에서는 외래 키가 있는 `orders.member_id`가 관계를 결정한다. 객체에서는 `Order.member` 참조로 탐색한다.

```text
@ManyToOne  → 여러 Order가 한 Member를 참조
@OneToMany  → 한 Member가 여러 Order collection을 가짐
@OneToOne   → 한 객체와 하나의 객체 관계
@ManyToMany → 중간 table을 자동 사용하지만 관계 속성을 담기 어려워 실무에서는 연결 Entity를 주로 사용
```

## 연관관계 주인과 mappedBy

양방향 관계에서는 외래 키 값을 실제로 변경할 한쪽을 연관관계 주인으로 정한다.

```java
@OneToMany(mappedBy = "member")
private List<Order> orders = new ArrayList<>();
```

`mappedBy`가 있는 쪽은 관계를 읽는 inverse side이고, `@JoinColumn`을 가진 `Order.member`가 외래 키를 관리한다. 객체 상태도 양쪽을 일관되게 유지하려면 연관관계 편의 method를 사용할 수 있다.

```java
public void changeMember(Member member) {
    this.member = member;
    member.getOrders().add(this);
}
```

모든 관계를 양방향으로 만들 필요는 없다. 필요한 탐색 방향만 두는 단방향 관계가 단순하다.

## Cascade와 orphanRemoval

```text
cascade
→ 부모의 persist/remove 같은 EntityManager 동작을 자식에 전파

orphanRemoval
→ 부모 collection에서 제거되어 관계가 끊긴 자식을 삭제
```

두 옵션은 비슷해 보이지만 목적이 다르다. 자식의 생명주기를 부모가 완전히 소유할 때만 사용한다. 다른 aggregate가 함께 참조하는 Entity에 `CascadeType.REMOVE`를 적용하면 의도하지 않은 데이터가 삭제될 수 있다.

## Fetch 전략과 OSIV

ToOne 관계도 명시적으로 `LAZY`를 선택하고 필요한 query에서 fetch join이나 projection으로 로딩 범위를 결정하는 편이 예측하기 쉽다.

OSIV(Open Session In View)가 켜져 있으면 web 요청이 끝날 때까지 persistence context가 열려 Controller에서도 lazy loading이 가능할 수 있다. 편리하지만 Controller에서 추가 SQL이 발생하고 DB connection 반환 시점을 예측하기 어려워질 수 있다.

OSIV를 끄면 Service transaction 안에서 필요한 데이터를 모두 조회해 DTO로 변환해야 한다. 어느 설정이든 query가 발생하는 위치를 명확히 통제해야 한다.

## JPQL, QueryDSL, Projection

```text
Derived Query Method
→ 간단한 조건 조회

JPQL
→ Entity와 field를 기준으로 query 작성

QueryDSL
→ type-safe하게 동적 query 조립

Native Query
→ DB 고유 기능이나 복잡한 SQL이 꼭 필요할 때

DTO Projection
→ 화면에 필요한 column만 직접 조회
```

Repository method 이름이 지나치게 길거나 조건 조합이 많아지면 QueryDSL 같은 동적 query 도구를 검토한다. 모든 조회를 Entity로 가져오면 불필요한 column과 연관 로딩 비용이 커질 수 있다.

## Bulk 연산 주의점

JPQL bulk update/delete는 persistence context를 거치지 않고 DB에 직접 반영된다.

```java
@Modifying(clearAutomatically = true, flushAutomatically = true)
@Query("update Member m set m.status = :status where m.lastLoginAt < :before")
int updateStatus(Status status, LocalDateTime before);
```

이미 관리 중인 Entity에는 이전 값이 남을 수 있으므로 bulk 연산 전 flush하고 이후 context를 clear하거나 transaction을 분리한다.

## 낙관적 락과 비관적 락

```java
@Version
private Long version;
```

낙관적 락은 조회 시점 version과 수정 시점 version이 다르면 충돌을 감지한다. 충돌이 드물고 재시도할 수 있을 때 유리하다.

비관적 락은 DB row lock을 먼저 획득한다. 충돌이 잦은 짧은 작업에는 유용하지만 대기, deadlock, transaction 장기화 위험이 있다. 어떤 락을 쓰더라도 transaction 범위를 짧게 유지한다.

## Auditing과 시간

```text
createdAt
updatedAt
createdBy
updatedBy
```

Spring Data JPA Auditing으로 공통 필드를 자동 기록할 수 있다. 서버와 DB의 timezone을 명확히 하고 저장 시각과 사용자에게 보여줄 지역 시각을 구분한다.

## Entity 설계 주의점

```text
API 요청 body로 Entity를 직접 받지 않음
응답으로 Entity를 직접 반환하지 않음
기본 생성자는 JPA용으로 protected 사용 가능
setter 전체 공개 대신 의미 있는 변경 method 제공
collection은 null 대신 빈 collection으로 초기화
toString, equals, hashCode에 lazy relation을 무심코 포함하지 않음
```

## 설명할 때 핵심 문장

```text
JPA는 Java 객체와 RDB 테이블을 매핑하는 ORM 표준이고, Hibernate는 대표적인 구현체다.
영속성 컨텍스트는 Entity를 관리하며 1차 캐시, 변경 감지, 쓰기 지연 같은 기능을 제공한다.
JPA는 편하지만 N+1, 지연 로딩, flush, transaction 경계를 이해하지 못하면 성능과 장애 문제가 생길 수 있다.
```
