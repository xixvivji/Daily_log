# 08. Spring Boot와 설정

## Spring Boot가 필요한 이유

Spring Framework만으로 애플리케이션을 만들면 설정할 것이 많다.

Spring Boot는 자주 쓰는 설정을 자동으로 구성해 빠르게 실행 가능한 애플리케이션을 만들게 해준다.

Spring Boot가 제공하는 것:

```text
Auto Configuration
Embedded Tomcat
Starter Dependency
Externalized Configuration
Actuator
Production-ready 설정
```

## @SpringBootApplication

Spring Boot 애플리케이션의 시작점이다.

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

내부적으로 주요 기능이 포함된다.

```text
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan
```

## Auto Configuration

Auto Configuration은 classpath와 설정 값을 보고 필요한 Bean을 자동 등록하는 기능이다.

예:

```text
spring-boot-starter-web
→ Spring MVC
→ Embedded Tomcat
→ Jackson
```

```text
spring-boot-starter-data-jpa
→ JPA
→ Hibernate
→ EntityManagerFactory
→ TransactionManager
```

개발자가 모든 Bean을 직접 등록하지 않아도 된다.

## Starter

Starter는 관련 의존성을 묶어둔 패키지다.

자주 쓰는 starter:

```text
spring-boot-starter-web
spring-boot-starter-validation
spring-boot-starter-data-jpa
spring-boot-starter-security
spring-boot-starter-test
spring-boot-starter-actuator
```

starter를 쓰면 버전 호환성을 Spring Boot가 관리해준다.

## Embedded Tomcat

Spring Boot는 내장 Tomcat을 포함할 수 있다.

그래서 별도 WAS에 war를 배포하지 않고 jar로 실행할 수 있다.

```bash
java -jar app.jar
```

흐름:

```text
Spring Boot app
→ embedded Tomcat
→ HTTP 요청 처리
```

## application.yml

Spring Boot 설정은 보통 `application.yml` 또는 `application.properties`에 둔다.

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/app
    username: app
    password: secret
```

환경별 설정:

```text
application-local.yml
application-dev.yml
application-prod.yml
```

실행 시 profile을 지정한다.

```bash
java -jar app.jar --spring.profiles.active=prod
```

## Profile

Profile은 환경별 Bean이나 설정을 분리하는 기능이다.

```java
@Profile("local")
@Bean
public TestPaymentClient testPaymentClient() {
    return new TestPaymentClient();
}
```

환경별로 DB, 외부 API, 로그 레벨 등이 달라질 수 있다.

```text
local
dev
stage
prod
```

## Configuration Properties

설정 값을 객체로 바인딩할 수 있다.

```java
@ConfigurationProperties(prefix = "payment")
public record PaymentProperties(
    String apiKey,
    String endpoint
) {
}
```

장점:

```text
설정 값을 타입으로 관리
관련 설정 묶기 쉬움
테스트 쉬움
```

## Actuator

Actuator는 운영에 필요한 endpoint를 제공한다.

대표 endpoint:

```text
/actuator/health
/actuator/metrics
/actuator/info
```

운영에서는 health check에 자주 사용한다.

```text
ALB Target Group health check
Kubernetes readinessProbe
```

주의:

```text
Actuator endpoint를 외부에 과하게 노출하면 보안 위험이 있다.
```

## 자동 설정이 결정되는 방식

자동 설정은 무조건 모든 Bean을 덮어쓰지 않는다. 다음과 같은 조건을 평가한다.

```text
classpath에 특정 class가 있는가?
특정 property가 설정되었는가?
사용자가 같은 종류의 Bean을 직접 등록했는가?
Servlet 애플리케이션인가 Reactive 애플리케이션인가?
```

조건을 만족하면 기본 Bean을 제공하고, 사용자가 명시적으로 등록하면 자동 설정이 물러나는 형태가 많다. 문제가 생기면 condition evaluation report와 debug log로 어떤 자동 설정이 적용되거나 제외됐는지 확인한다.

## 설정 우선순위와 외부화

같은 key가 여러 위치에 있으면 우선순위가 높은 설정이 적용된다. 세부 목록을 외우기보다 다음 방향을 이해한다.

```text
jar 내부 기본값
< profile별 설정
< 운영 환경의 환경 변수나 외부 설정 파일
< command line argument
```

```bash
export SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/app
java -jar app.jar --server.port=9090
```

실제 적용값을 확인할 때는 비밀번호나 token이 log에 출력되지 않게 주의한다.

## 비밀 정보 관리

DB 비밀번호, JWT key, 외부 API key를 Git에 commit하면 안 된다.

```text
local
→ Git에서 제외한 환경 변수 또는 개인 설정

AWS
→ Secrets Manager, Systems Manager Parameter Store

Kubernetes
→ Secret과 외부 secret 관리 도구
```

비밀 정보는 주입 경로뿐 아니라 log, Actuator endpoint, 예외 메시지, CI 출력에도 노출되지 않아야 한다. 유출 가능성이 있으면 Git에서 값을 지우는 데 그치지 않고 key를 폐기하고 재발급한다.

## 설정 값 검증

설정도 애플리케이션 입력값이므로 시작 시 검증하는 편이 좋다.

```java
@Validated
@ConfigurationProperties(prefix = "payment")
public record PaymentProperties(
    @NotBlank String apiKey,
    @NotNull URI endpoint,
    @NotNull Duration timeout
) { }
```

잘못된 운영 설정을 첫 요청 뒤 발견하는 것보다 애플리케이션 시작을 실패시키는 편이 원인을 찾기 쉽다.

## Liveness와 Readiness

```text
Liveness
→ process가 복구 불가능한 상태인지 판단
→ 실패가 지속되면 재시작 대상

Readiness
→ 현재 traffic을 받을 준비가 됐는지 판단
→ 실패하면 load balancer 대상에서 일시 제외
```

일시적인 DB 장애를 liveness 실패로 연결하면 모든 instance가 반복 재시작될 수 있다. 외부 의존성 상태는 보통 readiness와 분리해 설계한다.

## Graceful Shutdown

배포나 instance 종료 시 새 요청 수신을 중단하고 처리 중인 요청이 끝날 시간을 주는 것이 graceful shutdown이다.

```text
readiness 실패로 전환
→ load balancer가 새 요청 전송 중단
→ 진행 중 요청 완료 대기
→ application context 종료
→ connection과 thread pool 정리
```

종료 유예 시간은 load balancer 연결 해제 시간, 애플리케이션 종료 timeout, 컨테이너 종료 유예 시간을 함께 맞춘다.

## 의존성 버전 관리

Spring Boot dependency management는 검증된 라이브러리 버전 조합을 제공한다. 개별 라이브러리 버전을 임의로 덮어쓰면 호환성 문제가 생길 수 있다.

```text
버전 변경
→ release note와 migration guide 확인
→ compile/test
→ deprecated API 확인
→ staging 검증
→ metric과 error rate를 보며 배포
```

의존성은 기능뿐 아니라 보안 패치와 연결되므로 dependency report와 취약점 검사도 함께 관리한다.

## 설명할 때 핵심 문장

```text
Spring Boot는 Spring 애플리케이션을 빠르게 만들고 실행할 수 있도록 자동 설정, 내장 서버, starter 의존성, 외부 설정 관리를 제공한다.
Auto Configuration은 classpath와 설정을 기반으로 필요한 Bean을 자동 등록한다.
Profile과 application.yml을 사용하면 local, dev, prod 환경 설정을 분리할 수 있다.
Actuator는 health check와 metrics 같은 운영 기능을 제공한다.
```
