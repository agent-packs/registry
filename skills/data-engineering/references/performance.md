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
from __future__ import annotations

import os
from pathlib import Path

import duckdb


def _read_positive_int(path: str) -> int | None:
    try:
        value = Path(path).read_text(encoding="utf-8").strip()
        parsed = int(value)
        return parsed if parsed > 0 else None
    except (OSError, ValueError):
        return None


def _memory_budget_bytes() -> int | None:
    candidates: list[int] = []
    try:
        candidates.append(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (OSError, ValueError):
        pass

    for path in (
        "/sys/fs/cgroup/memory.max",  # cgroup v2
        "/sys/fs/cgroup/memory/memory.limit_in_bytes",  # cgroup v1
    ):
        limit = _read_positive_int(path)
        if limit is not None:
            candidates.append(limit)
    return min(candidates) if candidates else None


def _cpu_budget() -> int:
    if hasattr(os, "sched_getaffinity"):
        host_cpus = len(os.sched_getaffinity(0))
    else:
        host_cpus = os.cpu_count() or 1

    quotas: list[int] = []
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            quotas.append(max(1, int(quota) // int(period)))
    except (OSError, ValueError):
        pass

    quota_v1 = _read_positive_int("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
    period_v1 = _read_positive_int("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    if quota_v1 is not None and period_v1 is not None:
        quotas.append(max(1, quota_v1 // period_v1))
    return min([host_cpus, *quotas]) if quotas else host_cpus


def bounded_connection(memory_fraction: float = 0.6) -> duckdb.DuckDBPyConnection:
    if not 0 < memory_fraction <= 1:
        raise ValueError("memory_fraction must be in (0, 1]")

    connection = duckdb.connect()
    try:
        connection.execute(f"SET threads = {max(1, _cpu_budget())}")
        available = _memory_budget_bytes()
        if available is not None:
            memory_limit_bytes = int(available * memory_fraction)
            connection.execute(f"SET memory_limit = '{memory_limit_bytes}B'")
        return connection
    except Exception:
        connection.close()
        raise
```

`memory_limit` is not a total process-memory cap; extensions, result materialization, and some allocations live outside DuckDB's buffer manager. The helpers therefore respect both host and cgroup limits without promising that every query fits. Do not impose a 1 GB floor: a 256 MiB or 512 MiB container must either receive a smaller setting or fail explicitly, never be configured above its allocation.

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
