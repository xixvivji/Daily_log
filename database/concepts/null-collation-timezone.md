# NULL·Collation·Timezone 상세

DBMS를 바꿀 때 문법보다 더 위험한 것은 같은 SQL이 서로 다른 결과를 만드는 경우다. NULL, 문자열 비교, 시간 처리는 데이터 정합성과 조회 결과를 직접 바꾼다.

## 1. NULL은 빈 값이 아니다

`NULL`은 숫자 0, 빈 문자열 `''`, 공백 `' '`, 문자열 `'NULL'`이 아니다. 일반적으로 **값이 없거나 알 수 없음**을 나타내는 표지다.

```text
0       → 숫자 값이 0
''      → 길이가 0인 문자열
' '     → 공백 문자 하나
NULL    → 알려진 값이 없음
```

Oracle Database는 SQL의 문자 처리에서 길이 0인 문자열을 NULL처럼 취급하는 특성이 있다. MySQL·PostgreSQL의 빈 문자열과 그대로 같다고 생각하면 이식 과정에서 결과가 달라진다.

## 2. SQL의 3값 논리

일반 논리에는 TRUE와 FALSE가 있지만 NULL이 참여하는 SQL 조건에는 UNKNOWN이 생긴다.

| 비교 | 결과 |
| --- | --- |
| `10 = 10` | TRUE |
| `10 = 20` | FALSE |
| `10 = NULL` | UNKNOWN |
| `NULL = NULL` | UNKNOWN |
| `NULL <> NULL` | UNKNOWN |

`WHERE`는 TRUE인 행만 남긴다. FALSE뿐 아니라 UNKNOWN도 제외한다.

```sql
-- 잘못된 NULL 비교
WHERE phone = NULL

-- 올바른 검사
WHERE phone IS NULL
WHERE phone IS NOT NULL
```

### AND·OR·NOT과 UNKNOWN

- `FALSE AND UNKNOWN`은 FALSE
- `TRUE AND UNKNOWN`은 UNKNOWN
- `TRUE OR UNKNOWN`은 TRUE
- `FALSE OR UNKNOWN`은 UNKNOWN
- `NOT UNKNOWN`은 UNKNOWN

조건을 변형할 때 일반 boolean 직관만 사용하면 행이 사라질 수 있다.

## 3. NOT IN과 NULL 함정

```sql
SELECT *
FROM members
WHERE member_id NOT IN (1, 2, NULL);
```

각 값이 `1도 아니고 2도 아니고 NULL도 아니다`를 판단하는 과정에서 UNKNOWN이 생겨 예상과 달리 아무 행도 반환하지 않을 수 있다. Subquery가 NULL을 반환할 가능성이 있으면 특히 위험하다.

안전한 선택:

- 업무상 NULL이 불가능하도록 `NOT NULL` 제약을 둔다.
- subquery에서 `WHERE key IS NOT NULL`로 제거한다.
- 상관 조건이 명확한 `NOT EXISTS`를 사용한다.

```sql
SELECT m.*
FROM members m
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_members b
    WHERE b.member_id = m.member_id
);
```

## 4. NULL을 고려한 비교

두 nullable column이 둘 다 NULL일 때 같다고 간주하려면 일반 `=`만으로는 부족하다.

```sql
-- PostgreSQL 및 표준 계열 표현
a IS NOT DISTINCT FROM b

-- MySQL의 NULL-safe equality
a <=> b
```

Oracle과 다른 DBMS에서는 지원 문법과 optimizer 처리가 다르므로 명시적인 NULL 조건 또는 제품별 기능을 확인한다.

`COALESCE(a, '대체값') = COALESCE(b, '대체값')`는 대체값이 실제 데이터에 존재하면 잘못 같은 것으로 판단할 수 있고 index 사용에도 영향을 줄 수 있다.

## 5. Aggregate와 NULL

```sql
COUNT(*)       -- 행 수
COUNT(column)  -- column이 NULL이 아닌 행 수
SUM(column)    -- NULL을 제외하고 합산
AVG(column)    -- NULL을 제외한 값의 평균
```

입력 행이 없거나 값이 모두 NULL일 때 aggregate 결과가 NULL일 수 있다. 화면에 0을 보여야 하는지는 업무 규칙으로 결정하고 `COALESCE`를 사용한다.

```sql
SELECT COALESCE(SUM(amount), 0)
FROM orders
WHERE member_id = :member_id;
```

## 6. UNIQUE와 NULL

UNIQUE constraint에서 여러 NULL을 허용하는지는 DBMS와 index 설정에 따라 차이가 있다. “이 column은 값이 없을 수 있지만, 값이 있다면 유일” 같은 규칙은 대상 DBMS에서 실제로 test한다.

복합 UNIQUE에서도 `(tenant_id, email)` 중 nullable column이 있으면 예상보다 중복이 허용될 수 있다. PostgreSQL의 NULL 처리 option, SQL Server의 filtered index, Oracle의 index 특성 등 제품별 구현을 설계 단계에서 확인한다.

## 7. NULL 정렬

`ORDER BY column ASC`에서 NULL이 처음인지 마지막인지는 DBMS 기본값이 다를 수 있다. 이식 가능한 결과가 중요하면 명시한다.

```sql
ORDER BY last_login_at DESC NULLS LAST
```

`NULLS FIRST/LAST` 직접 지원 여부가 다르면 `CASE WHEN column IS NULL ...` 방식 등을 사용하되 실행 계획을 확인한다. Pagination에서는 반드시 유일한 tie-breaker까지 둔다.

```sql
ORDER BY last_login_at DESC, member_id DESC
```

## 8. Charset과 Encoding

Charset은 어떤 문자를 어떤 byte로 표현할지 정의한다. UTF-8이라도 제품 설정과 역사적 이름이 다를 수 있다.

확인할 층:

```text
Application string encoding
→ Driver connection encoding
→ Database·Schema default
→ Table·Column charset
→ Import/Export file encoding
```

한 층이라도 다르면 글자 깨짐, 저장 실패, 잘못된 byte 길이 계산이 발생한다. MySQL에서는 `utf8`과 완전한 Unicode 범위를 다루는 설정의 차이를 특히 확인한다. 신규 설계는 대상 version의 권장 Unicode charset을 선택한다.

## 9. Collation

Collation은 문자열을 비교하고 정렬하는 규칙이다. Charset이 “저장 가능한 문자”라면 Collation은 “어떤 문자를 같다고 보고 어떤 순서로 놓는가”에 가깝다.

Collation에 따라 달라질 수 있는 것:

- 대문자와 소문자를 같은 값으로 보는가
- 악센트가 있는 문자를 같은 것으로 보는가
- 한글·숫자·기호 정렬 순서
- Unicode normalization 형태 처리
- UNIQUE constraint의 중복 판단
- `LIKE`, equality, index 사용

예를 들어 case-insensitive collation에서는 `Kim`과 `kim`이 UNIQUE 충돌을 낼 수 있지만 binary 계열 비교에서는 다를 수 있다.

### DBMS별 관점

- MySQL: server/database/table/column 단위 charset·collation 설정과 coercibility 규칙이 query 결과에 영향을 준다.
- PostgreSQL: database와 column/expression collation, libc/ICU provider 등 생성 환경을 확인한다. 대소문자 무시에는 `citext`, expression index, 적절한 collation 등 여러 선택이 있다.
- Oracle: database character set과 linguistic comparison/sort 설정, column collation 지원 범위를 version별로 확인한다.

Collation version이 운영체제나 ICU 변경으로 달라지면 기존 index 정렬 가정과 충돌할 수 있으므로 upgrade 후 index 상태와 재구성 필요성을 검토한다.

## 10. 문자열 길이와 공백

`CHAR(n)`은 고정 길이 의미와 trailing space 비교 규칙 때문에 DBMS별 차이가 생길 수 있다. 일반 이름·email에는 보통 가변 길이 type을 우선 검토한다.

길이 함수도 문자 수와 byte 수를 구분한다.

```text
'가' → 사용자 관점 문자 1개
UTF-8 저장 → 여러 byte
```

column 길이, API validation, index key 한도를 byte와 문자 중 무엇으로 계산하는지 확인한다.

## 11. 시간에서 먼저 구분할 것

```text
Instant       → 세계에서 하나로 특정되는 순간
Local datetime→ timezone 없는 달력 시각
Date          → 날짜만
Time          → 시각만
Timezone ID   → Asia/Seoul 같은 규칙 이름
UTC offset    → +09:00 같은 특정 시점의 차이
```

`2026-07-26 10:00`만으로는 세계의 한 순간을 특정하지 못한다. 서울 10시와 뉴욕 10시는 다른 순간이다.

## 12. UTC 저장 원칙을 정확히 이해하기

“무조건 UTC로 저장”은 instant에 적합한 기본 원칙이지만 모든 시간 데이터에 그대로 적용하면 안 된다.

- 결제 승인 시각·로그 발생 시각: instant이므로 UTC 기반 보존이 적합
- 생일: timezone과 무관한 date
- 매일 오전 9시 알림: 지역의 local time과 timezone ID가 필요
- 미래 항공 일정: 현지 시각과 지역 timezone 규칙을 함께 고려

Timezone ID는 offset과 다르다. `Asia/Seoul`은 규칙 이름이고 `+09:00`은 offset이다. 여러 국가는 일광절약시간 때문에 날짜에 따라 offset이 달라진다.

## 13. DBMS 시간 Type 차이

### PostgreSQL

- `timestamp without time zone`: timezone 없는 local datetime
- `timestamp with time zone` (`timestamptz`): 입력 순간을 내부적으로 정규화하고 session timezone에 맞춰 표시

`timestamptz`가 원래 입력한 `Asia/Seoul`이라는 timezone 이름까지 보존하는 것은 아니다. 원래 지역 규칙이 필요하면 별도 column에 timezone ID를 저장한다.

### MySQL

- `TIMESTAMP`: session timezone 변환, 값 범위와 자동 초기화 특성을 version·설정별 확인
- `DATETIME`: 달력 값을 저장하는 성격으로 timezone 자동 변환과 구분

이름만 PostgreSQL type과 대응시키면 안 된다.

### Oracle

- `DATE`: 이름과 달리 날짜와 시·분·초를 포함
- `TIMESTAMP`
- `TIMESTAMP WITH TIME ZONE`
- `TIMESTAMP WITH LOCAL TIME ZONE`

각 type이 입력 timezone 정보와 database/session timezone을 어떻게 처리하는지 test한다.

## 14. DST의 존재하지 않거나 두 번 오는 시간

일광절약시간 전환 지역에는 다음 문제가 있다.

- 시계를 앞으로 이동: 존재하지 않는 local time
- 시계를 뒤로 이동: 같은 local time이 두 번 등장

예약 시스템은 모호하거나 존재하지 않는 시간을 거부할지, 앞/뒤 offset 중 무엇을 택할지 정책이 필요하다. timezone library와 tzdata version도 운영 환경 전체에서 관리한다.

## 15. 범위 Query의 안전한 형태

하루 데이터를 찾을 때 column을 함수로 감싸기보다 반열린 구간을 사용하면 index와 경계 처리에 유리하다.

```sql
WHERE created_at >= :start_instant
  AND created_at <  :next_start_instant
```

`23:59:59.999`를 끝으로 잡으면 type 정밀도가 달라졌을 때 누락될 수 있다. 사용자 지역의 하루 시작을 정확한 timezone 규칙으로 instant로 변환한 뒤 조회한다.

## 16. Application·DB·JSON 경계

- application의 datetime type이 timezone 정보를 보존하는가?
- driver가 어떤 session timezone으로 변환하는가?
- DB session timezone이 connection pool 재사용 후에도 올바른가?
- JSON에 `Z`, offset을 포함하는가?
- 날짜만 필요한 값에 timestamp를 쓰고 있지 않은가?
- 로그의 timestamp와 업무 timestamp를 구분하는가?

ISO 8601 문자열도 offset이 없는 `2026-07-26T10:00:00`과 `2026-07-26T10:00:00+09:00`은 의미가 다르다.

## 17. Migration 검증 Query

DBMS 전환 전후에 대표 경계값을 별도 dataset으로 비교한다.

- NULL·빈 문자열·공백
- 대문자·소문자·한글·emoji·조합형 문자
- 문자열 최대 길이와 multibyte
- leap day
- DST 시작·종료 시각
- timestamp 최대·최소 범위
- 소수 초 정밀도
- NULL 정렬과 UNIQUE
- `NOT IN`, `NOT EXISTS`, aggregate 결과

행 수만 비교하지 말고 key별 값, 정렬 결과, hash, 업무 aggregate도 비교한다.

## 18. 최종 점검표

- nullable column이 정말 “알 수 없음/없음”을 표현하는가?
- `= NULL`, `<> NULL`을 사용하지 않았는가?
- `NOT IN` subquery의 NULL 가능성을 확인했는가?
- `COUNT(*)`와 `COUNT(column)`을 구분했는가?
- UNIQUE와 NULL 동작을 대상 DBMS에서 test했는가?
- 정렬에서 NULL 위치와 tie-breaker를 명시했는가?
- charset·collation을 환경마다 기록했는가?
- 업무 값이 instant, local datetime, date 중 무엇인지 정의했는가?
- timezone ID와 UTC offset을 구분했는가?
- DB·driver·application·JSON 변환을 왕복 test했는가?
