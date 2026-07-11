# 01. Java Spring 백엔드 전체 그림

## 백엔드란 무엇인가?

백엔드는 사용자의 요청을 받아 비즈니스 로직을 처리하고, 데이터베이스나 외부 시스템과 통신한 뒤 응답을 돌려주는 서버 영역이다.

```text
Client
→ HTTP Request
→ Backend Server
→ Business Logic
→ Database / External API
→ HTTP Response
```

프론트엔드가 화면과 사용자 상호작용을 담당한다면, 백엔드는 데이터와 규칙을 책임진다.

예를 들어 회원가입 요청은 단순히 데이터를 저장하는 작업이 아니다.

```text
이메일 형식 검증
중복 이메일 확인
비밀번호 암호화
회원 엔티티 생성
DB 저장
가입 이벤트 발행
응답 반환
```

이 흐름을 안정적으로 처리하는 것이 백엔드의 역할이다.

## Java와 Spring을 쓰는 이유

Java는 안정적인 타입 시스템, 풍부한 생태계, JVM 기반 실행 환경을 가진 언어다.

Spring은 Java로 백엔드 애플리케이션을 만들 때 반복되는 문제를 해결해주는 프레임워크다.

Spring이 해결하는 대표 문제:

```text
객체 생성과 의존관계 관리
HTTP 요청 처리
트랜잭션 관리
DB 접근
인증/인가
검증
예외 처리
테스트
설정 관리
```

Spring을 쓰면 개발자는 인프라성 반복 코드보다 비즈니스 로직에 집중할 수 있다.

## Java Spring 백엔드 요청 흐름

Spring MVC 기준 요청 흐름은 보통 다음과 같다.

```text
Client
→ DispatcherServlet
→ HandlerMapping
→ Controller
→ Service
→ Repository
→ Database
```

각 계층의 역할:

```text
Controller
→ HTTP 요청과 응답을 담당

Service
→ 비즈니스 로직 담당

Repository
→ 데이터 접근 담당

Entity
→ DB 테이블과 매핑되고 영속성 컨텍스트가 관리하는 도메인 객체

DTO
→ API 경계에서 요청과 응답 데이터를 전달
```

## 한 요청이 처리되는 전체 과정

회원 조회 요청 `GET /api/members/1`을 예로 들면 다음 순서로 진행된다.

```text
1. 클라이언트가 HTTP 요청 전송
2. 웹 서버 또는 로드 밸런서가 애플리케이션으로 전달
3. Tomcat이 요청을 받을 thread 할당
4. Spring Security Filter가 인증과 인가 확인
5. DispatcherServlet이 요청을 받을 Controller 탐색
6. Controller가 path, query, body를 Java 값과 DTO로 변환
7. Service가 비즈니스 규칙과 트랜잭션 처리
8. Repository가 JPA를 통해 SQL 실행
9. DB 결과가 Entity로 변환
10. Entity를 응답 DTO로 변환
11. Jackson이 DTO를 JSON으로 직렬화
12. HTTP 상태 코드, header, body를 클라이언트에 반환
```

각 단계는 실패 지점도 다르다.

```text
인증 실패        → 401
권한 부족        → 403
요청 값 오류     → 400
리소스 없음      → 404
비즈니스 충돌    → 409
처리되지 않은 오류 → 500
```

## 애플리케이션을 구성하는 객체

```text
Controller
→ HTTP 형식과 애플리케이션 사이를 변환하는 adapter

Application Service
→ 하나의 use case를 조율하고 transaction 경계를 설정

Domain
→ 상태와 핵심 비즈니스 규칙을 표현

Repository
→ 저장소 접근을 추상화

Infrastructure
→ DB, Redis, Message Queue, 외부 API 같은 기술 구현
```

Controller가 Repository를 바로 호출할 수 없는 것은 아니지만, 비즈니스 규칙과 트랜잭션 경계가 Controller에 섞이기 쉽다. 일반적인 CRUD라도 Service를 두면 HTTP와 비즈니스 작업 단위를 분리할 수 있다.

## 빌드부터 실행까지

```text
Java source
→ Gradle 또는 Maven이 compile/test/package
→ 실행 가능한 jar 생성
→ JVM에서 java -jar로 실행
→ Spring ApplicationContext 생성
→ Bean 등록 및 의존관계 주입
→ 내장 Tomcat 시작
→ 요청 수신
```

Gradle과 Maven은 단순히 라이브러리를 내려받는 도구가 아니다. 소스 컴파일, 테스트, 패키징, 플러그인 실행과 의존성 버전 관리를 재현 가능한 절차로 만든다.

## 백엔드 품질을 판단하는 기준

```text
정확성      → 비즈니스 규칙과 데이터 정합성을 지키는가?
보안        → 인증, 인가, 입력 검증, 비밀 정보 보호가 되는가?
성능        → 필요한 처리량과 응답 시간을 만족하는가?
가용성      → 일부 장애가 전체 장애로 번지지 않는가?
관측 가능성 → 로그, metric, trace로 원인을 찾을 수 있는가?
변경 용이성 → 테스트와 책임 분리로 안전하게 수정할 수 있는가?
```

## 왜 계층을 나누는가?

계층을 나누는 이유는 책임을 분리하기 위해서다.

나쁜 구조:

```text
Controller에서 HTTP 처리, 검증, 비즈니스 로직, DB 접근을 모두 처리
```

문제:

```text
코드가 길어짐
테스트가 어려움
변경 영향 범위가 커짐
재사용이 어려움
비즈니스 규칙이 흩어짐
```

좋은 구조:

```text
Controller는 요청/응답
Service는 비즈니스 규칙
Repository는 DB 접근
```

이렇게 나누면 유지보수와 테스트가 쉬워진다.

## 백엔드에서 중요한 핵심 축

Java Spring 백엔드를 설명하려면 아래 축을 잡아야 한다.

```text
Java 언어
객체지향
JVM
Spring Core
Spring MVC
Spring Boot
Database
JPA
Transaction
Security
Test
Operation
Architecture
```

각 축은 따로 떨어져 있지 않다.

예:

```text
객체지향을 알아야 Service와 Domain을 설계할 수 있다.
JVM을 알아야 메모리와 성능 문제를 이해할 수 있다.
Spring Core를 알아야 Bean과 DI를 설명할 수 있다.
Transaction을 알아야 데이터 정합성을 지킬 수 있다.
Security를 알아야 인증/인가를 구현할 수 있다.
Test를 알아야 변경에 안전한 코드를 만들 수 있다.
```

## 설명할 때 핵심 문장

```text
백엔드는 요청을 받아 비즈니스 규칙을 실행하고 데이터를 안전하게 다룬 뒤 응답을 반환하는 서버 영역이다.
Java는 안정적인 서버 애플리케이션을 만들기 좋은 언어이고, Spring은 Java 백엔드에서 반복되는 객체 관리, 웹 요청 처리, 트랜잭션, 보안 같은 문제를 해결해주는 프레임워크다.
Spring 백엔드는 보통 Controller, Service, Repository로 책임을 나누고, 이 구조를 통해 유지보수와 테스트를 쉽게 만든다.
```
