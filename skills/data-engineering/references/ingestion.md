# Ingestion patterns (Python and DuckDB)

Reading files into a typed, contractual dataset. Use these patterns when a project does not already provide a preferred implementation. Adapt names and types to the dataset contract; do not copy examples without validating the actual schema.

Related: [testing-and-quality.md](testing-and-quality.md), [incremental-and-publication.md](incremental-and-publication.md), [performance.md](performance.md).

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


def load_orders(source: Path, cutoff: str) -> list[tuple]:
    with duckdb.connect() as connection:
        connection.execute("SET TimeZone = 'UTC'")
        return connection.execute(
            """
            SELECT order_id, customer_id, amount, ordered_at
            FROM read_parquet($source_path)
            WHERE ordered_at >= CAST($cutoff AS TIMESTAMPTZ)
            """,
            {"source_path": str(source), "cutoff": cutoff},
        ).fetchall()
```

Bind scalar values and file paths. Prefer named parameters when a statement contains parameters in both a query and an enclosing command such as `COPY`, because anonymous parameter ordering can be non-obvious.

Parameters bind to **one** statement. DuckDB raises `NotImplementedException` for a parameterized multi-statement string ("Prepared parameters are only supported for the last statement"), so split multi-step work into separate `execute` calls rather than sending a semicolon-delimited block.

SQL identifiers such as table or column names generally cannot be bound as parameters; validate them against an explicit allowlist before quoting or interpolating them.

Set the session timezone explicitly whenever timestamp behavior matters. `TIMESTAMPTZ` represents an instant, but DuckDB renders and performs some calendar operations using the configured session timezone. Use an in-memory connection for isolated tests. Use an explicit database file when persistence is part of the behavior under test — or when you need results to outlive the connection, which includes quarantine tables (below).

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
    delim = ',',
    quote = '"',
    escape = '"',
    timestampformat = '%Y-%m-%d %H:%M:%S%z',
    columns = {
        'order_id': 'VARCHAR',
        'customer_id': 'VARCHAR',
        'amount': 'DECIMAL(18,2)',
        'ordered_at': 'TIMESTAMPTZ'
    },
    nullstr = ['NULL', '']
);
```

Declaring `columns` fixes the schema but does **not** disable the sniffer. Delimiter, quote, escape, newline, and date/timestamp format are still auto-detected from a bounded sample unless you set them, so a file that changes shape can be reinterpreted without any error. The failure is silent for ambiguous dates: `01/02/2026` parses as either 2 January or 1 February depending on what the sniffer inferred from surrounding rows. Declare every setting the contract depends on.

To confirm what was actually used on a scan rather than assuming, read it back:

```sql
SELECT delimiter, quote, escape, date_format, timestamp_format
FROM reject_scans;  -- populated when store_rejects = true
```

Use automatic type inference for exploration, not as an unstated production contract. Validate a multi-file schema before relying on `union_by_name` because it can hide unexpected evolution.

For JSON, specify the expected structure and distinguish newline-delimited JSON from a JSON array. Reject or quarantine records that cannot meet the contract.

## Quarantining malformed records

Use the built-in rejects tables rather than hand-rolled filtering. Each rejected value is stored with its line, column, and error reason:

```sql
SELECT * FROM read_csv('data/orders.csv', header = true, store_rejects = true);

-- Diagnostics only. Never SELECT * here: reject_errors.csv_line holds the raw
-- failing source row, so a wildcard select copies unredacted source data
-- (names, emails, account numbers) into logs, notebooks, and agent output.
SELECT line, column_name, error_type FROM reject_errors;
```

Three properties constrain how these tables can be used.

### They are temporary

DuckDB creates `reject_errors` and `reject_scans` as temporary tables scoped to the connection. They are gone at disconnect, so they are a diagnostic surface, not durable evidence.

Persisting them requires all three of the following, or the evidence is still lost:

1. A **persistent database file** — `duckdb.connect("warehouse.duckdb")`, not `duckdb.connect()`. Copying rejects into a table on an in-memory connection preserves nothing.
2. **Append semantics** — `INSERT INTO`, not `CREATE TABLE AS`, which fails or replaces on the second run and silently discards prior runs' evidence.
3. **Run and source identity** — without these, rows from different runs and files are indistinguishable and cannot be traced back.

```sql
-- Once, as part of schema setup.
CREATE TABLE IF NOT EXISTS quarantine_orders(
    quarantined_at TIMESTAMPTZ,
    run_id         VARCHAR,
    source_path    VARCHAR,
    line           BIGINT,
    column_name    VARCHAR,
    error_type     VARCHAR
);

-- Per run, on a persistent connection. Deliberately excludes csv_line.
INSERT INTO quarantine_orders
SELECT current_timestamp, $run_id, s.file_path, e.line, e.column_name, e.error_type
FROM reject_errors AS e
JOIN reject_scans  AS s USING (scan_id, file_id);
```

Retain `csv_line` only when the data classification permits it and the store has the same access controls as the source. When it must be kept for debugging, write it to the quarantine location alongside the source, never into run logs or agent output.

### They record values, not records

`reject_errors` holds one row per failed *value*, so a single physical row with three bad columns produces three rows. Counting it directly overstates record loss and will not reconcile against the input.

```sql
-- Error events: how many values failed.
SELECT count(*) AS error_events FROM reject_errors;

-- Rejected records: how many input rows were lost. Use this for reconciliation.
-- Deduplicate on the full identity; `line` alone collides across files in a multi-file scan.
SELECT count(*) AS rejected_records
FROM (SELECT DISTINCT scan_id, file_id, line FROM reject_errors);
```

### They only catch what you declared

- Rejects capture failures against a **declared type**. Ingesting every column as `VARCHAR` rejects nothing and reports zero loss while passing malformed values straight through. Declare the contractual types you intend to enforce.
- Rejects capture cast and line-structure failures, not semantic violations. A negative `amount` or an unknown `status` casts cleanly and lands in the output. Enforce those with the data-quality queries in [testing-and-quality.md](testing-and-quality.md).

Report rejected records alongside the loaded count so the loss is visible, and carry the same figure into reconciliation.

## Reproducible samples

`REPEATABLE` alone is not sufficient. DuckDB guarantees a stable sample only when parallelism is disabled: with multiple threads, samples "are not necessarily consistent even with a fixed seed." Set `threads = 1` for the sampling query, and order explicitly if you intend to compare results row by row:

```sql
SET threads = 1;  -- REPEATABLE is only a guarantee single-threaded
SELECT * FROM read_parquet('data/orders/*.parquet')
USING SAMPLE reservoir(1000 ROWS) REPEATABLE (42)
ORDER BY order_id;
```

A multithreaded seeded sample often *appears* stable across repeated runs, so this defect will not reliably surface in testing. Treat single-threaded execution as the requirement, not as a fallback after observing drift. Restore the previous thread setting afterwards; do not leave the whole session single-threaded.

Reservoir sampling materializes the entire reservoir in memory and shares it across threads, so keep sample sizes small and prefer `bernoulli` when you need a percentage rather than an exact row count.

Use deterministic samples only for exploration. Do not use a sample as proof of an exhaustive invariant.
