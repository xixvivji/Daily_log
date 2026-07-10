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

## 설명할 때 핵심 문장

```text
Spring Boot는 Spring 애플리케이션을 빠르게 만들고 실행할 수 있도록 자동 설정, 내장 서버, starter 의존성, 외부 설정 관리를 제공한다.
Auto Configuration은 classpath와 설정을 기반으로 필요한 Bean을 자동 등록한다.
Profile과 application.yml을 사용하면 local, dev, prod 환경 설정을 분리할 수 있다.
Actuator는 health check와 metrics 같은 운영 기능을 제공한다.
```
