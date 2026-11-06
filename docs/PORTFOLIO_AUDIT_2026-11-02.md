# Power BI builder protection — 2 November 2026

The report builder previously proceeded without the excluded CSV exports and
could overwrite saved report definitions with an incomplete model. Preflight
now requires all 14 exports and nonempty, unique CSV headers before writes.

Three regressions passed: missing exports preserve the existing project,
invalid headers preserve it, and complete fixture headers build the expected
15 model tables and 16 relationships. Windows long-path failure in the first
test run was resolved using a short task-owned pytest temporary directory.

Existing Chennai/Coimbatore data, algorithms and historical validation
receipts are preserved. The full data pipeline and native Desktop were not
rerun in this repair. Whitespace-only checkout differences are not part of
the intended change. No operational savings are newly claimed.

Readiness: 8/10 within the existing simulation portfolio scope. Strong
analytical breadth and historical evidence; clean-machine full reproduction,
real deployment and field verification remain limitations.
