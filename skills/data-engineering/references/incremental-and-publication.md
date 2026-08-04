# Incremental processing and publication (Python and DuckDB)

Publishing output safely, advancing watermarks without losing data, and reconciling the result.

Related: [ingestion.md](ingestion.md), [testing-and-quality.md](testing-and-quality.md), [performance.md](performance.md).

## Publishing a single file

Write to a unique staging path, validate it, then swap it into place.

```python
import os
import uuid
from pathlib import Path

import duckdb


def build_orders(source: Path, destination: Path, cutoff: str) -> None:
    source, destination = source.resolve(), destination.resolve()
    if source == destination:
        raise ValueError(f"refusing to publish over the source: {source}")

    # Unique per attempt. A predictable staging name lets concurrent runs
    # interleave writes into one file, and lets one run's cleanup delete
    # another run's in-progress output.
    staging = destination.with_name(
        f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.staging"
    )
    try:
        with duckdb.connect() as connection:
            connection.execute("SET TimeZone = 'UTC'")
            connection.execute(
                """
                COPY (
                    WITH typed AS (
                        SELECT
                            CAST(order_id AS VARCHAR) AS order_id,
                            CAST(customer_id AS VARCHAR) AS customer_id,
                            CAST(amount AS DECIMAL(18, 2)) AS amount,
                            CAST(ordered_at AS TIMESTAMPTZ) AS ordered_at
                        FROM read_parquet($source_path)
                    )
                    SELECT * FROM typed
                    WHERE ordered_at >= CAST($cutoff AS TIMESTAMPTZ)
                ) TO $destination_path (FORMAT PARQUET)
                """,
                {
                    "source_path": str(source),
                    "cutoff": cutoff,
                    "destination_path": str(staging),
                },
            )
            # Publish only what has been checked. Raises on violation.
            assert_contract(connection, f"read_parquet('{staging}')")
        os.replace(staging, destination)
    finally:
        staging.unlink(missing_ok=True)
```

Filtering happens inside the CTE so the predicate applies to the cast `TIMESTAMPTZ`, not the raw column. Filtering before the cast compares whatever type the file happens to hold against a `TIMESTAMPTZ`, which for a naive `TIMESTAMP` column silently applies the session timezone and shifts the boundary.

Three properties make the pattern work, and the ordering between them matters.

**Validate before swapping.** Staging is the only point at which you can inspect the new output while the previous one is still live. Publishing an unvalidated staged file is the same defect as writing to the destination directly, with an extra step.

**Never publish over the source.** Resolve both paths and compare. Without the guard, `build_orders(p, p, ...)` destroys the input.

**Keep staging on the destination's filesystem.** `os.replace` is atomic only within one filesystem; across devices it raises `OSError` with `EXDEV` ("Invalid cross-device link"). It does not silently fall back to a copy, so the failure is loud — but it fails after the expensive write, so choose the path correctly up front.

DuckDB in practice leaves an existing single-file `COPY` target intact when the query fails partway through, so the naive version is less immediately destructive than it looks. Do not rely on that: it is not a documented guarantee, it does not extend to directory writes, and it does not hold across engines. The validation step needs staging regardless.

## Publishing a partitioned dataset

`os.replace` does **not** generalize from files to directories. Replacing an existing non-empty directory raises `OSError` with `ENOTEMPTY` ("Directory not empty"), so the single-file pattern silently stops being atomic exactly where output gets large enough to be partitioned. Removing the old directory first to make the rename succeed reintroduces the destroy-then-write window the pattern exists to avoid.

Publish immutable versioned directories and swap a pointer instead:

```python
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb


def publish_partitioned(
    connection: duckdb.DuckDBPyConnection, root: Path, run_id: str
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    version = root / f"v_{stamp}_{run_id}"          # never reused, never mutated

    connection.execute(
        """
        COPY (SELECT * FROM curated_orders)
        TO $out (FORMAT PARQUET, PARTITION_BY (order_date))
        """,
        {"out": str(version)},
    )
    assert_contract(connection, f"read_parquet('{version}/**/*.parquet')")

    # Atomic pointer swap: replacing a symlink is a rename of the link itself.
    pointer = root / "current"
    staged_pointer = root / f".current.{uuid.uuid4().hex}.tmp"
    staged_pointer.symlink_to(version.name)
    os.replace(staged_pointer, pointer)
    return version
```

Readers resolve `root/current` and are never exposed to a partially written version. A reader that opened the previous version keeps a consistent view until it finishes, which is why old versions must not be deleted immediately — retain them for at least the longest expected read, then prune oldest-first.

Where symlinks are unavailable — object stores in particular — publish an atomically replaced **manifest** instead: write the version's file list to a single small object, then replace the manifest object in one operation. Readers read the manifest, then the files it names. A transactional catalog (Iceberg, Delta, DuckLake) provides the same guarantee with snapshot isolation and retention built in; prefer it over hand-rolled pointers when the project already has one.

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

### Publish and watermark advance must be atomic

Publishing data and recording the new watermark are two writes. If they are not atomic, the crash window between them determines whether the failure is recoverable:

- **Watermark advanced, publish not durable:** the next run starts after data that was never written. The gap is permanent and silent — no error, no duplicate, nothing to detect it except reconciliation against the source.
- **Publish durable, watermark not advanced:** the next run reprocesses an already-published interval. Harmless when the publish is idempotent, which is the property the rest of this file requires anyway.

The second failure is recoverable and the first is not, so the ordering rule is unconditional: **never advance the watermark before the publish is durable.**

When the watermark lives in the same database as the output, commit both in one transaction:

```python
import duckdb

MERGE_ORDERS = """
MERGE INTO curated_orders AS target
USING staging_orders AS source ON target.order_id = source.order_id
WHEN MATCHED THEN UPDATE SET
    customer_id = source.customer_id,   -- corrections apply to every mutable
    amount      = source.amount,        -- column, not just the obvious ones
    ordered_at  = source.ordered_at
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, amount, ordered_at)   -- never positional
    VALUES (source.order_id, source.customer_id, source.amount, source.ordered_at)
"""


def publish_increment(
    connection: duckdb.DuckDBPyConnection, pipeline: str, interval_end: str
) -> None:
    connection.execute("BEGIN TRANSACTION")
    try:
        # 1. Guard. A validation SELECT aborts nothing on its own: read the
        #    result and raise, or the MERGE below runs anyway.
        duplicates = connection.execute(
            """
            SELECT order_id, count(*) AS occurrences
            FROM staging_orders
            GROUP BY order_id
            HAVING count(*) > 1
            ORDER BY occurrences DESC
            LIMIT 5
            """
        ).fetchall()
        if duplicates:
            raise ValueError(f"duplicate merge keys in staging_orders: {duplicates}")

        # 2. Publish.
        connection.execute(MERGE_ORDERS)

        # 3. Advance the watermark in the same transaction.
        connection.execute(
            """
            UPDATE pipeline_watermark
            SET processed_through = CAST($interval_end AS TIMESTAMPTZ)
            WHERE pipeline_name = $pipeline
            """,
            {"interval_end": interval_end, "pipeline": pipeline},
        )

        # 4. Confirm it actually moved. An UPDATE matching zero rows succeeds
        #    silently, which would commit data with a stale boundary.
        advanced = connection.execute(
            """
            SELECT count(*) FROM pipeline_watermark
            WHERE pipeline_name = $pipeline
              AND processed_through = CAST($interval_end AS TIMESTAMPTZ)
            """,
            {"interval_end": interval_end, "pipeline": pipeline},
        ).fetchone()[0]
        if advanced != 1:
            raise ValueError(f"watermark for {pipeline} did not advance")

        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
```

Each statement is a separate `execute` call. A semicolon-delimited block carrying parameters raises `NotImplementedException` in DuckDB, and a `SELECT` embedded in such a block could not stop the statements after it in any case.

Three details in the `MERGE` are load-bearing:

- **Deduplicate staging before merging.** DuckDB does not raise on a source with duplicate merge keys — it silently applies one arbitrary row, so the result is non-deterministic and reruns need not reproduce it. Uniqueness must be asserted, as in step 1.
- **Update every mutable column.** Omitting one pins it at its first-seen value, so corrections to that field are accepted, reported as merged, and discarded. Columns absent from `UPDATE SET` should be absent by decision, not oversight.
- **List target columns in the `INSERT`.** Positional inserts bind to current column order, so adding or reordering a target column silently shifts values into the wrong fields, with no error whenever types remain compatible.

### Deriving the watermark from published data

Reading the boundary back from the output (`SELECT max(...) FROM curated_orders`) removes the second write entirely, but **only if the column is a monotonic ingestion coordinate** — an append-only ingestion timestamp, source sequence number, log offset, or file arrival order.

Never derive it from event time. `max(ordered_at)` advances the boundary past an interval that late events are still arriving for, and every such event is skipped permanently and silently. That is the same failure as advancing the watermark before publishing, reintroduced through the choice of column.

If only event time is available, the boundary alone is insufficient. Pair it with a bounded lookback and an idempotent merge:

```sql
-- Reprocess a lookback window on every run; the merge makes the overlap free.
WHERE ordered_at >= CAST($watermark AS TIMESTAMPTZ) - INTERVAL '3 days'
  AND ordered_at <  CAST($interval_end AS TIMESTAMPTZ)
```

State the lookback in the contract, size it against observed arrival lag rather than intuition, and monitor for events arriving outside it — those are silent losses the pipeline cannot recover on its own.

### Tests

1. Initial load
2. Identical rerun
3. New records exactly on both interval boundaries
4. Late record inside the supported lookback
5. Correction of an existing key
6. Failure before publication followed by retry
7. Failure after publication but before the watermark advances — the next run must not skip the interval
8. Watermark advanced against a publish that later proves invalid — recovery must be possible without manual reconstruction
9. Backfill overlapping already-published data

## Reconciliation

Compare sources and targets at the same business grain and filter window. Record more than row counts:

```sql
SELECT
    count(*) AS row_count,
    count(DISTINCT order_id) AS distinct_orders,
    SUM(amount) AS total_amount,
    MIN(ordered_at) AS first_ordered_at,
    MAX(ordered_at) AS last_ordered_at
FROM curated_orders
WHERE ordered_at >= $start_time
  AND ordered_at < $end_time;
```

For row-preserving pipelines, a useful conservation equation is:

```text
input = published + rejected + intentionally_filtered + superseded
```

Each input row must land in exactly one term. `superseded` is the catch-all for rows consumed but not separately published: duplicates collapsed during deduplication, older versions replaced by a correction, and rows removed by a tombstone. Counting a deduplicated row under both `published` and `superseded`, or under neither, is the usual reason this fails to balance.

The identity holds only while the transformation preserves grain. Aggregation, fan-out joins, pivots, and snapshotting break it by construction, not as a defect. Where grain changes, drop the row-count identity and reconcile a measure the transformation is contractually required to preserve — a summed amount, a distinct key count — and state which invariant you chose.
