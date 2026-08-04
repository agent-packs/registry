# Performance and portability (Python and DuckDB)

Making a correct pipeline faster without changing what it produces, and keeping it movable between engines.

Related: [ingestion.md](ingestion.md), [testing-and-quality.md](testing-and-quality.md), [incremental-and-publication.md](incremental-and-publication.md).

## Measure before changing anything

- Capture a baseline at representative scale in the same environment. A speedup measured on a fixture does not transfer.
- Use `EXPLAIN` or `EXPLAIN ANALYZE` on representative data before guessing at bottlenecks.
- Do not benchmark a warm cache against a cold-cache baseline without labeling the difference.
- Verify exact semantic equivalence after every optimization. Faster incorrect output is a regression, so keep the transformation tests green throughout.
- Keep correctness tests independent from performance thresholds, so a slow machine cannot look like a data defect.

## Resource limits

Bound DuckDB explicitly with values derived from the host, not copied from an example. Read the actual limits — `os.cpu_count()`, cgroup memory limits under `/sys/fs/cgroup/memory.max`, or the container's declared allocation — and set a fraction of available memory rather than a fixed figure. A hardcoded `'4GB'` overcommits a 2 GB container and wastes a 64 GB host.

```python
import os

import duckdb


def bounded_connection(memory_fraction: float = 0.6) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    threads = max(1, (os.cpu_count() or 2) // 2)
    connection.execute(f"SET threads = {threads}")
    try:
        with open("/sys/fs/cgroup/memory.max") as handle:
            raw = handle.read().strip()
        if raw != "max":
            budget_gb = max(1, int(int(raw) * memory_fraction) // 1024**3)
            connection.execute(f"SET memory_limit = '{budget_gb}GB'")
    except (OSError, ValueError):
        pass  # fall back to DuckDB's own detection rather than guessing
    return connection
```

Set a spill location with `SET temp_directory = '...'` when large sorts or joins would otherwise fail, having confirmed the path is writable and has capacity. It is not a universal default: read-only or memory-backed filesystems make it useless, a full spill volume converts an out-of-memory failure into a disk-full one affecting other processes, and heavy spilling is often the signal that the query should be fixed rather than accommodated.

## Reducing work

- Select only required columns and filter as early as semantics permit.
- Push filtering, projection, joins, and aggregation into the engine rather than into Python.
- Avoid row-by-row Python loops for relational work.
- Aggregate to the intended grain before joining incompatible grains, so a fan-out never materializes.
- Partition files by stable, commonly filtered fields; avoid creating many tiny files, which cost more in listing and metadata than they save in scanning.

## Portability

- Prefer standard SQL for portable transformations. Isolate DuckDB-specific functions and file readers behind ingestion and publication boundaries.
- When moving to another engine, verify null ordering, timestamp behavior, decimal rules, identifier case, implicit casts, merge semantics, and regular-expression differences.
- Engine defaults differ in ways that change results silently rather than raising: division semantics, string comparison and collation, and rounding of half-way decimal values are the common surprises. Assert them in tests rather than assuming they carried over.
