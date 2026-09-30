# Phase 2 data-quality report

Generated 2026-09-23 T16:17:38.572983+00:00. See data_profile.json for complete column types and missing percentages.

| Dataset | Rows | Columns | Duplicate IDs/rows | Stored bytes |
|---|---:|---:|---:|---:|
| dim_zone_ward | 200 | 11 | 0 | 891257 |
| census_chennai_2011_native | 162 | 97 | 0 | 91726 |
| weather_chennai_grid_2025 | 365 | 7 | 0 | 8492 |
| osm_road_nodes_chennai | 157,785 | 6 | 0 | 3429983 |
| osm_road_segments_chennai | 179,568 | 8 | 0 | 3452120 |
| osm_poi_nodes_chennai | 1,507 | 7 | 0 | 37270 |
| dim_bin | 1,000 | 11 | 0 | 42174 |
| fact_bin_readings | 4,380,000 | 14 | 0 | 45450809 |
| simulation_truth | 4,380,000 | 12 | 0 | 56383332 |
| interim_readings | 4,380,000 | 19 | 0 | 93726968 |
| collection_events | 218,959 | 9 | 0 | DB table |
| bin_daily_metrics | 365,000 | 14 | 0 | DB table |
| zone_daily_metrics | 72,635 | 12 | 0 | DB table |
| route_daily_metrics | 18,200 | 10 | 0 | DB table |
| vehicle_daily_metrics | 18,200 | 9 | 0 | DB table |

## Critical checks
- reading_id_duplicates: 0
- reading_zone_mismatch: 0
- reading_orphan_bin: 0
- bin_orphan_ward: 0
- invalid_fill: 0
- invalid_bin_coordinates: 0
- negative_route_distance: 0
- invalid_collection_status: 0

## Issues
- No critical key/range failures in the implemented tables.

## Model calibration warning
Synthetic overflow occurs in 501,938 of 4,380,000 scheduled bin-slots (11.46%). This is a calibration warning, not observed Chennai overflow; inspect duration/volume and sensitivity before policy or savings claims.

## Interpretation limits
- Official PDFs/HTML are unstructured source snapshots; their byte counts are recorded, not fictional row counts.
- 2011 census geography is not mapped to current wards.
- Synthetic route distance is an explicit planning assumption, not an observed road measurement.
- Estimated memory is extrapolated from a sample, not a measured full-load peak.

## Phase 4 extension

See `phase4_advanced_analytics_report.md` and `phase4_verification.json`. Eight bins fail the 100 m road-access tolerance; five are required on the frozen dispatch date and explicitly queued for access review. All 1,000 ward assignments intersect official polygons. Forecast 90% interval coverage is 88.45%, not a guaranteed risk probability. Routes pass mandatory-stop, directed-distance, capacity and shift checks. Capacity-infeasible scenarios carry NULL savings. Counterfactual mass balance passes; distance savings can coincide with higher spill. Missing OSM restrictions remain an external data limitation.
