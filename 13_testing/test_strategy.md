# Testing strategy and execution scope

Phase 2 pytest checks actual primary and foreign keys, ranges, coordinates, CSV-to-Parquet transformation, synthetic mass balance and collection reset, two-hour timestamp ordering, join cardinality, mart aggregation and raw-file SHA256 provenance. Phase 3 adds cross-checks of SQL fact/mart reconciliation, weekly statistical outputs and zone-year totals. The standard-library Phase 1 foundation validator remains available. See `14_outputs/reports/data_quality_report.md` for full-table profiling. Tests do not prove that synthetic demand parameters resemble Chennai observations.

Run `python -m pytest 13_testing -q -p no:cacheprovider` with dependencies installed. The completed run used project-local `work/pydeps` on `PYTHONPATH`; this is a tested local environment, not a clean-install CI result. Large-source hash checking streams blocks so the 558 MB PBF need not be read into Python memory at once.

Future test layers should cover feature-leakage boundaries, forecast holdouts, truck-route access/feasibility, cost-rate provenance and independent SQL/Excel/Power BI/cloud reconciliation. Add a small committed synthetic fixture with hand-calculated expectations and deliberately invalid cases before CI, rather than making CI depend on generated multi-million-row files.
