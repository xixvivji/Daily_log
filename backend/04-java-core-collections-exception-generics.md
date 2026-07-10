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

## 설명할 때 핵심 문장

```text
Collection은 여러 데이터를 목적에 맞게 다루기 위한 자료구조 API다.
List는 순서와 중복이 필요할 때, Set은 중복 제거가 필요할 때, Map은 key-value 조회가 필요할 때 사용한다.
Generic은 컴파일 시점 타입 안정성을 제공한다.
Exception은 실패 상황을 표현하고, Spring에서는 공통 예외 처리를 통해 HTTP error response로 변환할 수 있다.
```
