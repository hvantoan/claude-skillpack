---
name: database-design
description: Use when designing, reviewing, or normalizing relational database schemas. Covers normalization (1NF-3NF-BCNF), integrity constraints, many-to-many mapping, self-referencing trees, ACID, indexing, and schema evolution.
when_to_use: User asks to design a DB schema, normalize tables, model relationships (1-to-many, many-to-many, hierarchy/tree), add integrity constraints, review an existing schema for correctness, or decide between normalization and denormalization.
user-invocable: true
license: MIT
category: database
keywords:
  - database
  - schema
  - normalization
  - 1nf
  - 2nf
  - 3nf
  - bcnf
  - foreign key
  - many-to-many
  - erd
related:
  - postgres-pro
  - microservices-architect
  - dotnet-vsa
metadata:
  author: https://github.com/hvantoan
  version: "1.0.0"
  domain: database
  role: specialist
  scope: design
  output-format: sql
---

# Database Design

Senior database designer. Produces normalized, correct schemas with integrity enforced at the DB layer, not just the UI/application.

## When to Use This Skill

- Designing a relational schema from scratch (OLTP).
- Normalizing existing tables or fixing redundancy/anomalies.
- Modeling relationships: one-to-one, one-to-many, many-to-many, self-referencing hierarchy.
- Adding integrity constraints (PK, FK, UNIQUE, CHECK, partial unique index).
- Deciding when to denormalize (reporting/OLAP).
- Reviewing a schema for correctness and completeness.

## Core Principles

### 1. Normalization (do this first — up to 3NF by default)

| Normal form | Rule |
|---|---|
| **1NF** | Every cell holds ONE atomic value; no lists/arrays/repeated groups. |
| **2NF** | No partial dependency on part of a composite key (only relevant with composite PK). |
| **3NF** | No transitive dependency — non-key columns depend only on the full key. |
| **BCNF** | Every determinant is a candidate key. |

**Default target: 3NF.** Deeper normalization causes more JOINs; denormalize deliberately later for read performance (never normalize into the red).

### 2. Integrity Constraints — enforce at DB, not just UI

- **Entity integrity:** every table has a non-null unique primary key.
- **Referential integrity:** foreign keys must point to existing rows; pick `ON DELETE CASCADE / SET NULL / RESTRICT` deliberately per relationship.
- **Domain integrity:** `NOT NULL`, `UNIQUE`, `CHECK`, ENUM for valid values.
- **Business rules** live in constraints/triggers (single source of truth), never only in the frontend.

### 3. Relationship Patterns

**One-to-many** → `child.parent_id BIGINT REFERENCES parent(id)` + index on the FK column.

**Many-to-many** → association (join) table with composite PK of both FKs.

**"1 main + n sub"** (e.g. one main group + many sub groups) → many-to-many mapping table with an `is_main` boolean, plus a **partial unique index** to enforce exactly one main:

```sql
CREATE TABLE customer_group_mapping (
    customer_id BIGINT NOT NULL REFERENCES customer(id),
    group_id    BIGINT NOT NULL REFERENCES customer_group(id),
    is_main     BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (customer_id, group_id)
);

-- Enforce: exactly ONE main group per customer
CREATE UNIQUE INDEX uq_customer_one_main
ON customer_group_mapping(customer_id)
WHERE is_main = true;
```

**Self-referencing hierarchy (tree)** → `parent_id BIGINT REFERENCES table(id)` (NULL = root). Use `parent_id IS NULL` to identify roots instead of a redundant `is_root` flag. For deep/recursive trees queried often, add a closure table or `path`/`level` columns — that is deliberate denormalization, add only when needed.

### 4. Keys

- Prefer **surrogate keys** (`BIGSERIAL`/UUID) as PK; add `UNIQUE` on natural keys (email, code).
- **Single source of truth** — never store the same fact in two places.

### 5. Transactions & Concurrency (ACID)

- Wrap multi-step writes in **transactions**.
- Choose isolation level per problem (Read Committed default vs Serializable).
- Optimistic locking (version/timestamp) or pessimistic (`SELECT ... FOR UPDATE`) for concurrent updates.

### 6. Physical Design & Performance

- **Index** columns used in WHERE/JOIN/ORDER BY; always index FK columns. Don't over-index (write + storage cost).
- **Denormalize deliberately** for OLAP/reporting (star schema) — not before it's needed.
- Separate OLTP (normalized) from OLAP (dimensional).

### 7. Audit & History

- Always add `created_at`, `updated_at`, `created_by`.
- Temporal/history tables for mutable facts that need traceability (prices, order status).

### 8. Security

- Hash passwords (bcrypt/argon2), never plaintext.
- RBAC at DB layer (roles/grants), not just hidden UI.
- Row-level security (PostgreSQL RLS) for multi-tenant.

### 9. Evolution

- Versioned **migrations** (EF Core Migrations / Flyway / Liquibase).
- Backward-compatible changes: add columns rather than rename/change type that breaks consumers.

## Workflow

1. **Clarify the domain** — entity list and relationship arity/cardinality before drawing anything.
2. **Normalize to 3NF** — tables, PKs, FKs, remove redundancy.
3. **Model relationships** — 1:N, M:N (join table), trees (self-ref).
4. **Add constraints** — PK/FK/UNIQUE/CHECK, partial unique for "one main" rules.
5. **Add audit columns + indexes.**
6. **Output SQL** or ORM (EF Core) mapping; verify joins and constraint enforcement.

## Pitfalls

- **UI-only rules:** "1 main group" enforced only in the frontend lets bad data in via API/tools. Enforce with a partial unique index.
- **Composite key partial dependency** missed in 2NF — check every non-key column depends on the WHOLE key.
- **Redundant `is_root`/`is_main` flags** duplicating what `parent_id IS NULL` / partial index already express.
- **Over-normalization** → excessive JOINs for read-heavy workloads; stop at 3NF and denormalize deliberately.
- **Missing FK indexes** → N+1 and slow cascades.
- **`SELECT *`** in production.
- **No migrations from day one** → painful schema changes later.

## Verification

- Confirm each table has a PK; every non-key column depends on the full key (3NF).
- Confirm every FK column is indexed.
- Confirm "exactly one X" business rules are DB-enforced (partial unique index), not app-enforced.
- For trees, confirm root detection (`parent_id IS NULL`) and recursive query strategy.
