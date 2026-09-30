# BigQuery Sandbox: optional no-billing demonstration

Verified reference: [Google Sandbox documentation](https://docs.cloud.google.com/bigquery/docs/sandbox), accessed 2026-09-23 (S21).

The documented limits are 10 GiB **lifetime** storage (deleting data does not refund it), 1 TiB query processing monthly, and automatic expiration of tables/views/partitions after 60 days. Streaming, DML and Data Transfer Service are unsupported. This is a dated research finding; recheck at execution.

No billing account, paid service, free-trial activation or cloud bucket is needed or authorized for this phase. Later use a dedicated unbilled Sandbox project only if available. If account policy demands billing, record the blocker and keep the project local.

Upload a compact aggregate or small sample within the current browser local-upload limit, rather than all simulation runs. Target at most 10 MiB for the first demonstration, measure bytes and existing lifetime quota, and avoid repeated uploads. Do not assume compressed Parquet size equals quota consumption. Keep full-scale analytics in local DuckDB. Use SELECT/CTE/window queries and supported DDL/batch load paths; no MERGE/UPDATE pipeline.

Evidence required later: account's sandbox/no-billing status with personal information redacted, source/output schema, job ID, query, estimated and actual scan bytes, local-versus-cloud reconciliation, upload date and expiration. Use maximum-bytes controls where supported; partition predicates and column selection reduce scans. Export evidence locally before expiry. No cloud setup has been performed.
