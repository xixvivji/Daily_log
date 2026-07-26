# 무중단 Schema Migration·Online DDL 상세

Schema 변경은 SQL 한 줄로 끝나는 작업이 아니다. application 여러 version, 대형 table, lock, 복제 지연, rollback까지 포함한 배포 과정이다.

## 1. 왜 ALTER TABLE이 위험한가

개발 DB의 작은 table에서는 즉시 끝난 DDL이 운영에서는 다음을 일으킬 수 있다.

- table 전체 scan 또는 rewrite
- metadata/schema lock
- 기존 transaction과 lock 대기
- CPU·I/O·WAL/redo 급증
- replica lag
- 추가 임시 disk 공간 사용
- application query plan 변화
- 긴 DDL 실패 후 rollback·정리 비용

“Online DDL”도 보통 영향 0이라는 뜻은 아니다. 시작·종료 시 짧은 lock, 추가 I/O, 제한되는 동시 작업, replica 영향이 있을 수 있다.

## 2. 무중단의 정확한 목표

다음을 별도로 정의한다.

- 읽기 요청을 계속 받을 수 있는가?
- 쓰기 요청을 계속 받을 수 있는가?
- error rate와 latency 허용치는 얼마인가?
- 모든 replica와 region도 정상이어야 하는가?
- schema 구버전과 신버전 application이 얼마 동안 공존하는가?
- rollback 가능한 시점은 어디까지인가?

## 3. Expand and Contract

호환되지 않는 변경을 한 번에 하지 않고 **추가 → 병행 → 전환 → 제거**로 나눈다.

```text
Expand
  새 schema를 기존 기능을 깨지 않게 추가
→ Migrate
  기존 data backfill, dual write/read 검증
→ Switch
  새 application이 새 schema 사용
→ Contract
  더 이상 사용하지 않는 구 schema 제거
```

핵심 규칙은 배포 중 인접한 application version들이 같은 schema에서 모두 동작해야 한다는 것이다.

## 4. Column 이름 변경 예시

`users.name`을 `display_name`으로 바꾼다고 즉시 rename하면 구버전 application이 실패할 수 있다.

### 1단계: Expand

nullable한 새 column을 추가한다.

```sql
ALTER TABLE users ADD COLUMN display_name VARCHAR(200);
```

### 2단계: 새 쓰기 경로

새 application은 한동안 `name`과 `display_name`을 함께 기록한다. DB trigger로 동기화할 수도 있지만 숨은 쓰기와 recursion, 제거 시점을 관리해야 한다. application dual write는 부분 실패와 transaction 경계를 처리해야 한다.

### 3단계: Backfill

기존 row를 작은 batch로 채운다.

```sql
UPDATE users
SET display_name = name
WHERE user_id > :last_id
  AND user_id <= :next_id
  AND display_name IS NULL;
```

### 4단계: 검증과 Read 전환

NULL 수, key별 값 불일치, checksum, sample을 확인하고 새 column을 읽도록 application을 배포한다.

### 5단계: Constraint 강화

모든 writer 전환과 data 검증이 끝난 뒤 `NOT NULL` 등 constraint를 적용한다. 검증과 강제 적용을 분리할 수 있는 DBMS 기능을 활용하면 큰 table lock을 줄일 수 있다.

### 6단계: Contract

구버전 application이 완전히 사라지고 rollback window가 끝난 뒤 기존 column을 제거한다. 즉시 물리 삭제되지 않더라도 metadata·storage 동작을 제품별로 확인한다.

## 5. Backfill 설계

Backfill은 “UPDATE 한 번”이 아니라 운영 workload다.

### 작은 Batch

큰 transaction 하나 대신 PK/key range로 나눈다.

- lock 유지 시간 감소
- WAL/redo burst 완화
- replica lag 관찰 가능
- 중단 지점부터 재시작 가능
- rollback 크기 감소

### Idempotency

같은 batch를 다시 실행해도 결과가 같아야 한다. `WHERE new_column IS NULL` 같은 조건과 progress key를 사용한다.

### Throttling

batch마다 DB CPU, I/O, lock wait, WAL/redo, replica lag를 보고 속도를 조절한다. 고정 sleep만 믿지 말고 지표 기반으로 멈추고 재개한다.

### SKIP LOCKED의 한계

작업 queue에서는 유용할 수 있지만 잠긴 row를 건너뛰므로 마지막 재검사 단계가 필요하다. DBMS별 문법과 starvation 가능성을 확인한다.

## 6. Default와 NOT NULL 추가

새 column에 default와 `NOT NULL`을 한 번에 추가했을 때 table rewrite 여부는 DBMS version과 default 표현에 따라 다를 수 있다.

안전한 일반 절차:

```text
nullable column 추가
→ 새 write부터 값 기록
→ 기존 data batch backfill
→ NULL 0건 검증
→ default 설정
→ NOT NULL 검증·강제
```

최신 DBMS가 metadata-only 최적화를 지원하더라도 volatile expression, type, version 조건을 확인한다.

## 7. Index를 안전하게 생성하기

대형 table index 생성은 table scan, sort, 임시 공간, write 추적, WAL/redo를 유발한다.

### PostgreSQL

`CREATE INDEX CONCURRENTLY`는 일반 생성보다 쓰기 차단을 줄이지만 더 오래 걸리고 여러 단계 transaction을 기다린다. transaction block 제한, 실패 후 invalid index 정리, long transaction 영향을 확인한다.

### MySQL InnoDB

DDL algorithm과 lock option의 지원은 변경 종류와 version에 따라 다르다. 요청한 online 방식이 불가능할 때 error를 낼지 더 무거운 방식으로 fallback할지 명시적으로 확인한다.

### Oracle

Online index 생성·재구성 및 edition별 기능을 확인한다. 작업 중 redo, temporary space와 DML 영향이 사라지는 것은 아니다.

공통 확인 항목:

- 예상 생성 시간
- source table 크기와 증가율
- 임시·최종 disk 여유
- replica와 backup 영향
- 실패한 객체 정리법
- 취소했을 때 회복 시간

## 8. Type 변경

Column type 변경은 다음 셋으로 나눈다.

1. metadata만 바뀌는 호환 변경
2. index·constraint 재구성이 필요한 변경
3. 모든 row를 변환해 table rewrite가 필요한 변경

대규모 rewrite가 예상되면 새 column 또는 shadow table을 만들고 backfill·dual write·검증·전환하는 방식을 검토한다.

변환 실패 값도 미리 찾는다.

```sql
-- 문자열을 숫자로 옮기는 경우 개념 예시
SELECT id, legacy_value
FROM source
WHERE legacy_value가_목표_숫자형으로_변환되지_않음;
```

DBMS마다 안전한 변환 검사 문법이 다르므로 production SQL은 대상 제품에서 작성한다.

## 9. Table 이름 변경·분리·병합

### Table rename

View나 synonym으로 구 이름을 잠시 유지할 수 있지만 write 가능성, constraint, ORM mapping, 권한을 확인한다.

### Table 분리

한 table을 두 table로 나눌 때:

```text
새 table 추가
→ dual write 또는 change capture
→ historical backfill
→ 불일치 검증
→ read 전환
→ 구 column 제거
```

### Table 병합

key 충돌, 중복 row, FK 재연결, delete 전파, sequence 범위를 먼저 해결한다.

## 10. Foreign Key 추가

기존 대형 table에 FK를 추가하면 모든 기존 row 검증과 lock이 필요할 수 있다.

안전한 흐름:

```text
고아 row 사전 탐지·정리
→ 새 write에 관계 규칙 적용
→ 가능하면 constraint 생성과 기존 data 검증 분리
→ 부하가 낮을 때 검증
→ 실제 위반 0건 확인
```

FK child column index는 parent 삭제·변경과 JOIN 성능에 중요하지만 DBMS가 자동 생성하는지 가정하지 않는다.

## 11. 호환성 Matrix

배포 전에 구·신 application과 구·신 schema 조합을 기록한다.

| Application | 기존 Schema | 확장 Schema | 축소 후 Schema |
|---|---:|---:|---:|
| 구버전 | 가능 | 가능해야 함 | 보통 불가능 |
| 신버전 | 가능하도록 설계할 수 있음 | 가능 | 가능 |

Contract는 구버전 instance, worker, batch, mobile client, rollback artifact가 더 이상 구 column을 사용하지 않을 때만 진행한다.

## 12. Migration 도구

Flyway, Liquibase 같은 도구는 version과 실행 이력을 관리하지만 DDL을 자동으로 무중단화하지 않는다.

좋은 migration file의 특성:

- 한 변경의 목적이 명확함
- 재실행·부분 실패 처리 방침이 있음
- 실행 시간과 lock 위험을 사전 측정
- application 배포 순서가 문서화됨
- rollback 또는 forward-fix 절차가 있음
- production 권한과 감사 기록을 고려

이미 공유된 migration 파일을 나중에 수정하면 환경별 checksum과 이력이 갈라질 수 있다. 새 migration으로 수정하는 정책을 둔다.

## 13. DDL Transaction 차이

DDL이 transaction rollback 가능한지, 암시적 commit을 일으키는지 DBMS마다 다르다.

- PostgreSQL: 많은 DDL이 transactional이지만 concurrent index 등 예외와 외부 효과를 확인
- MySQL: atomic DDL 개선과 별개로 DDL의 implicit commit, online algorithm 조건을 확인
- Oracle: DDL 전후 implicit commit 특성과 edition 기능을 고려

“실패하면 전체 rollback”이라고 가정하지 말고 각 단계가 어디까지 적용됐는지 탐지하는 절차를 둔다.

## 14. Lock과 Long Transaction

짧은 metadata lock도 기존 long transaction 때문에 오래 대기할 수 있다. 그동안 뒤에 온 query까지 queue를 만들 수 있다.

실행 전 확인:

- 현재 long transaction
- idle in transaction
- 대상 table을 사용하는 batch
- lock timeout과 statement timeout
- DDL이 기다릴지 즉시 실패할지
- application retry가 부하를 증폭하는지

작업을 무기한 기다리게 하기보다 짧은 lock timeout으로 안전하게 실패시키고 조건을 정리한 후 다시 시도하는 전략이 유용할 수 있다.

## 15. Replication·CDC 영향

Primary에서 끝났다고 migration이 끝난 것이 아니다.

- replica가 DDL·backfill을 재생하는 시간
- replica lag와 read stale
- logical replication/CDC가 새 column을 전달하는지
- schema registry와 consumer 호환성
- Debezium 같은 connector의 schema change 처리
- data warehouse ETL과 BI query

Backfill이 대량 change event를 만들어 downstream을 압도할 수도 있다. event를 구분하거나 consumer capacity를 준비한다.

## 16. 검증

### 구조 검증

- column type·default·nullable
- index·constraint·FK
- owner·role·privilege
- trigger·generated column

### 데이터 검증

- 전체 row 수
- NULL과 중복 수
- key range별 checksum/aggregate
- 구·신 column 불일치
- FK orphan
- 시간·문자열·소수 경계값

### 성능 검증

- 대표 query 실행 계획
- p50/p95/p99 latency
- CPU·I/O·buffer
- lock wait·deadlock
- WAL/redo·replica lag

## 17. Rollback과 Forward Fix

Schema 변경은 application binary처럼 단순히 이전 version으로 되돌리기 어렵다. 새 application이 새 형식 data를 쓰기 시작하면 구버전이 읽지 못할 수 있다.

단계별로 결정한다.

- application만 rollback 가능한가?
- dual write 중 어느 column이 source of truth인가?
- backfill을 역변환할 수 있는가?
- 이미 삭제한 data를 backup/PITR 없이 복구할 수 있는가?
- rollback보다 수정 migration을 앞으로 적용하는 것이 안전한가?

파괴적 Contract를 늦추면 rollback window가 길어진다.

## 18. 운영 Runbook

```text
사전
1. 대상·row 수·크기·version 확인
2. staging에서 production 규모로 시간·lock 측정
3. backup과 restore 가능성 확인
4. 지표 dashboard·alert·중단 기준 정의
5. application/schema 호환 순서 승인

실행
6. Expand DDL
7. 새 writer 배포
8. throttle 가능한 backfill
9. 불일치·lag·latency 지속 확인
10. read 전환과 constraint 검증

사후
11. 모든 구 consumer 제거 확인
12. rollback window 경과
13. Contract DDL
14. 통계 갱신·실행 계획·공간 확인
15. migration 결과와 소요 시간 기록
```

## 19. 중단 기준 예시

- DB CPU·I/O가 정한 한계 초과
- p99 latency 또는 error rate 증가
- lock wait가 업무 SLO 초과
- replica lag가 허용 범위 초과
- disk 여유가 안전선 아래로 감소
- checksum·불일치 건수가 예상과 다름
- CDC consumer backlog 급증

중단 기준은 작업 도중 즉흥적으로 정하지 않는다.

## 20. 최종 점검표

- 변경을 Expand·Migrate·Switch·Contract로 나눴는가?
- 구·신 application이 동시에 동작하는 기간을 고려했는가?
- 실제 DBMS version에서 DDL algorithm과 lock을 확인했는가?
- backfill이 batch·idempotent·restartable한가?
- DDL과 backfill의 disk·WAL/redo·replica 영향을 계산했는가?
- long transaction을 사전에 확인했는가?
- Flyway/Liquibase 사용을 무중단 보장으로 오해하지 않는가?
- CDC·DW·batch·mobile client까지 schema consumer를 찾았는가?
- 단계별 rollback/forward-fix와 source of truth가 정해졌는가?
- Contract 전에 rollback window와 구버전 제거를 확인했는가?
