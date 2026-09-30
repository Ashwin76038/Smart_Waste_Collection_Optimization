# Reproduction and review

## Existing local project: verify without rebuilding
Executed environment: Windows, Python3.10.11. The local dependency folders are ignored installation caches, not portable dependencies.

```powershell
$env:PYTHONPATH="$PWD\work\phase4deps;$PWD\work\pydeps"
python -m pytest 13_testing -q -p no:cacheprovider
python 13_testing/validate_foundation.py
python 06_python/scripts/final_audit.py
python 06_python/scripts/run_city_sql.py
```

The final audit reran14 Chennai queries and24 city/filter queries. `run_sql_analytics.py` refreshes a protected run-manifest timestamp; avoid rerunning it merely to inspect saved outputs. Run its named SELECT statements read-only when checking queries. The explicit final-audit preservation amendment records the one metadata change;119 other protected artifacts retain original hashes.

## Fresh source checkout
A complete clean-machine replay is **not yet verified**. Source-only tests can run after dependency installation, but integration tests require regenerated data. No CI green badge is implied.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python -m pytest 13_testing/test_acquisition_safety.py -q
```

Direct analytical versions reflect the executed environment; optional validation helpers are not a transitive lock. Allow several GB for the regional OSM file, monthly CSVs, Parquet copies and local dependencies. Review licenses before sharing downloaded data. Raw snapshots are intentionally absent from GitHub.

Restore exact acquisition manifest URLs/hashes with `python 06_python/scripts/restore_raw_snapshots.py`. This uses normal TLS and refuses changed bytes. Historical URLs may no longer return the recorded snapshot; a failure is a real reproducibility blocker, not permission to relabel new data. In that case obtain the archived asset, or create a new versioned manifest and recompute results. Two Census snapshots historically used a logged TLS exception; future acquisition no longer disables validation. Fresh restoration has not been run in this audit.

## Ordered full rebuild (new workspace only)
Create the numbered empty folders from PLAN.md, including `03_data/raw`, `03_data/interim`, `03_data/processed`, `03_data/synthetic`, `work`, and `14_outputs/{reports,tables,charts,maps}`. Retain the checked-in config and source manifests.

```powershell
python 06_python/scripts/restore_raw_snapshots.py
python 06_python/scripts/prepare_real_sources.py official
python 06_python/scripts/prepare_real_sources.py osm
python 06_python/scripts/build_synthetic_bins.py
python 06_python/scripts/generate_operations.py 365
python 06_python/scripts/convert_events.py
python 06_python/scripts/build_duckdb.py
python 06_python/scripts/profile_data.py
python 06_python/scripts/benchmark_large_data.py
python 06_python/scripts/run_sql_analytics.py
python 06_python/scripts/phase3_eda.py
python 06_python/scripts/phase3_statistics.py
python 06_python/scripts/phase4_extract_roads.py
python 06_python/scripts/phase4_forecast.py
python 06_python/scripts/phase4_geospatial.py
python 06_python/scripts/phase4_routing.py
python 06_python/scripts/phase4_counterfactual.py
python 06_python/scripts/expand_cities_acquire.py
python 06_python/scripts/run_city.py --city CBE --stage extract
python 06_python/scripts/run_city.py --city CBE --stage prepare
python 06_python/scripts/run_city.py --city CBE --stage generate
python 06_python/scripts/run_city.py --city CBE --stage convert
python 06_python/scripts/run_city.py --city CBE --stage marts
python 06_python/scripts/run_city.py --city CBE --stage forecast
python 06_python/scripts/run_city.py --city CBE --stage geospatial
python 06_python/scripts/run_city.py --city CBE --stage routing
python 06_python/scripts/run_city.py --city CBE --stage counterfactual
python 06_python/scripts/build_two_city.py
python 06_python/scripts/run_city_sql.py
python 06_python/scripts/build_phase5_bi.py
python 06_python/scripts/phase5_decision_support.py
```

Routing invokes priority creation. Expansion initializes CBE directories/config; it also captures Chennai preservation state. Cached canonical partitions are reused by design: never mix newly generated city facts with old canonical partitions. Use a new workspace/version for regeneration. Five-second solver runs may differ by hardware. The above order documents dependencies; it is not a claim that a clean replay passed.

Do **not** run `finalize_phase5.py` or `finalize_two_city.py` after final handover: these historical documentation generators are guarded. Other historical `phase4_document`/handoff scripts should also not replace final narrative.

## Power BI, Excel and cloud
The local PBIX includes embedded data. For a fresh clone, generate14 CSV exports, update absolute CSV paths in the PBIP semantic model, and open the project in Power BI Desktop; follow PHASE5_BUILD_GUIDE.md. Building PBIP definitions with `build_powerbi_project.py` overwrites authored definitions—use a disposable copy and preserve Desktop edits. Save As PBIX, then run DESKTOP_RECONCILIATION.dax. PBIX validation in final_audit.py requires this local binary. No unattended PBIX save is claimed.

Excel sample CSVs and workbook specifications are in04_excel. The original workbook was created through the artifact runtime; full workbook regeneration is not in the Python pipeline. Notebooks call script companions and contain no saved executed outputs.

11_cloud contains Sandbox SQL/upload instructions only. No cloud account, billing, execution or scheduled refresh was performed.

## Publication contents
Source, small analytical outputs, reports and PBIP definitions are versioned. Raw data, sensor CSVs, Parquet, DuckDB, PBIX, Excel binaries, graph caches and installers remain local. OSM derivatives require OpenStreetMap attribution/ODbL review; government assets retain individual terms. The publication is an auditable source portfolio, not a one-click deployment.
