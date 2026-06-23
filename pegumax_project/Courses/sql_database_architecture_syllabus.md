# SQL & Database Architecture for Builders

*A principal engineer's course on designing relational databases that stay fast, correct, and maintainable as they grow. Model your data right, query it efficiently, and evolve it safely.*

---

## Module 1: Relational Foundations & SQL Basics
**Build the core mental model of relational data so every query and design decision afterward has solid footing.**

- Tables, rows, columns, keys, and the relational model in plain terms
- The query essentials: `SELECT`, `WHERE`, `ORDER BY`, and `LIMIT`
- Data types, `NULL` semantics, and choosing the right type for each column

---

## Module 2: Designing Relational Schemas
**Translate real-world requirements into a clean table structure that captures relationships accurately.**

- Entity-relationship modeling: entities, attributes, and relationships
- Primary keys, foreign keys, and enforcing referential integrity
- One-to-one, one-to-many, and many-to-many relationships via join tables

---

## Module 3: Normalization Rules
**Eliminate redundancy and update anomalies by structuring data according to proven normal forms.**

- First, second, and third normal form explained with concrete examples
- Spotting and fixing anomalies: insertion, update, and deletion problems
- When to denormalize deliberately for read performance—and the tradeoffs

---

## Module 4: Querying Data with Joins
**Combine data across tables fluently so you can answer real questions spanning your whole schema.**

- Inner, left, right, and full joins—and exactly when each applies
- Multi-table joins, self-joins, and aliasing for readable queries
- Set operations (`UNION`, `INTERSECT`, `EXCEPT`) and combining result sets

---

## Module 5: Aggregation & Analytical Queries
**Summarize and analyze data directly in SQL so you extract insight without exporting to other tools.**

- Aggregate functions with `GROUP BY` and filtering groups with `HAVING`
- Window functions for running totals, rankings, and per-partition analytics
- Conditional aggregation and `CASE` expressions for shaped reporting

---

## Module 6: Nested Queries & CTEs
**Compose complex logic from simpler queries so even hard questions stay readable and correct.**

- Subqueries in `SELECT`, `FROM`, and `WHERE`, including correlated subqueries
- Common Table Expressions (CTEs) for clarity and breaking down complex logic
- Recursive CTEs for hierarchical and graph-like data

---

## Module 7: Indexing for Performance
**Make slow queries fast by understanding exactly how indexes work and when to use them.**

- How B-tree indexes work and what they cost on writes and storage
- Single-column, composite, covering, and partial indexes—and choosing the right one
- Reading `EXPLAIN`/`EXPLAIN ANALYZE` to diagnose scans and verify index usage

---

## Module 8: Transactions & Data Integrity
**Guarantee your data stays correct under concurrent access so failures never leave it half-written.**

- ACID properties and wrapping multi-step operations in transactions
- Isolation levels and the anomalies they prevent (dirty/phantom reads, lost updates)
- Constraints (`CHECK`, `UNIQUE`, `NOT NULL`) and locking basics for concurrency

---

## Module 9: Data Migration Workflows
**Evolve a live schema safely so you can ship changes without downtime or data loss.**

- Version-controlled, repeatable migrations and rollback strategies
- Zero-downtime patterns: expand/contract, backfills, and additive-first changes
- ETL and bulk data loading, transformation, and validation between systems

---

## Module 10: Scaling, Security & Operations
**Operate a production database with the performance, safety, and resilience real systems demand.**

- Scaling reads with replicas, connection pooling, caching, and partitioning/sharding basics
- Security: least-privilege roles, parameterized queries, and preventing SQL injection
- Backups, point-in-time recovery, and monitoring slow queries in production

---
