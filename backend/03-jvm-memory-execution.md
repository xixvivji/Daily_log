# 03. JVM과 Java 실행 구조

## JVM을 알아야 하는 이유

Java 코드는 운영 서버에서 JVM 위에서 실행된다.

JVM을 모르면 아래 문제를 설명하기 어렵다.

```text
OutOfMemoryError
StackOverflowError
GC pause
메모리 누수
스레드 덤프
힙 덤프
애플리케이션이 느려지는 이유
```

백엔드 개발자는 JVM 내부를 모두 구현할 필요는 없지만, 실행 구조와 메모리 구조는 설명할 수 있어야 한다.

## Java 실행 흐름

Java 코드는 바로 기계어로 실행되지 않는다.

```text
.java
→ javac compile
→ .class bytecode
→ JVM
→ machine code
```

JVM 덕분에 Java는 운영체제에 독립적으로 실행될 수 있다.

```text
Write Once, Run Anywhere
```

같은 `.class` 파일을 JVM이 설치된 여러 환경에서 실행할 수 있다.

## JVM 구성

JVM은 크게 다음으로 볼 수 있다.

```text
Class Loader
Runtime Data Area
Execution Engine
Garbage Collector
```

Class Loader:

```text
class 파일을 JVM으로 로딩
```

Runtime Data Area:

```text
메서드 영역, 힙, 스택 등 실행 중 사용하는 메모리
```

Execution Engine:

```text
bytecode를 실행
```

Garbage Collector:

```text
더 이상 참조되지 않는 객체 메모리 정리
```

## Runtime Data Area

주요 메모리 영역:

```text
Method Area
Heap
Stack
PC Register
Native Method Stack
```

백엔드 개발자가 특히 자주 보는 것은 Heap과 Stack이다.

## Heap

Heap은 객체가 저장되는 영역이다.

```java
Member member = new Member();
```

`new Member()`로 만들어진 객체는 Heap에 저장된다.

Heap에 객체가 계속 쌓이고 GC로 정리되지 않으면 OutOfMemoryError가 발생할 수 있다.

원인 예:

```text
static collection에 객체를 계속 저장
cache eviction 없음
대용량 파일을 한 번에 메모리에 로드
무한히 쌓이는 이벤트 버퍼
```

## Stack

Stack은 메서드 호출 정보와 지역 변수가 저장되는 영역이다.

메서드가 호출될 때 stack frame이 생기고, 메서드가 끝나면 제거된다.

재귀 호출이 너무 깊으면 StackOverflowError가 발생할 수 있다.

```java
public void call() {
    call();
}
```

## Garbage Collection

GC는 더 이상 참조되지 않는 객체를 정리한다.

중요한 점:

```text
GC는 메모리 해제를 자동화하지만, 메모리 누수를 완전히 막아주지는 않는다.
```

객체가 계속 참조되고 있으면 GC 대상이 아니다.

예:

```java
static List<Object> store = new ArrayList<>();
```

여기에 계속 객체를 추가하면 참조가 살아 있으므로 GC가 치우지 못한다.

## GC Pause

GC가 동작하는 동안 애플리케이션 스레드가 잠깐 멈출 수 있다.

이를 Stop-The-World라고 한다.

운영에서 GC pause가 길면:

```text
응답 지연
timeout
일시적인 트래픽 처리량 감소
```

로 나타날 수 있다.

## JIT Compiler

JIT는 Just-In-Time Compiler다.

JVM은 자주 실행되는 bytecode를 기계어로 컴파일해서 성능을 높인다.

즉 Java는 단순 인터프리터 방식만 사용하는 것이 아니라, 실행 중 최적화도 한다.

## 설명할 때 핵심 문장

```text
Java 코드는 .class bytecode로 컴파일되고 JVM 위에서 실행된다.
JVM의 Heap에는 객체가 저장되고, Stack에는 메서드 호출 정보와 지역 변수가 저장된다.
GC는 참조되지 않는 객체를 정리하지만, 살아 있는 참조가 계속 남아 있으면 메모리 누수가 발생할 수 있다.
JVM을 이해하면 OutOfMemoryError, StackOverflowError, GC pause 같은 운영 문제를 설명할 수 있다.
```
