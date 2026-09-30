# Project state

Last updated: 2026-09-30. Read before continuing. `docs/two_city_state_snapshot.md` preserves the prior handoff. All files stay in this project root.

## Current Phase
**PROJECT COMPLETE — audited local portfolio scope.** Final audit passed43 pytest tests,13 foundation checks,52 SQL/Python KPI checks and raw/PBIX integrity checks. Public GitHub repository created at https://github.com/Ashwin76038/Smart_Waste_Collection_Optimization; audited sources published (initial audit commit42c0c60a033d5beec75ef067345c43ccd4e2bb98). Local .git metadata writes are blocked by Windows ACLs despite requested access; publication used the authenticated GitHub connector. The local checkout is not synchronized to a remote branch. This status does not claim production deployment, clean-machine replay, executed cloud work or exhaustive UI acceptance.

## GEOGRAPHIC COVERAGE
- **Chennai â€” COMPLETE for synthetic Phases 1â€“5 model/preparation; PARTIAL for real operations.** 1,000 hypothetical bins, 4,380,000 synthetic two-hour readings, 200 real GCC ward polygons. Original Phase 1â€“4 artifacts and 120 protected hashes preserved. Actual sensors, truck GPS, depot/receiving access, fleet and current ward demographics remain missing.
- **Coimbatore â€” COMPLETE for synthetic two-city expansion and Phase 5 model/preparation; PARTIAL for real operations.** 500 independent hypothetical bins, 2,190,000 synthetic readings, 100 OpenCity real ward geometries. Current official boundary certification, ward population, true bin/fleet/route data, receiving entrance and local procurement costs remain missing.

## Completed
- Installed verified Microsoft Power BI Desktop with user approval, refreshed 14 CSV tables plus KPI Measures, and saved the actual PBIX with embedded data, five pages, 16 relationships and 35 measures.
- Executed Desktop DAX reconciliation: 52/52 passed, maximum absolute difference zero. Reviewed all five rendered pages; repaired map coordinate roles, city defaults and navigation labels.
- Canonical two-city 6.57M-reading Parquet/DuckDB layer from previous phase retained. Phase 5 exports 5 dimensions and 9 facts from it without changing Chennai/source artifacts. Grains, keys and 16 active single-direction relationships are documented in `12_powerbi/PHASE5_MODEL.md`.
- DAX measures for collected tonnes, weighted fill, physical overflow slots, collection completion, early-service diagnostic, dispatch priority, one-scenario road savings, assumed fuel/cost, reserved truck capacity, counterfactual spill and forecast MAE. Unsupported average delay is omitted because no independent due timestamp exists.
- Five-page dashboard wireframe, professional theme, exact Desktop build guide, City Comparison panel, operational recommendations and `14_outputs/reports/phase5_business_intelligence_report.md`.
- SQL and independent Pandas export calculations agree on 52 city-specific KPI checks. Sixteen relationship and all declared grain checks pass. Attempt/daily mass differences are 0.37/0.17 kg from float32 rounding; dashboard collected mass uses attempts.
- Within-city ward audit candidates and 70/80/90% route/spill tradeoffs saved with source SQL. Existing Chennai and Coimbatore interactive maps remain separate.

## Files Created
- `12_powerbi/Smart_Waste_Chennai_Coimbatore.pbix`, `desktop_project/`, `DESKTOP_RECONCILIATION.dax`, `DESKTOP_DELIVERY.md`, `desktop_validation_receipt.json`.
- `06_python/scripts/build_powerbi_project.py`, `validate_powerbi_project.py`, `build_desktop_qa.py`.
- `06_python/scripts/build_phase5_bi.py`, `phase5_decision_support.py`, `finalize_phase5.py`; `05_sql/phase5_decision_support.sql`.
- `12_powerbi/phase5_model/`: 14 import CSVs, `qa_receipt.json`, `kpi_reconciliation.csv`, `ward_audit_candidates.csv`, `threshold_tradeoffs.csv`.
- `12_powerbi/PHASE5_MODEL.md`, `PHASE5_MEASURES.dax`, `PHASE5_WIREFRAMES.md`, `PHASE5_BUILD_GUIDE.md`, `PHASE5_RECOMMENDATIONS.md`, `phase5_theme.json`.
- `14_outputs/reports/phase5_business_intelligence_report.md`; `docs/two_city_state_snapshot.md`. README, PLAN, architecture and reproducibility updated.

## Data Acquired
No new source downloads in Phase 5. The previous catalog remains 30 sources; 26 preserved raw assets across 24 source IDs. All operational facts are synthetic. The original city-specific geographic/source caveats remain in `docs/two_city_model.md`.

## Blocked Items
Desktop construction is now complete. Service publication and scheduled refresh were not performed. BigQuery still has no authenticated no-billing run. Real municipal telemetry, comparable GPS/baselines, verified truck/depot/receiving details and local CBE prices remain unavailable. These are external-data/runtime gaps, not hidden completions.

## Important Decisions
Keep a real star schema, not a giant joined flat table. City filters cascade through bin/ward/scenario dimensions; no ambiguous bidirectional path. Date controls historical facts only; fixed dispatch/route snapshots are visibly labeled. Route cards require one city and scenario. Do not sum duplicate city/bin/zone daily views, counterfactual alternatives, or old formula-route proxies. The historical Chennai diesel rate is a common-price proxy in both cities. City comparisons remain descriptive synthetic scenarios.

## Known Limitations
Desktop DAX and five-page rendering were verified. Exhaustive manual filter/scenario combinations and 100%/narrow-window acceptance are not claimed. Refresh uses absolute local CSV paths; online maps require connectivity. Different random seeds, bin counts, geometry vintages and Coimbatore's assumed 0.9 demand multiplier preclude empirical city-effect claims. Forecast bands undercover and near-full recall is limited. Hypothetical depot, capacities, speeds and isolated 24-hour counterfactual limit route decisions. Early collection threshold is a diagnostic, not proof service was unnecessary. No relocation/purchase or annualized savings claim is justified.

## Verification (prior-phase evidence)
`12_powerbi/phase5_model/qa_receipt.json` records 16 valid links and 52/52 SQL/Python KPI checks. `kpi_reconciliation.csv` includes each exact city-level value and tolerance. **Final regression: 39 pytest checks passed; 13/13 offline foundation checks passed.** Theme and QA JSON parse successfully. Desktop DAX: 52/52 checks passed, zero maximum difference. Saved PBIX archive, five pages, embedded model and query verified; SHA256 recorded in `12_powerbi/desktop_validation_receipt.json`. Earlier pytest/foundation results are preserved prior-phase checks, not newly rerun tests.

## Next Phase
No analysis phase remains in the requested portfolio scope. Optional follow-up: clean-machine replay, compact CI fixture, repeated policy experiments and real municipal validation. See docs/FINAL_AUDIT.md for remaining limitations and honest scorecard.

## Final Audit Handover
- Final43-test suite passed on2026-09-30;13/13 foundation checks passed.
- Exact canonical readings:CHN4,380,000;CBE2,190,000;total6,570,000. All26 raw assets matched recorded SHA256.
-14 Chennai SQL queries and24 city-filter executions rerun;52 BI SQL/Python values and16 relationships passed. Relative and absolute tolerances now explicit.
- Saved PBIX unchanged with5 pages/35 measures; prior52 Desktop DAX checks remain historical evidence, not newly rerun Desktop execution.
- Final README, FINAL_PROJECT_REPORT.md, docs/RECRUITER_SUMMARY.md, INTERVIEW_GUIDE.md, RESUME_BULLETS.md, FINAL_AUDIT.md and REPRODUCTION.md created.
- Acquisition integrity/TLS fixes and4 offline regression tests added. Large local data/caches/binaries excluded from Git. Raw files untouched.
- Audit score approximately7.5/10. Cloud execution and full clean installation remain unverified. Do not reinterpret PROJECT COMPLETE as municipal production readiness.
