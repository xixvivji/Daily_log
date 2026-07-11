# 20. Redis와 Cache 실전

## Redis를 쓰는 이유

Redis는 memory 중심 key-value data store다.

```text
Cache
Session store
Rate limit counter
분산 coordination
짧은 수명의 상태
Stream과 Pub/Sub
```

Redis가 빠르다고 모든 데이터를 옮기는 것이 아니라, 원본 저장소와 일관성 요구를 기준으로 사용한다.

## Cache Aside

```text
1. Redis 조회
2. hit면 반환
3. miss면 DB 조회
4. Redis 저장
5. 반환
```

```java
@Cacheable(cacheNames = "members", key = "#id")
public MemberResponse findById(Long id) { ... }
```

수정 시:

```java
@CacheEvict(cacheNames = "members", key = "#id")
@Transactional
public void update(Long id, MemberUpdateRequest request) { ... }
```

Annotation은 편리하지만 key, TTL, 직렬화, 예외, transaction commit 시점을 숨길 수 있으므로 실제 동작을 확인한다.

## Cache 일관성

```text
DB update 후 cache 삭제
→ 삭제 실패하면 stale cache

cache 삭제 후 DB update
→ 사이에 다른 요청이 이전 DB 값을 cache할 수 있음
```

완벽한 원자성을 얻기 어렵기 때문에 허용 가능한 stale 시간과 복구 방식을 정한다.

```text
짧은 TTL
transaction commit 이후 evict
event 기반 invalidation
version을 key에 포함
중요 조회는 cache를 사용하지 않음
```

## TTL과 Eviction

TTL은 데이터 유효 시간이고 eviction은 memory가 부족할 때 어떤 key를 제거할지 정하는 정책이다.

```text
allkeys-lru
allkeys-lfu
volatile-ttl
noeviction
```

Cache 용도라면 `maxmemory`와 eviction policy를 반드시 설정한다. TTL이 있다고 memory 한도가 자동 설정되는 것은 아니다.

TTL에 작은 random jitter를 추가하면 인기 key가 동시에 만료되는 현상을 줄일 수 있다.

## Cache Stampede

인기 key가 만료되는 순간 많은 요청이 DB를 동시에 조회하는 문제다.

대응:

```text
single flight 또는 lock으로 한 요청만 갱신
TTL jitter
만료 전 background refresh
stale 값을 짧게 제공하며 갱신
DB와 downstream rate limit
```

## Cache Penetration

존재하지 않는 key를 반복 요청해 매번 DB까지 가는 문제다.

```text
짧은 negative cache
입력 validation
Bloom filter
공격성 traffic rate limit
```

`null` cache는 실제 데이터 생성 후에도 TTL 동안 없는 것으로 보일 수 있어 invalidation이 필요하다.

## Key 설계

```text
app:prod:member:123
app:prod:product:10:v2
```

```text
namespace 포함
환경 충돌 방지
업무 식별자 명확화
schema 변경 시 version 고려
무제한 cardinality 방지
```

긴 원본 JSON 전체나 개인정보를 key에 넣으면 memory와 log 노출 문제가 생길 수 있다.

## Serialization

```text
String/JSON
→ 확인과 호환이 쉬움, 크기와 parsing 비용

Binary
→ 작고 빠를 수 있음, schema 호환과 디버깅 어려움

Java native serialization
→ 보안과 호환 문제로 일반적으로 피함
```

class 변경 후 이전 cache를 읽을 수 있는지와 polymorphic type 정보의 보안 위험을 확인한다.

## Redis 자료구조

```text
String → cache, counter, token
Hash   → object field
Set    → 중복 없는 membership
Sorted Set → ranking, 시간순 score
List   → 단순 queue
Stream → consumer group과 replay 가능한 event log
```

한 key에 매우 큰 collection을 만들면 단일 command 지연과 network payload가 커진다.

## Session Store

Spring Session으로 여러 application instance가 session을 공유할 수 있다.

```text
장점 → scale-out 시 session 공유
주의 → Redis 장애가 전체 로그인 요청에 영향
```

Session TTL, logout 삭제, serialization 호환, failover를 test한다.

## Rate Limiting

```text
Fixed Window
Sliding Window
Token Bucket
Leaky Bucket
```

단순 `INCR`와 `EXPIRE`를 별도 command로 실행하면 중간 실패가 생길 수 있어 Lua script나 atomic command 조합을 사용한다. 기준은 IP만이 아니라 사용자, API key, endpoint 비용을 함께 고려한다.

## 분산 Lock 주의점

Lock key에는 소유자별 random token과 TTL이 필요하고 해제할 때 token이 같은지 atomic하게 확인한다.

하지만 Redis failover와 network partition에서 항상 하나의 소유자만 보장된다고 단순 가정하면 안 된다. 중요한 정합성은 DB constraint나 fencing token 같은 추가 방어가 필요하다.

## 장애 대응

```text
짧은 connect/command timeout
무제한 retry 금지
Cache 장애 시 DB fallback 부하 제한
connection pool metric
memory/eviction/latency/replication lag 관찰
대형 key와 hot key 탐지
```

Redis가 죽었을 때 모든 요청이 동시에 DB로 fallback하면 DB까지 장애가 전파될 수 있다.

## 공식 참고 자료

- [Redis Key Eviction](https://redis.io/docs/latest/develop/reference/eviction/)
- [Redis Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)

## 설명할 때 핵심 문장

```text
Cache는 원본 데이터의 복사본이므로 TTL, invalidation, stale 허용 범위를 설계해야 한다.
Redis 성능보다 장애 시 DB로 부하가 몰리는 상황과 memory eviction 정책이 더 중요할 수 있다.
```
