# WAL과 Consensus

[← 핵심 용어 문서로 돌아가기](../01-database-course-map-and-glossary.md)

## 이 개념이 중요한 이유

WAL은 한 DB instance가 장애 후 자신의 상태를 복구하는 원리를 이해하는 핵심이고, consensus는 여러 node가 있는 DB cluster에서 어떤 변경을 공식 결과로 인정할지 이해하는 핵심이다.

다음 제품과 구조를 공부할 때 필요하다.

- Google Spanner
- CockroachDB
- TiDB와 TiKV
- etcd
- YugabyteDB
- 일부 cloud-native DB의 metadata·storage cluster
- Kafka controller와 replicated log 구조

## 강의 문장의 정확한 해석

강의에서는 다음처럼 단순화했다.

```text
WAL
→ 한 DB 안에서 장애 대비 안전장치

Consensus
→ 여러 DB가 흩어져 있어도 모두 같은 결과를 보장하는 안전장치
```

학습 방향은 맞지만, 더 정확하게는 다음과 같다.

```text
WAL
→ 변경을 data page보다 log에 먼저 기록해
  한 node가 crash 후 committed state를 재현할 수 있게 하는 원칙

Consensus
→ 여러 node 중 장애와 network 분리가 발생해도
  어떤 log와 leader를 공식 결과로 인정할지 합의하는 protocol
```

WAL이 반드시 “한 DB 안에서만” 사용되는 것은 아니다. 분산 DB의 각 node도 local durability를 위해 WAL이나 유사한 persistent log를 사용할 수 있다.

Consensus도 “모든 node가 매 순간 완전히 같은 data를 가진다”는 뜻은 아니다. follower가 일시적으로 뒤처질 수 있지만, protocol의 조건과 quorum 아래에서 서로 충돌하는 두 결과가 동시에 commit되는 것을 방지한다.

## 해결하는 문제가 다르다

### WAL이 해결하는 질문

```text
이 node가 갑자기 꺼졌다가 다시 켜졌을 때
성공 처리한 transaction을 어떻게 복구할까?
```

### Consensus가 해결하는 질문

```text
node가 여러 개인데 network가 끊기거나 leader가 죽었다면
어느 node의 변경 이력을 공식 기록으로 인정할까?
```

WAL만으로는 여러 node 사이의 충돌을 해결하지 못한다. 각 node가 서로 다른 log를 안전하게 저장했더라도 어떤 log가 cluster의 정답인지 결정해야 한다.

Consensus만으로 local storage의 durability가 자동으로 완성되는 것도 아니다. consensus에 참여한 node는 합의 log를 재시작 후에도 복구할 수 있도록 안정적으로 저장해야 한다.

## 함께 사용하는 구조

분산 DB에서는 둘을 함께 사용할 수 있다.

```text
Client write
→ Leader가 변경 log 생성
→ Followers에 log 복제
→ Quorum이 log를 durable하게 기록
→ 해당 log entry를 committed로 결정
→ 각 node가 state machine 또는 data page에 적용
```

여기서:

- local WAL·persistent log는 각 node의 crash recovery를 담당한다.
- consensus는 어느 log entry가 cluster에서 committed되었는지 결정한다.

## Raft의 기본 흐름

Raft는 consensus를 설명할 때 자주 사용하는 algorithm이다.

### 1. Leader 선출

node는 일반적으로 다음 상태 중 하나다.

- **Leader**: client write를 받고 log 복제를 주도
- **Follower**: leader의 log를 복제
- **Candidate**: leader가 보이지 않을 때 election에 참여

각 election 시기를 **term**으로 구분한다.

### 2. Log 복제

```text
Client
→ Leader: x = 10 요청
→ Leader가 자신의 log에 entry 추가
→ Followers에 AppendEntries 전송
→ 다수 node가 기록했다고 응답
→ Leader가 entry를 committed로 결정
→ state machine에 적용하고 client에 성공 응답
```

### 3. Quorum

일반적인 과반수 quorum:

```text
3 nodes → 2 nodes 필요
5 nodes → 3 nodes 필요
```

과반수 quorum끼리는 최소 한 node가 겹치므로, 서로 모순되는 두 값이 각각 과반수에게 동시에 commit되는 것을 막는 기반이 된다.

## Network Partition 예시

5개 node가 다음처럼 분리됐다고 가정한다.

```text
Partition A: 3 nodes
Partition B: 2 nodes
```

과반수가 필요한 구조라면:

- A는 quorum 3을 확보해 leader를 정하고 write를 계속할 수 있다.
- B는 quorum을 확보하지 못해 새로운 write를 commit할 수 없다.

B가 write를 거절한다고 해서 algorithm이 실패한 것이 아니다. 서로 충돌하는 두 cluster가 동시에 성공 응답을 주는 split-brain을 방지하기 위한 safety 선택이다.

## “모든 node가 같은 결과”의 정확한 의미

Consensus가 보장하려는 핵심은 보통 다음과 같은 **safety**다.

```text
같은 log 위치에 서로 다른 두 값이
모두 committed 결과로 인정되지 않게 한다.
```

다음과는 다르다.

```text
모든 follower가 매 순간 leader와 byte 단위로 완전히 동일하다.
모든 replica read가 언제나 가장 최신 값을 반환한다.
network가 끊겨도 모든 partition에서 write가 가능하다.
```

follower read가 최신인지 여부는 read consistency와 lease, read index, timestamp, routing 정책 등에 따라 달라진다.

## Consensus와 Replication의 차이

- **Replication**: data나 log를 다른 node에 복사하는 행위
- **Consensus**: 복제본 중 어떤 순서와 값을 공식 commit으로 인정할지 합의하는 protocol

단순 asynchronous primary-replica도 replication이지만 모든 구성이 Raft/Paxos consensus를 사용하는 것은 아니다.

## Consensus와 Distributed Transaction의 차이

둘도 같은 개념이 아니다.

- **Consensus**: replica group 안에서 하나의 log나 상태에 합의
- **Distributed Transaction**: 여러 shard 또는 service의 transaction을 하나의 업무 단위로 조정

분산 transaction은 2PC를 사용할 수 있고, 각 participant shard 내부에서는 Raft 같은 consensus를 사용할 수 있다.

```text
Distributed transaction coordinator
├── Shard A: Raft replica group
├── Shard B: Raft replica group
└── Shard C: Raft replica group
```

2PC와 consensus는 서로 대체 관계가 아니라 다른 층에서 함께 사용될 수 있다.

## Raft와 Paxos

### Raft

- 이해와 구현 가능성을 강조
- leader election, log replication, safety 규칙을 명확히 분리
- etcd, TiKV 등에서 활용

### Paxos 계열

- proposal과 quorum을 통해 값에 합의
- Multi-Paxos 등 반복 log 합의를 위한 변형 존재
- 분산 system 이론과 여러 상용 system에 큰 영향

제품이 “Paxos 사용” 또는 “Raft 사용”이라고 적었다고 해서 사용자에게 제공하는 transaction consistency가 자동으로 동일해지는 것은 아니다. timestamp, shard transaction, read policy까지 함께 봐야 한다.

## WAL, Replication, Consensus 비교

| 구분 | WAL | Replication | Consensus |
| --- | --- | --- | --- |
| 핵심 목적 | local crash recovery와 durability | data·log 복사 | 공식 log 순서와 leader 합의 |
| 주요 범위 | 한 node의 storage | 둘 이상의 node | replica group |
| network partition 해결 | 직접 해결하지 않음 | 방식에 따라 다름 | quorum으로 충돌 commit 방지 |
| follower 지연 가능 | 해당 없음 | 가능 | 가능 |
| 대표 용어 | WAL, redo, LSN | primary, replica, lag | term, leader, quorum, committed index |

## 성능과 가용성 Trade-off

Consensus write는 일반적으로 network 왕복과 quorum 응답을 기다린다.

```text
더 많은 replica와 먼 region
→ 장애 허용 범위 증가 가능
→ write latency 증가 가능
```

quorum을 얻지 못하면 consistency를 지키기 위해 write를 거절할 수 있다. 따라서 “consensus를 사용하면 항상 availability도 높다”고 단순하게 말하면 안 된다.

## 면접에서 설명하는 문장

```text
WAL은 각 node가 commit된 변경을 crash 후 복구하기 위한 local durability 장치입니다.
Consensus는 여러 node 중 어떤 log entry를 cluster의 commit 결과로 인정할지 quorum으로 합의합니다.
분산 DB에서는 각 node가 WAL로 log를 보존하고, Raft 같은 consensus로 그 log의 순서와 commit 여부를 결정할 수 있습니다.
```

## 핵심 정리

```text
WAL만 있음
→ 한 node의 복구는 가능
→ 여러 node 중 누구의 기록이 정답인지는 결정하지 못함

Consensus만 있음
→ cluster의 공식 log는 결정 가능
→ 각 node가 그 log를 재시작 후 복구할 local durability도 필요

둘을 결합
→ node별 crash recovery + cluster 차원의 합의
```

