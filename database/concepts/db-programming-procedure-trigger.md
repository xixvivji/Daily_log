# Procedure·Function·Trigger

[← PPT 순차 학습 가이드로 돌아가기](../00-ppt-sequential-study-guide.md)

## DB Programming이란?

SQL statement 하나를 실행하는 것을 넘어 DB 안에 reusable logic을 정의하는 기능이다.

```text
Procedure
→ 작업 절차 실행

Function
→ 값을 계산해 반환

Trigger
→ 특정 DB event에 자동 실행

Event·Scheduler
→ 정해진 시간에 실행
```

제품마다 기능 경계와 문법이 다르다.

## Procedure와 Function의 일반적인 차이

| 구분 | Procedure | Function |
| --- | --- | --- |
| 주 목적 | 여러 작업과 side effect | 값을 계산해 반환 |
| 호출 | `CALL`·PL/SQL block 등 | SQL expression 또는 전용 호출 |
| 반환 | OUT parameter·result set | return value·table |
| Transaction 제어 | DBMS별 허용 범위 다름 | 일반적으로 더 제한적 |
| SELECT 내부 사용 | 보통 직접 사용하지 않음 | 가능할 수 있음 |

DBMS별로 예외가 있으므로 이름만으로 동작을 단정하지 않는다.

## MySQL Procedure

```sql
DELIMITER //

CREATE PROCEDURE transfer_money(
    IN p_from_id BIGINT,
    IN p_to_id BIGINT,
    IN p_amount DECIMAL(12, 2)
)
BEGIN
    UPDATE accounts
    SET balance = balance - p_amount
    WHERE id = p_from_id
      AND balance >= p_amount;

    IF ROW_COUNT() <> 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'insufficient balance';
    END IF;

    UPDATE accounts
    SET balance = balance + p_amount
    WHERE id = p_to_id;
END//

DELIMITER ;
```

호출:

```sql
CALL transfer_money(1, 2, 10000);
```

실제 transaction 경계, 오류 handler, 대상 계좌 존재 확인을 추가해야 한다.

## PostgreSQL Procedure

```sql
CREATE OR REPLACE PROCEDURE transfer_money(
    p_from_id BIGINT,
    p_to_id BIGINT,
    p_amount NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE accounts
    SET balance = balance - p_amount
    WHERE id = p_from_id
      AND balance >= p_amount;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'insufficient balance';
    END IF;

    UPDATE accounts
    SET balance = balance + p_amount
    WHERE id = p_to_id;
END;
$$;
```

호출:

```sql
CALL transfer_money(1, 2, 10000);
```

Procedure 내부 transaction control 허용은 호출 context와 version을 확인한다.

## Oracle Procedure

```sql
CREATE OR REPLACE PROCEDURE transfer_money(
    p_from_id IN NUMBER,
    p_to_id IN NUMBER,
    p_amount IN NUMBER
) AS
BEGIN
    UPDATE accounts
    SET balance = balance - p_amount
    WHERE id = p_from_id
      AND balance >= p_amount;

    IF SQL%ROWCOUNT <> 1 THEN
        RAISE_APPLICATION_ERROR(-20001, 'insufficient balance');
    END IF;

    UPDATE accounts
    SET balance = balance + p_amount
    WHERE id = p_to_id;
END;
/
```

호출:

```sql
BEGIN
    transfer_money(1, 2, 10000);
END;
/
```

Oracle에서는 관련 Procedure·Function·Type을 Package로 묶는 설계도 중요하다.

## Function 예제

세금 포함 금액 계산:

### MySQL

```sql
CREATE FUNCTION price_with_tax(
    p_price DECIMAL(12, 2),
    p_rate DECIMAL(5, 4)
)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
RETURN ROUND(p_price * (1 + p_rate), 2);
```

### PostgreSQL

```sql
CREATE FUNCTION price_with_tax(
    p_price NUMERIC,
    p_rate NUMERIC
)
RETURNS NUMERIC
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT ROUND(p_price * (1 + p_rate), 2);
$$;
```

### Oracle

```sql
CREATE OR REPLACE FUNCTION price_with_tax(
    p_price IN NUMBER,
    p_rate IN NUMBER
) RETURN NUMBER DETERMINISTIC AS
BEGIN
    RETURN ROUND(p_price * (1 + p_rate), 2);
END;
/
```

## DETERMINISTIC과 Volatility

### Deterministic

같은 입력에 같은 결과를 반환한다는 선언이다.

```text
price_with_tax(100, 0.1)
→ 항상 110
```

현재 시각, random, table 조회, session 설정에 따라 결과가 달라지면 deterministic으로 표시하면 안 된다.

### PostgreSQL

- `IMMUTABLE`: 같은 입력이면 영구적으로 같은 결과
- `STABLE`: 한 statement 안에서는 같은 결과로 볼 수 있음
- `VOLATILE`: 호출마다 달라질 수 있음

잘못된 volatility 선언은 optimizer가 값을 미리 계산하거나 index expression에 사용하면서 잘못된 결과를 만들 수 있다.

## Trigger

Table의 INSERT·UPDATE·DELETE 같은 event에 자동 실행되는 logic이다.

사용할 수 있는 경우:

- 짧은 감사 정보
- 변경 경로와 무관하게 반드시 적용할 단순 규칙
- 단순 derived column

주의할 경우:

- 외부 API 호출
- 복잡하고 자주 변경되는 business flow
- 긴 batch
- 여러 trigger의 숨은 연쇄

## PostgreSQL Audit Trigger

```sql
CREATE TABLE member_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id BIGINT NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE FUNCTION log_member_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO member_audit(
            member_id, old_status, new_status
        )
        VALUES (
            NEW.id, OLD.status, NEW.status
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_member_status_audit
AFTER UPDATE OF status ON members
FOR EACH ROW
EXECUTE FUNCTION log_member_status_change();
```

## MySQL Trigger

```sql
DELIMITER //

CREATE TRIGGER trg_member_status_audit
AFTER UPDATE ON members
FOR EACH ROW
BEGIN
    IF NOT (OLD.status <=> NEW.status) THEN
        INSERT INTO member_audit(
            member_id, old_status, new_status, changed_at
        )
        VALUES (
            NEW.id, OLD.status, NEW.status, CURRENT_TIMESTAMP
        );
    END IF;
END//

DELIMITER ;
```

MySQL의 NULL-safe equality `<=>` 등을 이해해야 한다.

## Oracle Trigger

```sql
CREATE OR REPLACE TRIGGER trg_member_status_audit
AFTER UPDATE OF status ON members
FOR EACH ROW
WHEN (OLD.status <> NEW.status)
BEGIN
    INSERT INTO member_audit(
        audit_id,
        member_id,
        old_status,
        new_status,
        changed_at
    )
    VALUES (
        member_audit_seq.NEXTVAL,
        :NEW.id,
        :OLD.status,
        :NEW.status,
        SYSTIMESTAMP
    );
END;
/
```

NULL 비교와 version별 identity 전략을 별도로 검토한다.

## BEFORE와 AFTER

```text
BEFORE
→ 저장 전 값 검증·변환

AFTER
→ 저장 완료 후 audit·후속 DB 작업

INSTEAD OF
→ View 등에 대한 작업을 다른 logic으로 대체
```

DBMS별 지원 event와 row·statement trigger 차이가 있다.

## Row Trigger와 Statement Trigger

```text
FOR EACH ROW
→ 영향받은 row마다 실행

Statement Level
→ SQL statement당 한 번 실행
```

백만 row UPDATE에 row trigger가 있으면 백만 번 실행될 수 있다. Bulk DML 성능을 반드시 측정한다.

## Trigger Recursion과 실행 순서

Trigger가 다른 table을 변경하고 그 table trigger가 다시 원래 table을 변경하면 recursion과 deadlock 위험이 있다.

```text
Trigger A
→ Table B UPDATE
→ Trigger B
→ Table A UPDATE
→ Trigger A 반복
```

제품별 recursion 제한, 실행 순서 지정, nested trigger 설정을 확인한다.

## Trigger와 CDC

Trigger 기반 audit와 transaction log 기반 CDC는 다르다.

```text
Trigger
→ DB transaction 안에서 직접 table에 기록

Log-based CDC
→ WAL·Binary Log·Redo에서 변경 추출
```

대량 event integration에는 Debezium 같은 log-based CDC가 source transaction 부담과 schema evolution 측면에서 더 적합할 수 있다.

## pg_notify

PostgreSQL의 `NOTIFY`는 listener에게 작은 notification을 보낸다.

```sql
NOTIFY order_changed, '12345';
```

durable message queue가 아니다.

- Listener가 없으면 영구 보관을 기대하지 않음
- Payload 크기 제한
- 재처리·offset·long retention 없음

Kafka나 outbox를 대체하는 것으로 보면 안 된다.

## MySQL Event Scheduler

```sql
CREATE EVENT purge_expired_sessions
ON SCHEDULE EVERY 1 DAY
DO
    DELETE FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
```

PostgreSQL은 pg_cron extension이나 외부 scheduler, Oracle은 DBMS_SCHEDULER 등을 사용할 수 있다.

## Application과 DB의 역할

DB에 적합:

- Set-based JOIN·Aggregate
- Constraint
- Transaction 가까이에서 수행해야 하는 짧은 logic

Application에 적합:

- 외부 API
- 복잡한 workflow
- 자주 변경되는 domain logic
- Service 간 orchestration

Code line이 줄었다는 이유만으로 Procedure가 좋은 설계가 되는 것은 아니다.

## DBMS 전환 Check

```text
MySQL DELIMITER
→ 다른 DBMS에 없음

Error 처리
→ SIGNAL, RAISE, RAISE_APPLICATION_ERROR

Return 형식
→ Scalar·Table·OUT Parameter 차이

Volatility
→ DETERMINISTIC·IMMUTABLE 의미 차이

Trigger
→ OLD·NEW 표기, Row·Statement, 실행 순서

Scheduler
→ Event Scheduler·pg_cron·DBMS_SCHEDULER

Package
→ Oracle Package의 직접 대응 기능 검토
```

Routine과 Trigger는 migration 자동 변환 실패가 많은 영역이므로 별도 inventory와 integration test가 필요하다.

