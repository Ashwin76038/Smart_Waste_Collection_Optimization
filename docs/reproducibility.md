> Final-audit status (2026-09-30): an actual five-page PBIX has been delivered. Earlier phase-status statements below are historical. Current entry points are README.md, FINAL_PROJECT_REPORT.md and docs/REPRODUCTION.md. Do not run historical finalizers over the final handover.

# Reproducibility and Phase 2 execution

Run from the project root on Windows. The completed run used Python 3.10 with globally available NumPy, Pandas, PyArrow, DuckDB, Requests, OpenPyXL and psutil, plus project-local packages in `work/pydeps` (pytest, osmium, Shapely and pypdf). Direct package versions are pinned in `requirements-phase2.txt`; this is **not a tested clean-environment lockfile**. Keep caches, virtual environments, spills and scratch output under this root. Do not modify raw snapshots manually.

Stage order for a clean rerun with legitimate download access:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'work/pydeps'  # completed host only; omit in a clean installed environment
python 06_python/scripts/acquire_sources.py --large
python 06_python/scripts/prepare_real_sources.py official
python 06_python/scripts/prepare_real_sources.py osm
python 06_python/scripts/build_synthetic_bins.py
python 06_python/scripts/generate_operations.py 365
python 06_python/scripts/convert_events.py
python 06_python/scripts/build_duckdb.py
python 06_python/scripts/profile_data.py
python 06_python/scripts/benchmark_large_data.py
python 13_testing/validate_foundation.py
python -m pytest 13_testing -q -p no:cacheprovider
```

The acquisition script preserves existing snapshots and checks hashes. The dated Geofabrik PBF is large (~558 MB). OSM parsing can take several minutes. The generator uses seed `20260923` and produces exactly 1,000 bins × 365 days × 12 slots = 4,380,000 scheduled readings for a hypothetical 2026; it does not replay observed Chennai operations. CSV conversion and DuckDB builds are scripted. A clean install from `requirements-phase2.txt` has not been validated. Workbook generation used the bundled artifact runtime and is delivered as a QA artifact; rerunnable Python-only generation is not claimed.

Provenance is in `02_research/acquisition_manifest.csv` (source URL, UTC retrieval, bytes, SHA256). The source catalog indicates unacquired references and original licensing caveats. `14_outputs/reports/data_profile.json` records schema, missingness, key/range checks, file sizes and estimated memory; `data_quality_report.md` is its concise handoff. The large-data benchmark is a single measured local January run, not a platform comparison. `11_cloud/` contains an unexecuted BigQuery Sandbox upload workflow and exact SQL. No cloud billing or account setup was performed.

For Phase 3, run `python 06_python/scripts/run_sql_analytics.py`, then `python 06_python/scripts/phase3_eda.py`, then `python 06_python/scripts/phase3_statistics.py`. The direct analysis packages are listed in `requirements-phase3.txt`. SQL and Python outputs are generated from the existing Phase 2 database; no raw file is changed. The three notebooks in `06_python/notebooks/` call the same scripts and have validated notebook structure/Python syntax. Their scripts executed successfully, but Jupyter kernel startup failed in this Windows sandbox when it attempted to set a connection-file ACL, so the saved notebooks have no executed cell outputs. Run them from the project root in an environment where Jupyter can start normally.

Raw and large generated data remain untracked. A local Git repository exists on `main`, but no commit or remote was created. Future phases should add a compact fixture, a tested clean environment/lockfile and independent scenario replications before publishing a portable repository. A run manifest with git revision, output hashes and replay metrics is still a gap against the long-term foundation design.

## Phase 4 executed workflow

[Phase 4 methodology](phase4_methodology.md) lists scripts in dependency order, units, assumptions, local dependency paths and rerun limits. `requirements-phase4.txt` pins used direct versions; `14_outputs/reports/phase4_run_manifest.json` records output hashes and versions. OR-Tools uses a five-second search limit, so saved feasible routes are authoritative for the reported run. The complete pytest suite and foundation checks are recorded in `phase4_verification.json`. A clean installation remains unverified.

## Two-city expansion — 25 September 2026

Expansion commands and isolated workspaces are documented in `two_city_model.md`. Existing Chennai outputs are protected by 120 saved hashes. `finalize_two_city.py` updates documentation, runs pytest and offline foundation checks, and writes verification and artifact hashes without rerunning generators or models. The CBE seed is 20260924; CHN remains 20260923. A regenerated scenario needs a new version of canonical partitions; the builder deliberately reuses existing partitions. Dependencies and clean-install limitations remain unchanged. No billing/cloud activation occurred.

## Phase 5 — business intelligence

From the project root with existing local dependencies: set `PYTHONPATH` to `work/phase4deps;work/pydeps`, run `python 06_python/scripts/build_phase5_bi.py`, then `python 06_python/scripts/phase5_decision_support.py`, then `python 06_python/scripts/finalize_phase5.py`. The first script reads the combined DuckDB without mutation, writes 14 CSVs, and independently reconciles 52 city-specific values. The second runs `05_sql/phase5_decision_support.sql`. Manual Desktop steps and final visual QA remain in `12_powerbi/PHASE5_BUILD_GUIDE.md`. Regenerating prior synthetic city datasets is unnecessary.
