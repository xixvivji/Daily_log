# 21. Kafka·RabbitMQ와 Transactional Outbox

## Message Broker를 쓰는 이유

```text
요청 path에서 느린 작업 분리
Producer와 Consumer 결합도 감소
traffic 완충
재시도와 replay
한 event를 여러 consumer가 처리
```

비동기 처리는 복잡성을 없애지 않고 처리 시점과 장애 위치를 옮긴다. 중복, 순서, 유실, backlog, schema 변경을 설계해야 한다.

## Queue와 Log

```text
RabbitMQ Queue
→ routing된 message를 consumer가 처리하고 ack 후 제거
→ 작업 분배와 유연한 routing에 적합

Kafka Partitioned Log
→ partition에 append하고 offset으로 읽음
→ 보관 기간 동안 replay 가능
→ 높은 처리량과 event stream에 적합
```

제품 이름보다 업무가 작업 queue인지, 여러 독립 consumer가 replay할 event log인지 판단한다.

## Delivery Semantics

```text
At-most-once
→ 손실 가능, 중복 감소

At-least-once
→ 재전달 가능, consumer 멱등성 필요

Exactly-once
→ broker와 처리 경계의 제한된 조건에서 제공
→ 외부 email, HTTP API, 별도 DB 부수 효과까지 자동 보장하지 않음
```

실무에서는 at-least-once와 idempotent consumer를 기본으로 보는 것이 안전하다.

## Event 설계

```json
{
  "eventId": "8ab1...",
  "eventType": "OrderCompleted",
  "occurredAt": "2026-07-11T10:00:00Z",
  "aggregateId": "order-100",
  "version": 1,
  "payload": {"memberId": 10, "amount": 30000}
}
```

Event는 이미 발생한 사실을 과거형으로 표현한다. Consumer가 producer DB를 다시 조회해야만 처리 가능한 얇은 event는 두 서비스의 시간적 결합을 키울 수 있다.

개인정보와 secret을 message에 불필요하게 넣지 않는다.

## Consumer Idempotency

```sql
CREATE TABLE processed_events (
    consumer_name VARCHAR(100) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    PRIMARY KEY (consumer_name, event_id)
);
```

업무 변경과 처리 기록을 같은 DB transaction에 저장한다. 단순 Redis 중복 key만 사용하면 Redis 기록과 DB commit 사이에 원자성 공백이 생길 수 있다.

업무 자체의 unique key나 상태 전이로 멱등성을 만들 수 있으면 더 강하다.

## 순서 보장

Kafka는 같은 partition 안에서 순서를 제공한다. 같은 주문의 event를 같은 partition으로 보내려면 `orderId`를 key로 사용할 수 있다.

```text
partition 수 증가
consumer 병렬성 증가
하지만 전체 global ordering은 없음
```

RabbitMQ도 여러 consumer와 redelivery가 있으면 처리 완료 순서가 publish 순서와 달라질 수 있다. 순서가 필요한 범위를 aggregate 단위로 좁힌다.

## Retry와 DLQ

```text
일시적 오류 → 제한적 retry + exponential backoff + jitter
영구 오류   → 즉시 DLQ 또는 실패 상태
```

무한 requeue는 poison message가 queue를 계속 순환하게 한다. 최대 횟수, 실패 원인, 다음 재시도 시각과 수동 replay 절차를 둔다.

DLQ도 monitoring과 담당자가 없으면 실패를 숨기는 저장소가 된다.

## RabbitMQ Ack와 Confirm

```text
Publisher Confirm
→ broker가 publish를 책임졌는지 producer에 알림

Consumer Ack
→ consumer가 처리를 완료했음을 broker에 알림
```

둘은 서로 다른 구간을 보호한다. Consumer는 DB commit 같은 필요한 부수 효과가 끝난 뒤 ack한다. Connection이 끊기면 미확인 message가 재전달될 수 있으므로 중복을 처리한다.

Prefetch가 너무 크면 consumer memory와 처리 중 message가 증가하고, 너무 작으면 처리량이 낮아질 수 있다.

## Kafka Producer와 Consumer

```text
Producer acks
→ broker replica 확인 수준

Idempotent Producer
→ retry 중 partition 내 중복 write를 줄임

Consumer Group
→ partition을 group consumer 사이에 분배

Offset Commit
→ 어디까지 처리했는지 기록
```

처리 전에 offset을 commit하면 장애 시 message를 잃을 수 있고, 처리 후 commit하면 중복 처리가 가능하다. DB 처리와 offset은 서로 다른 system이므로 idempotency가 필요하다.

## Dual Write 문제

```java
@Transactional
public void completeOrder(Long orderId) {
    order.complete();
    kafkaTemplate.send("orders", event); // DB transaction과 별개
}
```

DB commit과 publish 중 하나만 성공할 수 있다.

```text
DB commit 성공 + publish 실패 → event 유실
publish 성공 + DB rollback     → 존재하지 않는 변경의 event
```

## Transactional Outbox

```text
같은 DB transaction
→ Order update
→ Outbox row insert
→ commit

Publisher
→ 미발행 outbox 읽기
→ broker publish
→ 발행 상태 갱신
```

```sql
CREATE TABLE outbox_events (
    id VARCHAR(100) PRIMARY KEY,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    published_at TIMESTAMP NULL
);
```

Polling publisher 또는 CDC 도구로 전달할 수 있다. Publish 성공 후 상태 갱신 전에 장애가 나면 중복 발행할 수 있으므로 consumer 멱등성은 여전히 필요하다.

## Schema Evolution

```text
기존 field 제거·의미 변경 주의
새 field는 consumer가 무시할 수 있게 추가
event version 관리
producer와 consumer 배포 순서 고려
contract test
```

DB Entity를 그대로 직렬화하면 내부 모델 변경이 외부 event contract를 깨뜨릴 수 있으므로 event DTO를 분리한다.

## Monitoring

```text
publish success/failure/latency
consumer lag와 queue depth
processing latency와 error rate
retry와 DLQ 증가
oldest unprocessed message age
rebalance와 consumer 수
outbox 미발행 row 수
```

## 공식 참고 자료

- [RabbitMQ Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ Dead Letter Exchanges](https://www.rabbitmq.com/docs/dlx)

## 설명할 때 핵심 문장

```text
Message broker는 비동기 처리를 가능하게 하지만 중복, 순서, retry, backlog 문제를 추가한다.
Outbox는 DB 변경과 event 기록을 같은 transaction에 묶어 유실을 줄이지만 중복 publish 가능성은 남는다.
```
