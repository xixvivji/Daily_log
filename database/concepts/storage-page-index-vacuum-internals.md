# 저장 구조·Page·Index·VACUUM 내부 원리

SQL은 논리적으로 row를 다루지만 DBMS는 storage에서 page/block 단위로 읽고 쓴다. 이 차이를 이해하면 “index가 있는데 왜 느린가”, “UPDATE했는데 왜 table이 커지는가”를 설명할 수 있다.

## 1. 논리 구조와 물리 구조

```text
논리: Database → Schema → Table → Row → Column
물리: Datafile/Segment → Extent → Page(Block) → Record(Tuple)
```

제품마다 이름과 구현은 다르지만 disk와 buffer cache 사이의 I/O 기본 단위는 보통 page/block이다. 한 row만 필요해도 그 row가 들어 있는 page를 읽는다.

## 2. Page·Block·Extent

- Page/Block: DBMS가 저장하고 cache하며 읽는 기본 단위
- Extent: 연속 또는 묶음으로 할당되는 여러 page
- Segment/Table space/Datafile: 객체와 공간을 관리하는 더 큰 단위

Page에는 row만 들어 있지 않다. header, slot/line pointer, free space, visibility·transaction 정보 등이 함께 저장된다. 한 row가 너무 크면 overflow/TOAST 같은 별도 저장 방식이 사용될 수 있다.

Page 크기와 row 크기는 다음에 영향을 준다.

- 한 page에 들어가는 row 수
- query가 읽는 page 수
- cache 효율
- update 시 남는 free space
- index fan-out과 tree 높이

## 3. Buffer Cache

DBMS는 매번 storage에서 직접 읽지 않고 자주 쓰는 page를 memory buffer cache에 둔다.

```text
Query가 page 요청
→ cache에 있음: memory hit
→ cache에 없음: storage read 후 cache 적재
```

OS page cache를 함께 사용하는 제품도 있고 DB가 큰 전용 cache를 관리하는 제품도 있다. 실행 시간이 짧아졌다고 SQL 자체가 개선된 것은 아닐 수 있다. 첫 실행은 cold cache, 다음 실행은 warm cache일 수 있으므로 buffer read와 physical I/O를 함께 본다.

## 4. Heap Table과 Clustered 구조

### Heap

논리 key 순서와 물리 row 위치가 직접 일치하지 않는 일반 table 구조다. PostgreSQL heap table에서 index는 tuple 위치를 가리킨다. row version이 새 위치에 생기면 index와 visibility 확인이 중요하다.

### MySQL InnoDB Clustered Primary Key

InnoDB table의 row는 primary key를 기준으로 한 clustered index의 leaf에 저장되는 구조로 이해할 수 있다. Secondary index leaf는 보통 row의 primary key를 포함한다.

```text
secondary index 탐색
→ primary key 획득
→ clustered primary key 다시 탐색
→ 전체 row 획득
```

그래서 primary key가 매우 크면 모든 secondary index도 커질 수 있다. Random한 key는 page locality와 split에 영향을 줄 수 있다.

### SQL Server·Oracle 관점

SQL Server는 heap과 clustered index table을 선택할 수 있다. Oracle heap-organized table은 ROWID로 물리 row 위치를 식별하고 index-organized table이라는 별도 선택도 있다. 이름이 비슷하다고 MySQL clustered 구조와 완전히 같다고 보지 않는다.

## 5. B-Tree Index 내부

B-Tree 계열 index는 정렬된 key와 pointer를 tree 구조로 유지한다.

```text
Root
 ├─ Internal page
 │   ├─ Leaf page: key 001~100
 │   └─ Leaf page: key 101~200
 └─ Internal page
     └─ Leaf page: key 201~300
```

한 page에 많은 key가 들어가므로 tree 높이는 보통 낮다. equality와 범위 탐색에 강한 이유는 root에서 범위를 좁힌 뒤 leaf를 순서대로 읽을 수 있기 때문이다.

### 복합 Index의 정렬

`INDEX (tenant_id, created_at, order_id)`는 사전식으로 정렬된다.

```text
tenant_id 우선
→ 같은 tenant 안에서 created_at
→ 둘 다 같으면 order_id
```

따라서 선두 column 조건 없이 뒤 column만 찾을 때 효율이 제한될 수 있다. “자주 쓰는 column을 모두 넣기”가 아니라 equality, range, ordering, selectivity, covering, 쓰기 비용을 함께 설계한다.

## 6. Page Split

가득 찬 B-Tree leaf 중간에 새 key를 넣어야 하면 page를 나누고 일부 key를 새 page로 이동할 수 있다.

비용:

- 추가 page 할당과 write
- WAL/redo 증가
- page fragmentation
- cache locality 저하 가능

증가하는 key는 보통 끝부분에 삽입돼 중간 random insert와 동작이 다르다. 그러나 증가 key는 동시 insert가 특정 끝 page에 집중되는 hot spot을 만들 수 있다. UUID도 version과 생성 방식에 따라 locality가 다르다.

## 7. Fill Factor와 Free Space

Fill factor는 page를 처음부터 얼마나 채울지 조절하는 개념이다. 여유 공간을 남기면 update·중간 insert의 split을 줄일 수 있지만 index나 table 크기가 커져 read 효율이 떨어질 수 있다.

모든 객체에 낮은 fill factor를 적용하지 않는다. update 패턴, key 분포, page split, 공간 사용량을 측정해 결정한다. 제품마다 적용 대상과 재구성 시점이 다르다.

## 8. MVCC가 만드는 Row Version

MVCC에서는 reader와 writer가 서로 덜 막히도록 여러 transaction이 서로 다른 row version을 볼 수 있다.

### PostgreSQL

UPDATE는 일반적으로 새 tuple version을 만들고 이전 version은 즉시 물리 삭제되지 않는다. 더 이상 어떤 snapshot에도 필요하지 않을 때 VACUUM이 재사용 가능하게 정리한다.

### MySQL InnoDB

현재 record와 undo 정보를 이용해 필요한 이전 version을 구성한다. 오래된 snapshot이 유지되면 purge가 이전 version 정리를 진행하지 못할 수 있다.

### Oracle

Undo segment를 통해 read consistency와 rollback을 제공한다. 필요한 undo가 재사용돼 버리면 오래 실행한 query가 과거 version을 재구성하지 못하는 문제가 생길 수 있다.

공통 핵심은 **long transaction이 오래된 version 정리를 방해하고 공간·복구·성능 비용을 키울 수 있다**는 것이다.

## 9. PostgreSQL VACUUM

VACUUM은 일반적으로 다음 역할을 한다.

- 더 이상 보이지 않는 dead tuple 공간을 재사용 가능하게 표시
- visibility map 등 index-only scan 관련 정보 관리
- transaction ID wraparound 방지를 위한 freeze 작업
- planner 통계 갱신은 `ANALYZE`가 담당하며 `VACUUM ANALYZE`로 함께 실행 가능

일반 VACUUM이 table file을 운영체제에 항상 즉시 반환하는 것은 아니다. 내부에서 재사용할 공간으로 만든다. 물리 file 축소에는 더 강한 작업이 필요할 수 있고 큰 lock·추가 공간·I/O 비용을 고려한다.

### Autovacuum

Autovacuum은 table 변경량 등을 기준으로 VACUUM/ANALYZE를 자동 실행한다. 기본값을 끄는 것은 해결책이 아니다. 큰 table, update가 많은 table, partition별 특성에 맞춰 threshold·scale factor, worker, 비용 제한 등을 관찰하고 조정한다.

확인할 신호:

- dead tuple 증가
- 마지막 vacuum/analyze 시각
- autovacuum이 오래 걸리거나 반복 취소
- long/idle-in-transaction session
- table·index bloat
- transaction age와 wraparound 위험

## 10. PostgreSQL HOT Update

Heap-Only Tuple(HOT) update는 index가 참조하는 column을 변경하지 않고 같은 heap page에 새 tuple을 둘 공간이 있을 때 불필요한 index entry 추가를 줄일 수 있는 최적화다.

HOT 가능성은 다음과 관련된다.

- 변경 column이 index에 포함되는지
- 같은 page에 free space가 있는지
- table fillfactor와 row 크기

HOT을 기대해 필요한 index를 제거하는 것이 아니라 workload에서 update 비용과 read 이득을 함께 비교한다.

## 11. Index Bloat와 불필요한 Index

Index도 insert/update/delete로 page가 분할되고 사용하지 않는 entry와 빈 공간이 생길 수 있다. 그러나 file이 크다는 이유만으로 전부 bloat는 아니다.

불필요한 index 비용:

- 모든 관련 write마다 index 유지
- WAL/redo와 replication traffic 증가
- backup과 cache 공간 증가
- optimizer 선택지와 maintenance 증가

삭제 전에는 사용 통계의 관찰 기간, 계절성 query, constraint/FK 용도, replica와 batch workload를 확인한다. “사용 횟수 0” 통계가 최근 restart 이후만 집계됐을 수도 있다.

## 12. Index Only Scan이 항상 Table을 안 읽는 것은 아니다

필요 column이 index에 모두 있어도 visibility 확인이 필요할 수 있다.

- PostgreSQL: visibility map 상태에 따라 heap fetch 발생
- MySQL InnoDB: covering secondary index로 해결 가능하지만 MVCC와 필요한 column·조건을 확인
- Oracle: index-only 접근 가능 여부와 NULL 저장·table access 계획 확인

실행 계획 node 이름만 보지 말고 실제 heap/table fetch와 buffer를 확인한다.

## 13. 통계와 Cardinality Estimation

Optimizer는 모든 실행 방법을 실제로 돌려보지 않고 통계로 row 수와 비용을 추정한다.

대표 통계:

- 전체 row와 page 수
- distinct 값 수
- NULL 비율
- 빈도와 histogram
- column 간 상관관계 또는 확장 통계
- index clustering/correlation

예상 10행, 실제 100만 행이라면 optimizer가 나쁜 것이 아니라 입력 정보가 부족하거나 데이터 분포가 변했을 수 있다.

원인 후보:

- 통계가 오래됨
- tenant별 data skew
- 두 column이 강하게 상관되는데 독립으로 가정
- function·expression 결과 통계 부족
- prepared statement의 일반화된 plan
- 임시 table·변수의 통계 제한

통계를 갱신한 뒤에도 SQL 의미, histogram, extended statistics, parameter별 plan을 검토한다.

## 14. Sequential Scan이 항상 나쁜 것은 아니다

table의 많은 행이 필요하면 index에서 위치를 찾고 table page를 무작위로 읽는 것보다 순차 scan이 저렴할 수 있다. 작은 table은 한 번에 읽는 편이 낫다.

```text
필요 행이 매우 적음 → index 접근 후보
중간 범위           → bitmap/범위 접근 후보
대부분의 행         → sequential/table scan 후보
```

고정 비율 규칙은 없다. row 폭, cache, storage, clustering, 병렬 처리, 비용 parameter에 따라 달라진다.

## 15. Write Amplification

한 번의 논리적 UPDATE가 여러 물리 write를 만들 수 있다.

```text
table/clustered record 변경
+ 관련 secondary index 변경
+ WAL/redo
+ undo 또는 old row version
+ replica 전송
+ backup·CDC 영향
```

읽기 최적화를 위해 index와 MV를 추가할 때 write amplification을 함께 계산한다.

## 16. DBMS별 빠른 비교

| 주제 | MySQL InnoDB | PostgreSQL | Oracle |
| --- | --- | --- | --- |
| 기본 row 조직 | clustered PK 중심 | heap + 별도 index | heap + ROWID가 일반적 |
| 과거 version | undo + purge | heap tuple + VACUUM | undo segment |
| 물리 위치 변화 | PK 구조와 secondary lookup 고려 | tuple version·HOT·heap fetch | row migration/chaining 등 고려 |
| 통계 | optimizer statistics/histogram | ANALYZE·extended statistics | optimizer statistics/histogram |
| 공간 정리 | purge와 table rebuild 계열 구분 | VACUUM과 file 축소 작업 구분 | segment 공간 관리와 shrink/move 등 구분 |

실제 명령과 online 가능 범위는 version, edition, storage 설정에 따라 검증한다.

## 17. 진단 순서

```text
1. 느린 SQL과 실제 실행 계획 확보
2. 실제 rows·loops·buffers 확인
3. 읽은 page와 반환 row 비율 확인
4. 통계 시각과 estimate 오차 확인
5. table·index 크기와 증가 추세 확인
6. long transaction과 old version 정리 상태 확인
7. index write 비용과 사용 빈도 확인
8. 변경 전후 같은 workload로 비교
```

## 18. 최종 점검표

- DBMS가 row가 아니라 page 단위로 I/O한다는 점을 이해했는가?
- heap과 clustered table의 차이를 대상 DBMS 기준으로 확인했는가?
- 복합 index의 실제 정렬 순서를 설명할 수 있는가?
- page split, fill factor, random key의 trade-off를 아는가?
- long transaction이 VACUUM·purge·undo에 주는 영향을 보는가?
- PostgreSQL autovacuum을 단순히 끄지 않고 원인을 측정하는가?
- index-only plan의 실제 table/heap fetch를 확인하는가?
- 예상 rows와 실제 rows가 다르면 통계와 skew를 조사하는가?
- index 추가 전 write amplification과 저장 공간을 계산하는가?
