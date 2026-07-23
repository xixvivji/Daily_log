# MySQL과 PostgreSQL의 Schema 차이

[← 핵심 용어 문서로 돌아가기](../01-database-course-map-and-glossary.md)

## MySQL

MySQL은 database와 schema를 사실상 같은 대상으로 취급한다.

```sql
-- 두 명령은 같은 종류의 namespace를 만든다.
CREATE DATABASE shop;
CREATE SCHEMA campus;

SELECT * FROM shop.orders;
SELECT * FROM campus.students;
```

```text
MySQL Server
├── shop Database(Schema)
│   └── orders
└── campus Database(Schema)
    └── students
```

## PostgreSQL

PostgreSQL에서는 database와 schema가 서로 다른 계층이다. 먼저 특정 database에 접속한 다음, 그 database 내부에 여러 schema를 만들 수 있다.

```sql
-- shop database에 접속한 상태
CREATE SCHEMA sales;
CREATE SCHEMA inventory;

CREATE TABLE sales.products (
    id BIGINT PRIMARY KEY
);

CREATE TABLE inventory.products (
    id BIGINT PRIMARY KEY
);
```

```text
PostgreSQL Server
└── shop Database
    ├── public Schema
    │   └── customers
    ├── sales Schema
    │   └── products
    └── inventory Schema
        └── products
```

## 차이 비교

| 구분 | MySQL | PostgreSQL |
| --- | --- | --- |
| Database와 schema | 사실상 같은 개념 | 서로 다른 계층 |
| `CREATE SCHEMA sales` | `sales` database 생성 | 현재 database 내부에 `sales` schema 생성 |
| 일반적인 객체 이름 | `database.table` | `schema.table` |
| 한 database 내부의 여러 schema | 별도 schema 계층 없음 | 지원 |

```text
MySQL:      Server → Database(Schema) → Table
PostgreSQL: Server → Database → Schema → Table
```

