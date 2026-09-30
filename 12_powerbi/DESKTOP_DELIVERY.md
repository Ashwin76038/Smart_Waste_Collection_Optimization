# Power BI Desktop delivery

Verified 30 September 2026. Actual **Smart_Waste_Chennai_Coimbatore.pbix** is saved beside this document, with an embedded imported model and five report pages. No service publication occurred.

## Contents
1. Executive Overview: historical KPIs, normalized city comparison, daily generation.
2. Waste & Bin Analysis: ward spill ranking, fill bands, bin audit table.
3. Geographic Intelligence: coordinate-based hotspot map, ward risk, frozen dispatch queue.
4. Route Optimization: one-city/scenario fleet comparison, truck details, fuel/cost proxies, modeled spill.
5. Forecasting & Planning: collection requirements, model accuracy, operational queue.

## Open and refresh
Open the PBIX in Power BI Desktop. Use page tabs, or Ctrl+click canvas navigation buttons in edit mode. Scroll detailed tables to see additional rows/columns. Historical pages offer date selections; route/dispatch facts remain fixed at 23 September 2026. Maps require internet connectivity and Map visuals enabled, which was authorized during construction.

Imported data are included in the PBIX. Refresh reads 14 CSVs from this project's phase5_model directory using absolute local paths. Update File.Contents paths in Power Query if moving the project. Scheduled/unattended refresh is not configured.

## Executed validation
Desktop loaded and refreshed the model. All 52 executed DAX reconciliation checks passed with maximum absolute difference zero against independent Python export values. Both cities' operational, base-route, cost, spill and forecasting metrics are covered. The exact query is included in the PBIX DAX query view and DESKTOP_RECONCILIATION.dax.

All five pages rendered and were visually inspected. Fixed the reserved Measures table name (now KPI Measures), default slicer selections, navigation labels and map coordinate roles. The Chennai map renders in its correct geographic extent. Chennai base-route cards show 36 bins, 57.34 km baseline, 45.50 km optimized, 11.85 km saved and 20.66% reduction. Fuel/cost/spill cards show 2.63 L, INR 243.20 and 11.06 L. Planning shows 586 required/forecast-triggered bins and 8 access reviews. Overview shows 1,500 bins and 309,791 completed collections across both cities.

The 94 generated report-definition files passed Microsoft schema checks before Desktop normalization. Saved PBIX archive integrity, five page definitions, embedded DataModel and saved reconciliation query were checked on 30 September. desktop_validation_receipt.json records file size and SHA256.

## Evidence boundaries
All operations are synthetic; geographic context is real and bins hypothetical. Fleet/fuel economy are assumptions; fuel cost uses a historical common-price proxy. This is a decision-method demonstration, not evidence of realized municipal savings.

Not every city/scenario/filter combination was manually exercised. Full 100% zoom and narrow-window acceptance, service publication, scheduled refresh and final portfolio audit are not claimed. Keep the existing Phase 4/5 feasibility and statistical caveats.

## Reproducible authoring
build_powerbi_project.py creates editable PBIP/PBIR and model definitions from preserved exports. build_desktop_qa.py generates the DAX checks. The desktop_project folder retains the editable project. The binary was created by Desktop Save As > Power BI file (.pbix), not by renaming PBIP.

Back up Desktop edits before rerunning the builder: it overwrites definitions and must not run against a project open in Desktop. Do not rerun the old finalize_phase5.py to update state; it describes the previous offline handoff.
