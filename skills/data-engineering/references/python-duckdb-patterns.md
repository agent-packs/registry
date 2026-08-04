# Python and DuckDB patterns

Use these patterns when a project does not already provide a preferred implementation. Adapt names and types to the dataset contract; do not copy examples without validating the actual schema.

## Contents

1. Environment discovery
2. Connection lifecycle
3. Reading files
4. Transformation boundaries
5. Testing transformations
6. Data-quality checks
7. Incremental processing
8. Reconciliation
9. Performance and portability

## Environment discovery

Before adding dependencies, check the repository's `pyproject.toml`, lockfiles, requirements files, task runner, and existing imports. Verify availability with a non-mutating command such as:

```bash
python -c "import duckdb; print(duckdb.__version__)"
```

Use the project's Python runner (`uv run`, `poetry run`, or similar) when configured. Match its formatting and test commands.

## Connection lifecycle

Use a context manager and parameterize values:

```python
from pathlib import Path
import duckdb


def build_orders(source: Path, destination: Path, cutoff: str) -> None:
    with duckdb.connect() as connection:
        connection.execute("SET TimeZone = 'UTC'")
        connection.execute(
            """
            COPY (
                SELECT
                    CAST(order_id AS VARCHAR) AS order_id,
                    CAST(customer_id AS VARCHAR) AS customer_id,
                    CAST(amount AS DECIMAL(18, 2)) AS amount,
                    CAST(ordered_at AS TIMESTAMPTZ) AS ordered_at
                FROM read_parquet($source_path)
                WHERE ordered_at >= CAST($cutoff AS TIMESTAMPTZ)
            ) TO $destination_path (FORMAT PARQUET)
            """,
            {
                "source_path": str(source),
                "cutoff": cutoff,
                "destination_path": str(destination),
            },
        )
```

Bind scalar values and file paths. Prefer named parameters when a statement contains parameters in both a query and an enclosing command such as `COPY`, because anonymous parameter ordering can be non-obvious. SQL identifiers such as table or column names generally cannot be bound as parameters; validate them against an explicit allowlist before quoting or interpolating them.

Set the session timezone explicitly whenever timestamp behavior matters. `TIMESTAMPTZ` represents an instant, but DuckDB renders and performs some calendar operations using the configured session timezone. Use an in-memory connection for isolated tests. Use an explicit database file only when persistence is part of the behavior under test.

## Reading files

DuckDB can query files without first loading them into Python:

```sql
SELECT customer_id, SUM(amount) AS revenue
FROM read_parquet('data/orders/*.parquet', union_by_name = true)
WHERE ordered_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
GROUP BY customer_id;
```

Prefer explicit CSV settings for stable ingestion:

```sql
SELECT *
FROM read_csv(
    'data/orders.csv',
    header = true,
    columns = {
        'order_id': 'VARCHAR',
        'customer_id': 'VARCHAR',
        'amount': 'DECIMAL(18,2)',
        'ordered_at': 'TIMESTAMPTZ'
    },
    nullstr = ['NULL', '']
);
```

Use automatic type inference for exploration, not as an unstated production contract. Validate a multi-file schema before relying on `union_by_name` because it can hide unexpected evolution.

To quarantine malformed CSV rows instead of failing or silently dropping them, use the built-in rejects tables. Each rejected row is stored with the failing line, column, and error reason, satisfying the quarantine-with-reason requirement without hand-rolled filtering:

```sql
SELECT * FROM read_csv('data/orders.csv', header = true, store_rejects = true);
SELECT * FROM reject_errors;  -- one row per rejected value, with line number and reason
```

Report the rejects count alongside the loaded count so the loss is visible.

For JSON, specify the expected structure and distinguish newline-delimited JSON from a JSON array. Reject or quarantine records that cannot meet the contract.

For deterministic exploration samples, use reservoir sampling with a fixed seed rather than `LIMIT` (which depends on scan order):

```sql
SELECT * FROM read_parquet('data/orders/*.parquet')
USING SAMPLE reservoir(1000 ROWS) REPEATABLE (42);
```

## Transformation boundaries

Keep SQL independently readable and testable. Store substantial queries in `.sql` files when that matches repository conventions. Keep orchestration functions small:

```python
from pathlib import Path
from decimal import Decimal

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

For floating-point values, use an explicit tolerance. Prefer decimal types for contractual financial values. Normalize engine-specific Python values before comparison only when normalization is part of the intended contract.

Useful test categories:

- Exact fixture-to-output tests for SQL and Python transforms
- Property tests for invariants over generated inputs
- Serialization tests that write and reread CSV, JSON, or Parquet
- Schema compatibility tests
- Rerun and recovery tests using a temporary directory or database

Confirm a new test fails for the expected reason before implementing the behavior.

## Data-quality checks

Express exhaustive invariants as queries that return violations:

```sql
-- Must return zero rows.
SELECT order_id, COUNT(*) AS occurrences
FROM curated_orders
GROUP BY order_id
HAVING COUNT(*) <> 1;
```

```sql
-- Must return zero rows.
SELECT customer_id
FROM curated_orders
WHERE customer_id IS NULL OR amount < 0;
```

```sql
-- Must return zero rows unless orphan handling is explicitly allowed.
SELECT DISTINCT f.customer_id
FROM fact_orders AS f
LEFT JOIN dim_customer AS d USING (customer_id)
WHERE d.customer_id IS NULL;
```

Fail closed on contractual violations. For monitoring thresholds, report the numerator, denominator, threshold, and evaluation window.

Check output schemas through engine metadata instead of inferring them from Python values. In DuckDB, inspect `DESCRIBE SELECT ...` or `information_schema.columns`.

## Incremental processing

Define three concepts separately:

- **Event time:** when the business event occurred.
- **Ingestion time:** when the system observed it.
- **Processing watermark:** the boundary recorded by the job.

Use half-open intervals such as `[start, end)` to prevent gaps and overlaps. Store boundaries in a single normalized timezone, normally UTC.

Do not assume a timestamp watermark handles corrections or deletions. Choose a strategy that matches the source:

- Immutable append-only events: watermark plus stable event ID deduplication.
- Mutable records: change-data capture, version column, or overlapping lookback with merge.
- Source deletions: tombstones, snapshots plus diff, or an authoritative full-key reconciliation.

Test at minimum:

1. Initial load
2. Identical rerun
3. New records exactly on both interval boundaries
4. Late record inside the supported lookback
5. Correction of an existing key
6. Failure before publication followed by retry
7. Backfill overlapping already-published data

Prefer staging plus transactional merge or atomic file/directory replacement. Never delete the existing result before the replacement is known to be valid.

## Reconciliation

Compare sources and targets at the same business grain and filter window. Record more than row counts:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT order_id) AS distinct_orders,
    SUM(amount) AS total_amount,
    MIN(ordered_at) AS first_ordered_at,
    MAX(ordered_at) AS last_ordered_at
FROM curated_orders
WHERE ordered_at >= $start_time
  AND ordered_at < $end_time;
```

Account explicitly for filtered, deduplicated, rejected, corrected, and deleted records. A useful conservation equation is:

```text
input = published + rejected + intentionally_filtered + superseded
```

If measures change grain, reconcile using the transformation's business rule rather than expecting identical row counts.

## Performance and portability

- On memory-constrained machines, bound DuckDB explicitly: `SET memory_limit = '4GB'; SET threads = 4;`. Give it a spill location with `SET temp_directory = '...'` so large sorts and joins spill to disk instead of failing.
- Select only required columns and filter as early as semantics permit.
- Use `EXPLAIN` or `EXPLAIN ANALYZE` on representative data before guessing at bottlenecks.
- Avoid row-by-row Python loops for relational work.
- Partition files by stable, commonly filtered fields; avoid creating many tiny files.
- Do not benchmark a warm cache against a cold-cache baseline without labeling the difference.
- Keep correctness tests independent from performance thresholds.
- Prefer standard SQL for portable transformations. Isolate DuckDB-specific functions and file readers at ingestion or publication boundaries.
- When moving to another engine, verify null ordering, timestamp behavior, decimal rules, identifier case, implicit casts, merge semantics, and regular-expression differences.
