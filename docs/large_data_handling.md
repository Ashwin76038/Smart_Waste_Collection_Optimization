# Large-data handling, measured on this machine

The pipeline generated 4,380,000 **synthetic** scheduled readings and converted monthly CSV files to typed, Zstandard-compressed Parquet. The 12 CSV files use 535,896,739 bytes. Full-schema interim Parquet uses 93,726,968 bytes; the observed-only fact uses 45,450,809 bytes; isolated truth uses 56,383,332 bytes. Different schemas and separate paths make a single headline compression ratio misleading.

## January benchmark

The same task counted January 2026 scheduled rows and observed fill values and summed fill percentages. Each method used a fresh process; peak resident memory was sampled. Results are one local run, not a universal tool ranking.

| Method | Scope | Wall time | Sampled peak RSS | Rows / observed |
|---|---|---:|---:|---:|
| Pandas full-load CSV, selected columns | January, 372,000 rows | 1.07 s | 99.7 MB | 372,000 / 366,450 |
| Pandas 50k-row chunks, selected columns | January | 1.13 s | 98.4 MB | 372,000 / 366,450 |
| DuckDB CSV aggregation | January | 0.40 s | 87.4 MB | 372,000 / 366,450 |
| DuckDB Parquet aggregation | January | 0.24 s | 34.7 MB | 372,000 / 366,450 |

The fill sum agreed across methods to floating-point tolerance. Full benchmark details and file sizes are in `14_outputs/reports/large_data_benchmark.json`. January CSV was 45,131,643 bytes; its observed-only Parquet file was 3,847,017 bytes, with different column sets. Pandas chunking had little measured memory benefit for this narrow two-column month because interpreter/library overhead dominated; its advantage grows when processing a wider or longer file without retaining every chunk. No full-year Pandas load was attempted or measured, and no claim about its exact peak memory is made.

## Filtering and aggregation

`05_sql/phase2_marts.sql` creates a Parquet-backed fact view. The stored `EXPLAIN ANALYZE` uses `WHERE year=2026 AND month='01'`, selects `bin_id` and `fill_level_pct`, and groups by bin. The current plan confirms **one of 12 Parquet files read**. The zero-padded month partition is text; `month=1` would cast and scan all 12 files, so use the matching string predicate. DuckDB documentation explains projection and filter pushdown, including Parquet row-group pruning when statistics permit: https://duckdb.org/docs/lts/data/parquet/overview. This project verifies file pruning and selected columns in its saved plan; it does not claim measured row-group skipping.

A database or columnar engine can read needed columns, filter partitions and aggregate before returning a compact result. Excel's current `.xlsx` worksheet limit is 1,048,576 rows (Microsoft: https://support.microsoft.com/en-us/excel/excel-specifications-and-limits). The 4.38M fact therefore cannot fit on one sheet; even split sheets would obscure grain and validation. `04_excel/collection_qa_sample.xlsx` uses 500 explicitly synthetic rows for human QA, with full-data controls from DuckDB.

## BigQuery concept

The unbilled BigQuery Sandbox can demonstrate the same SQL on a compact aggregate upload. Its documentation currently specifies a 10 GiB **lifetime** storage allowance, 1 TiB of monthly query processing and automatic 60-day expiration: https://docs.cloud.google.com/bigquery/docs/sandbox. See `11_cloud/README.md`, `bigquery_sandbox_demo.sql`, and the January sample/control files. **No cloud query was executed** and no screenshot is presented as execution evidence.

## Reproduction and caveats

Rerun acquisition only when network access is available. Immutable source snapshots plus hashes remain local because raw data and PBF are excluded from Git. `requirements-phase2.txt` pins direct packages used in the local Phase 2 pipeline, but this run used preinstalled packages plus project-local `work/pydeps`, not a fresh isolated environment. The numbers above are tied to that environment and source snapshot; reruns may vary with cache, CPU and library versions. OSM data attribution: © OpenStreetMap contributors, ODbL 1.0, https://www.openstreetmap.org/copyright.

## Two-city expansion — 25 September 2026

The combined logical event dataset is 6.57M rows, partitioned by city/year/month in 24 Parquet files. A CBE January projection/filter reads one file, recorded in `14_outputs/reports/city_expansion/city_partition_query_plan.txt`. Original benchmark measurements remain Chennai-only; they are not represented as new combined benchmarks. The 730-row city-day CSV is the bounded cloud handoff. Counts of physical copies must not be added to logical row counts.
