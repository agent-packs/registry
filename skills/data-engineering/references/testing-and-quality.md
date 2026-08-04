# Testing and data-quality patterns (Python and DuckDB)

Proving a transformation is correct, and expressing invariants as checks that fail closed.

Related: [ingestion.md](ingestion.md), [incremental-and-publication.md](incremental-and-publication.md), [performance.md](performance.md).

## Transformation boundaries

Keep SQL independently readable and testable. Store substantial queries in `.sql` files when that matches repository conventions. Keep orchestration functions small:

```python
from __future__ import annotations

from pathlib import Path

import duckdb


def transform(connection: duckdb.DuckDBPyConnection, sql_path: Path) -> None:
    statement = sql_path.read_text(encoding="utf-8")
    connection.execute(statement)
```

Do not perform unrestricted template substitution on SQL. Use parameters for values and an allowlist for unavoidable identifiers.

Avoid converting a relation to pandas merely to apply filters or aggregations. Materialize into Python only when data size is bounded and Python-specific logic is justified.

## Testing transformations

Create tiny fixtures that make grain and edge cases obvious. Assert exact rows with an explicit order only at the test boundary:

```python
from decimal import Decimal

import duckdb


def test_customer_revenue_does_not_multiply_orders() -> None:
    with duckdb.connect() as connection:
        connection.execute("""
            CREATE TABLE orders(order_id INTEGER, customer_id INTEGER, amount DECIMAL(9,2));
            INSERT INTO orders VALUES (1, 10, 12.50), (2, 10, 7.50);

            CREATE TABLE customer_tags(customer_id INTEGER, tag VARCHAR);
            INSERT INTO customer_tags VALUES (10, 'new'), (10, 'priority');
        """)

        actual = connection.execute("""
            WITH revenue AS (
                SELECT customer_id, SUM(amount) AS revenue
                FROM orders
                GROUP BY customer_id
            )
            SELECT r.customer_id, r.revenue
            FROM revenue AS r
            WHERE EXISTS (
                SELECT 1 FROM customer_tags AS t
                WHERE t.customer_id = r.customer_id
            )
            ORDER BY r.customer_id
        """).fetchall()

    assert actual == [(10, Decimal("20.00"))]
```

The fixture above exists to catch join amplification: two tags on one customer must not double the revenue. `EXISTS` rather than a join is the fix being asserted.

For floating-point values, use an explicit tolerance. Prefer decimal types for contractual financial values. Normalize engine-specific Python values before comparison only when normalization is part of the intended contract.

Useful test categories:

- Exact fixture-to-output tests for SQL and Python transforms
- Property tests for invariants over generated inputs
- Serialization tests that write and reread CSV, JSON, or Parquet
- Schema compatibility tests
- Rerun and recovery tests using a temporary directory or database

Confirm a new test fails for the expected reason before implementing the behavior.

## Data-quality checks

Express exhaustive invariants as queries that return violations. Each must return zero rows:

```sql
-- Key uniqueness.
SELECT order_id, count(*) AS occurrences
FROM curated_orders
GROUP BY order_id
HAVING count(*) <> 1;
```

```sql
-- Nullability and accepted ranges.
SELECT order_id
FROM curated_orders
WHERE customer_id IS NULL OR amount < 0;
```

```sql
-- Referential integrity, unless orphan handling is explicitly allowed.
SELECT DISTINCT f.customer_id
FROM fact_orders AS f
LEFT JOIN dim_customer AS d USING (customer_id)
WHERE d.customer_id IS NULL;
```

Fail closed on contractual violations. A check that returns rows must stop the run — see the assertion helper below, and note that a bare `SELECT` inside a transaction aborts nothing on its own.

For monitoring thresholds, report the numerator, denominator, threshold, and evaluation window.

Check output schemas through engine metadata instead of inferring them from Python values. In DuckDB, inspect `DESCRIBE SELECT ...` or `information_schema.columns`.

## Turning checks into assertions

A validation query is only a guard if something reads its result and raises:

```python
from __future__ import annotations

from pathlib import Path

import duckdb


def assert_parquet_contract(
    connection: duckdb.DuckDBPyConnection,
    source_path: str | Path,
    *,
    min_rows: int | None = None,
) -> None:
    """Raise unless a Parquet file or glob satisfies the orders contract."""
    if min_rows is not None and min_rows < 0:
        raise ValueError("min_rows must be non-negative or None")

    row_count, null_keys, duplicate_keys, negative_amounts = connection.execute(
        """
        SELECT
            count(*)                                        AS row_count,
            count(*) FILTER (WHERE order_id IS NULL)        AS null_keys,
            count(order_id) - count(DISTINCT order_id)      AS duplicate_keys,
            count(*) FILTER (WHERE amount < 0)              AS negative_amounts
        FROM read_parquet($source_path)
        """,
        {"source_path": str(source_path)},
    ).fetchone()

    problems = {
        "below minimum rows": min_rows is not None and row_count < min_rows,
        "null keys": null_keys,
        "duplicate keys": duplicate_keys,
        "negative amounts": negative_amounts,
    }
    failed = {name: value for name, value in problems.items() if value}
    if failed:
        raise ValueError(f"{source_path} failed contract: {failed}")
```

Count duplicates with `count(order_id) - count(DISTINCT order_id)`, not `count(*) - count(DISTINCT order_id)`. `count(DISTINCT ...)` ignores nulls while `count(*)` does not, so the `count(*)` form reports every null key as a duplicate as well — three null keys and no actual duplicates yields a duplicate count of three. Nulls are already reported by their own check; counting them twice obscures which invariant actually broke.

Empty output is valid for many contracts, including an incremental interval with no arrivals. Require rows only when the contract does by passing `min_rows`; do not hard-code non-emptiness into a reusable assertion.

Do not accept a free-form SQL `relation` and interpolate it into the assertion query. File paths routinely contain quotes and other SQL syntax, and an allowlist mentioned only in a comment is not enforcement. Bind paths as above. For tables, accept only identifiers matched against an explicit code-level allowlist and quote them with an engine-provided identifier API; for other sources, write a constant query with bound values.
