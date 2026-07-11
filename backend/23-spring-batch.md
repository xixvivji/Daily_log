# 23. Spring Batch 실전

## Batch와 Scheduler 차이

```text
Batch
→ 많은 데이터를 정해진 절차로 안정적으로 처리

Scheduler
→ 작업을 언제 시작할지 결정
```

`@Scheduled`는 실행 시각을 제공하지만 대량 처리의 restart, chunk transaction, 실행 이력까지 자동 제공하지 않는다.

## Spring Batch Domain

```text
Job
→ 전체 batch 작업 정의

JobInstance
→ Job 이름과 식별 parameter로 구분되는 논리적 실행

JobExecution
→ 실제 실행 시도 한 번

Step
→ Job을 구성하는 처리 단계

StepExecution
→ Step 실행 상태와 통계

JobRepository
→ 실행 metadata 저장
```

같은 JobParameter로 완료된 JobInstance를 다시 실행할 수 있는지 정책을 이해해야 한다.

## Chunk Processing

```text
ItemReader
→ item 읽기

ItemProcessor
→ 변환과 validation

ItemWriter
→ 묶어서 저장
```

```text
10개 읽기·처리
→ 10개 write
→ transaction commit
→ 다음 chunk
```

Chunk가 크면 처리량은 좋아질 수 있지만 rollback 범위, memory, lock 시간이 커진다. 작으면 commit 비용이 증가한다.

## Step 설정 예시

```java
@Bean
Step memberStatusStep(
    JobRepository jobRepository,
    PlatformTransactionManager transactionManager
) {
    return new StepBuilder("memberStatusStep", jobRepository)
        .<Member, MemberUpdate>chunk(100, transactionManager)
        .reader(memberReader())
        .processor(memberProcessor())
        .writer(memberWriter())
        .faultTolerant()
        .retry(DeadlockLoserDataAccessException.class)
        .retryLimit(3)
        .skip(InvalidMemberException.class)
        .skipLimit(100)
        .build();
}
```

Version에 따라 builder API가 달라질 수 있으므로 사용하는 Spring Batch reference를 확인한다.

## Reader 선택

```text
Cursor Reader
→ DB cursor를 열고 순차 읽기
→ 긴 connection과 transaction 주의

Paging Reader
→ page 단위 query
→ 안정적인 정렬 key 필요

Flat File Reader
→ CSV 등 파일 item 읽기

Custom Reader
→ 외부 API나 object storage
→ checkpoint와 retry 직접 고려
```

Paging 중 데이터가 변경되면 offset 방식은 누락·중복이 생길 수 있다. 불변 조건, snapshot, keyset 방식이나 처리 상태 column을 고려한다.

## Restartability

Spring Batch는 ExecutionContext와 metadata를 이용해 실패 지점부터 재시작할 수 있다.

재시작 가능하려면:

```text
Reader 상태 저장
Writer가 중복 item을 견딤
JobParameter가 실행 대상을 식별
외부 부수 효과가 idempotent
임시 파일과 중간 상태 규칙 명확화
```

DB commit 후 checkpoint 저장 전에 process가 죽는 경계 등에서는 중복 가능성을 고려한다.

## Skip과 Retry

```text
Retry
→ 다시 하면 성공할 수 있는 일시적 오류
→ deadlock, 일시 network 오류

Skip
→ 특정 잘못된 item을 기록하고 나머지 계속 처리
→ parsing 또는 validation 오류

Fail
→ 설정·schema 오류처럼 전체 결과를 신뢰할 수 없음
```

무작정 skip하면 데이터가 조용히 누락된다. skip item, 원인, 원본 위치를 저장하고 임계치를 넘으면 Job을 실패시킨다.

## 중복 실행 방지

여러 application instance가 같은 cron을 실행할 수 있다.

```text
외부 scheduler가 단일 Job launch
DB 기반 scheduler lock
Kubernetes CronJob concurrencyPolicy
JobRepository와 business key constraint
```

Scheduler lock만 믿지 않고 Writer와 업무 결과도 idempotent하게 만든다.

## Partitioning과 Parallel Processing

```text
Multi-threaded Step
→ 한 process에서 병렬 처리

Partitioning
→ ID 범위나 날짜 범위로 나눠 worker 처리

Remote Chunking
→ manager가 item을 전달하고 remote worker가 처리
```

병렬성을 높이면 DB connection, lock, 외부 API quota가 병목이 될 수 있다. partition 경계가 겹치지 않는지와 thread-safe Reader/Writer인지 확인한다.

## Batch와 DB 부하

```text
운영 peak 시간 회피
chunk와 fetch size 조정
index 확인
한 번에 전체 Entity loading 금지
bulk update 검토
lock과 transaction 시간 관찰
read replica 사용 가능성 검토
```

대량 update가 online transaction을 방해하면 처리 속도를 일부러 제한하는 것이 전체 서비스에는 더 좋을 수 있다.

## 운영과 재처리

```text
Job 시작·완료·실패 알림
처리·skip·retry count
마지막 성공 시각
실행 parameter
실패 Step과 stack trace
수동 restart/runbook
오래 실행 중인 Job 탐지
```

## Test

```text
Reader가 대상만 읽는가?
Processor가 규칙대로 변환하는가?
Writer가 중복 실행에 안전한가?
중간 실패 후 restart되는가?
skip/retry limit이 동작하는가?
동시에 두 Job이 실행될 때 안전한가?
```

## 공식 참고 자료

- [Spring Batch Job Configuration](https://docs.spring.io/spring-batch/reference/job/configuring-job.html)
- [Spring Batch Restart](https://docs.spring.io/spring-batch/reference/step/chunk-oriented-processing/restart.html)

## 설명할 때 핵심 문장

```text
Spring Batch는 대량 작업을 Job과 Step으로 나누고 chunk transaction, 실행 이력, restart를 관리한다.
Batch의 핵심은 한 번 실행되는 것이 아니라 실패 후 어디서 어떻게 안전하게 재실행할지 정하는 것이다.
```
