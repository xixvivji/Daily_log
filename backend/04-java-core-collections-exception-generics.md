# 04. Java Core: Collection, Generic, Exception

## 핵심 관점

Java 백엔드에서 Collection, Generic, Exception은 거의 모든 코드에 등장한다.

```text
List로 목록 응답
Map으로 key-value 처리
Set으로 중복 제거
Generic으로 타입 안정성 확보
Exception으로 실패 흐름 처리
```

이 개념들은 문법이 아니라 API 설계와 장애 처리 방식에 직접 연결된다.

## Collection

Collection은 여러 데이터를 다루기 위한 자료구조 API다.

대표 인터페이스:

```text
List
Set
Map
Queue
```

## List

List는 순서가 있고 중복을 허용한다.

```java
List<String> names = new ArrayList<>();
```

사용 예:

```text
회원 목록
게시글 목록
주문 상품 목록
```

대표 구현체:

```text
ArrayList
LinkedList
```

일반적으로 조회와 순회가 많으면 ArrayList를 자주 사용한다.

## Set

Set은 중복을 허용하지 않는다.

```java
Set<String> tags = new HashSet<>();
```

사용 예:

```text
중복 없는 태그
권한 목록
이미 처리한 id 집합
```

대표 구현체:

```text
HashSet
LinkedHashSet
TreeSet
```

## Map

Map은 key-value 구조다.

```java
Map<String, Integer> scores = new HashMap<>();
```

사용 예:

```text
사용자 id별 데이터
설정 값
캐시
그룹핑 결과
```

주의:

```text
HashMap은 thread-safe하지 않다.
동시성 환경에서는 ConcurrentHashMap 등을 고려해야 한다.
```

## Generic

Generic은 타입을 파라미터처럼 다루는 기능이다.

```java
List<String> names = new ArrayList<>();
```

Generic이 없으면 Object를 꺼내서 형변환해야 한다.

```java
Object value = list.get(0);
String name = (String) value;
```

Generic을 쓰면 컴파일 시점에 타입을 확인할 수 있다.

장점:

```text
타입 안정성
불필요한 형변환 감소
컴파일 시점 오류 발견
```

## Collection 선택과 시간 복잡도

자료구조는 이름보다 주요 연산을 기준으로 선택한다.

```text
ArrayList
→ index 조회 O(1), 끝 추가 평균 O(1), 중간 삽입·삭제 O(n)

HashSet / HashMap
→ 평균 조회·추가 O(1), 올바른 equals/hashCode 필요

TreeSet / TreeMap
→ 정렬 상태 유지, 주요 연산 O(log n)

ArrayDeque
→ queue와 stack 용도로 양쪽 삽입·삭제가 효율적
```

`LinkedList`는 중간 노드를 이미 알고 있을 때 삽입·삭제가 빠르지만, 특정 위치를 찾는 데 O(n)이 필요하고 메모리 지역성이 좋지 않아 일반적인 목록에서는 `ArrayList`가 더 자주 사용된다.

컬렉션을 외부에 그대로 반환하면 호출자가 내부 상태를 변경할 수 있다. 읽기 전용 view가 필요하면 `List.copyOf()` 등을 고려한다.

## Generic 제약과 Wildcard

Generic은 상속 관계에서 불공변이다.

```text
Integer는 Number의 하위 타입
하지만 List<Integer>는 List<Number>의 하위 타입이 아님
```

범위를 열어줄 때 wildcard를 사용한다.

```java
double sum(List<? extends Number> numbers) { ... }
void addDefaults(List<? super Integer> target) { ... }
```

기억법은 PECS다.

```text
Producer Extends
→ 값을 읽어오는 생산자에는 ? extends T

Consumer Super
→ 값을 넣는 소비자에는 ? super T
```

Java Generic은 주로 type erasure로 구현된다. 실행 시점에는 많은 generic 타입 정보가 지워지므로 `new T()`나 `List<String>.class` 같은 표현을 직접 사용할 수 없다.

## Lambda와 함수형 인터페이스

함수형 인터페이스는 추상 메서드가 하나인 인터페이스다.

```text
Predicate<T>  → T를 받아 boolean 반환
Function<T,R> → T를 받아 R 반환
Consumer<T>   → T를 받고 반환 없음
Supplier<T>   → 인자 없이 T 반환
```

```java
Predicate<Member> active = member -> member.isActive();
```

Lambda는 동작을 값처럼 전달할 수 있게 하지만, 긴 비즈니스 로직을 lambda 안에 숨기면 읽기 어려워진다.

## Stream API

Stream은 collection 데이터를 선언적인 pipeline으로 처리한다.

```java
List<String> emails = members.stream()
    .filter(Member::isActive)
    .map(Member::getEmail)
    .toList();
```

```text
source
→ intermediate operation(filter, map, sorted)
→ terminal operation(toList, count, reduce)
```

Stream은 원본 collection을 저장하는 자료구조가 아니고 일회성 처리 흐름이다. 부작용이 있는 `map()`이나 DB 호출을 수행하는 pipeline은 예측하기 어렵고 N+1을 만들 수 있다. 데이터가 적다고 무조건 `parallelStream()`을 사용하면 common pool 경쟁과 순서·동시성 문제가 생길 수 있다.

## Optional

Optional은 값이 없을 수 있음을 표현하는 타입이다.

```java
Optional<Member> findById(Long id);
```

주의:

```text
필드에 Optional을 쓰는 것은 보통 권장하지 않는다.
메서드 반환 타입에서 값이 없을 수 있음을 표현할 때 주로 사용한다.
```

## Exception

Exception은 정상 흐름이 아닌 실패 상황을 표현한다.

Java 예외는 크게 checked exception과 unchecked exception으로 나뉜다.

Checked Exception:

```text
컴파일러가 처리 강제
Exception 상속
RuntimeException 제외
```

Unchecked Exception:

```text
컴파일러가 처리 강제하지 않음
RuntimeException 상속
```

Spring 백엔드에서는 비즈니스 예외를 RuntimeException으로 정의하는 경우가 많다.

```java
public class MemberNotFoundException extends RuntimeException {
    public MemberNotFoundException(Long id) {
        super("member not found: " + id);
    }
}
```

## 예외를 쓰는 이유

예외를 쓰는 이유:

```text
실패 상황을 명확히 표현
정상 흐름과 실패 흐름 분리
공통 예외 처리 가능
HTTP error response로 변환 가능
```

Spring에서는 `@ControllerAdvice`로 예외를 공통 처리할 수 있다.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(MemberNotFoundException.class)
    public ResponseEntity<ErrorResponse> handle(MemberNotFoundException e) {
        return ResponseEntity.status(404).body(new ErrorResponse(e.getMessage()));
    }
}
```

## 예외 처리 원칙

```text
복구할 수 있는 계층에서 처리
처리할 수 없으면 의미 있는 예외로 변환해 전파
원래 원인을 cause로 보존
같은 예외를 여러 계층에서 반복 logging하지 않음
민감 정보와 내부 stack trace를 API 응답에 노출하지 않음
```

```java
throw new PaymentUnavailableException("payment provider failed", cause);
```

`catch (Exception e)`로 잡고 아무 처리도 하지 않으면 장애가 정상 성공처럼 보일 수 있다. 반대로 모든 예외를 무조건 RuntimeException 하나로 바꾸면 실패 의미를 구분하기 어렵다.

`try-with-resources`를 사용하면 `AutoCloseable` 자원을 예외 발생 여부와 관계없이 정리할 수 있다.

```java
try (InputStream input = file.getInputStream()) {
    return input.readAllBytes();
}
```

## String과 Wrapper Type

`String`은 불변 객체다. 문자열을 변경하는 것처럼 보여도 기존 객체가 바뀌는 것이 아니라 새 문자열이 만들어진다.

```java
String value = "member";
value = value + "-active";
```

문자열 literal은 String Pool에서 재사용될 수 있지만, 문자열 값 비교는 pool 동작에 기대지 말고 `equals()`를 사용한다.

반복문에서 문자열을 계속 `+`로 이어 붙이면 중간 객체가 많이 생길 수 있다. 많은 문자열을 동적으로 조합할 때는 `StringBuilder`를 사용한다.

```java
StringBuilder builder = new StringBuilder();
for (String tag : tags) {
    builder.append(tag).append(',');
}
```

Wrapper type은 원시 타입을 객체로 다룬다.

```text
int     ↔ Integer
long    ↔ Long
boolean ↔ Boolean
```

Auto boxing/unboxing이 자동 변환을 제공하지만 `Integer`가 `null`인 상태에서 `int`로 unboxing하면 `NullPointerException`이 발생한다. Wrapper 객체 비교에도 `==` 대신 `equals()`를 사용한다.

## Annotation과 Reflection

Annotation은 class, method, field 등에 metadata를 붙인다.

```java
@Transactional
public void createOrder() { }
```

Annotation 자체가 transaction을 시작하는 것은 아니다. Spring이 시작 시점이나 실행 시점에 annotation metadata를 읽고 proxy와 interceptor를 구성해 동작을 추가한다.

Reflection은 실행 중 class의 type, constructor, method, field, annotation 정보를 조사하고 호출할 수 있는 기능이다. Spring의 component scan, dependency injection, Jackson의 객체 변환, JPA mapping 등에서 사용된다.

Reflection은 framework에는 강력하지만 일반 비즈니스 코드에서 과도하게 사용하면 compile-time 타입 검사가 약해지고 실행 시점 오류와 성능 비용이 생길 수 있다.

## 날짜와 시간

Java에서는 `java.time` API를 사용한다.

```text
Instant
→ UTC 기준의 한 시점

LocalDate
→ 시간대 없는 날짜

LocalDateTime
→ 시간대 없는 날짜와 시간

ZonedDateTime
→ timezone 규칙을 포함한 날짜와 시간

Duration
→ 시간 기반 간격
```

```java
Instant now = Instant.now();
ZonedDateTime seoul = now.atZone(ZoneId.of("Asia/Seoul"));
```

운영 데이터는 UTC 기준으로 저장하고 API 경계나 화면에서 사용자 timezone으로 변환하는 방식을 많이 사용한다. `LocalDateTime`만 저장하면 어느 timezone의 시각인지 정보가 없으므로 팀의 저장 규칙을 명확히 해야 한다.

테스트 가능한 시간 로직은 `Instant.now()`를 곳곳에서 직접 호출하지 않고 `Clock`을 주입할 수 있다.

```java
public CouponService(Clock clock) {
    this.clock = clock;
}
```

## I/O와 Resource 관리

```text
InputStream / OutputStream
→ byte 단위 I/O

Reader / Writer
→ 문자 단위 I/O와 charset 처리

Path / Files
→ 파일 경로와 파일 작업
```

문자를 byte로 변환할 때 charset을 명시한다.

```java
byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
```

파일이나 network stream은 사용 후 닫아야 하므로 `try-with-resources`를 사용한다. 대용량 파일을 `readAllBytes()`로 한꺼번에 heap에 올리면 OOM이 발생할 수 있어 stream으로 일정 크기씩 처리한다.

I/O API가 blocking인지 확인해야 한다. 외부 응답을 기다리는 동안 요청 thread를 점유하면 thread pool 고갈로 이어질 수 있다.

## 설명할 때 핵심 문장

```text
Collection은 여러 데이터를 목적에 맞게 다루기 위한 자료구조 API다.
List는 순서와 중복이 필요할 때, Set은 중복 제거가 필요할 때, Map은 key-value 조회가 필요할 때 사용한다.
Generic은 컴파일 시점 타입 안정성을 제공한다.
Exception은 실패 상황을 표현하고, Spring에서는 공통 예외 처리를 통해 HTTP error response로 변환할 수 있다.
```
