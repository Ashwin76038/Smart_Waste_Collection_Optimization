# Chennai and Coimbatore — expansion evidence

Completed 2026-09-25. **All operational comparisons are synthetic scenarios, not official municipal performance.** Chennai remains the preserved original study; Coimbatore adds the user's home city and a second geographic test of the same methods. No Phase 5 dashboard or final presentation was created.

## Coverage and compatible metrics

| Metric | Chennai | Coimbatore |
|---|---:|---:|
| Hypothetical bins | 1,000.000 | 500.000 |
| Scheduled readings | 4,380,000.000 | 2,190,000.000 |
| Mean observed fill (%) | 51.247 | 48.602 |
| Generated L/bin-day | 416.217 | 368.238 |
| Overflow slots (%) | 11.460 | 8.906 |
| Successful services/bin-day | 0.576 | 0.546 |
| Early successful collections (%) | 0.063 | 0.164 |

The combined canonical fact has **6,570,000 readings**, 1,500 hypothetical bins and 300 ward identifiers qualified by city. Both use 365 days and 12 scheduled readings/day. Compare normalized rates; annual total generated waste is not a fair ranking with twice as many Chennai bins. Physical overflow uses latent simulation truth, not fill clipped at 100%. Early service means successful collection below 35% true pre-service fill, an exploratory diagnostic.

![Normalized scenario trends](../../charts/city_comparison/normalized_city_trends.png)

## Independent forecasts and routes

Coimbatore has its own fitted ridge model: known-bin test MAE7.69 percentage points versus 20.57 for its best simple baseline. Chennai remains 8.17 versus 19.65. The same time split, target horizon, baseline definitions and every-fifth-bin holdout are used, but separate training and different synthetic scenarios mean the score gap is not evidence of superior city operations. Nominal 90% residual-band coverage is 88.22% in Coimbatore and 88.45% in Chennai, below nominal. Neither is a calibrated overflow probability.

The Coimbatore 60-bin geographic pilot selects 34 required bins. Three hypothetical trucks serve all 34 once: **38.46 km → 27.97 km**, saving **10.48 km (27.26%)**. Chennai's preserved pilot serves 36 bins:57.34→45.50 km (20.66%). Compare each matched baseline-relative improvement; different layouts/stops prohibit ranking real city efficiency from raw route lengths. No route connects cities. One/two-truck base cases exceed the conservative full-bin volume reserve in both cities.

Coimbatore's base estimates save 33.08 vehicle-minutes and 2.33 L at assumed 4.5 km/L. Cost is **INR 215.22 using Chennai's historical common-price proxy**, not an acquired Coimbatore diesel price. Fossil tailpipe CO2 proxy is 6.26 kg. No realized/annualized savings, wage savings or local certified emission factor is claimed.

Coimbatore's isolated 24-hour replay reduces base spill by 6.10 L, but terminal stock and removed volume also change. This evaluator has no other collections within 24 hours, so it is not a recurring policy result. Chennai's stress-scenario spill tradeoffs remain unchanged and must remain visible.

![Route and forecast comparisons](../../charts/city_comparison/routes_forecasts.png)

## Sources and geographic limits

Coimbatore uses 100 real ward geometries distributed by OpenCity (S25/S26;2024 per metadata, upstream livingatlas.esri.in). They are not certified current municipal polygons. The official CCMC zone-map PDF (S28), sanitation-plan PDF (S27), and NGT-hosted CCMC filing (S29) are archived separately. Public source does not imply current operational ground truth. S27 page 17 reports rounded 2011 population 16.01 lakh and area 257 km²; the context table preserves those references and an explicitly proxy ratio, not a current population/density input. Scanned S29 waste/facility quantities were not loaded as numeric facts without verification.

Real Coimbatore geography includes 258,080 graph nodes,561,940 directed edges,82,523 road nodes inside acquired wards and 2,662 mapped POI features. All 500 hypothetical bins intersect assigned wards and pass 100 mnetwork-access screening. Missing OSM truck restrictions and hypothetical depot/receiving access still prevent deployment certification. The independent centers are approximately 13.08 N80.27 E(Chennai) and 11.02 N76.96 E(Coimbatore).

Coimbatore POI coverage includes ways/morecategories while the preserved Chennai extract is narrower/node-only: **raw POI counts and coverage percentages are not compared**. NASA2025 grid weather is retained separately from hypothetical 2026 operations. Official current ward population, true bin inventory, sensors, collection/GPS logs, truck roster, receiving entrances and local procurement costs remain gaps.

## Statistical decision

No Chennai-versus-Coimbatore significance test is reported. Coimbatore has 500 bins versus 1,000, a distinct random seed and an explicit 0.9 demand-factor multiplier. Apparent mean differences are partly encoded by design. Two synthetic cities, one seed per city and repeated correlated bin/day observations are not independent evidence for a real city effect. `07_statistics/two_city_descriptive_diagnostics.csv` reports 365 city-days per city, moments, quartiles, skewness and lag-one autocorrelation. These support descriptive comparison, not causal or population inference. Route comparisons use a single fixed planning date; no t-test on individual route legs is justified.

## Model, quality and handoff

Use the [city-aware model contract](../../../docs/two_city_model.md) and [Power BI city-slicer specification](../../../12_powerbi/CITY_COMPARISON_SPEC.md). City-specific and both-city SQL outputs are in `14_outputs/tables/city_comparison/`; eight queries execute with all three filters. Prepared exports have explicitcity_id/globalkeys. A CBE/January predicate reads 1 of 24 Parquet files. Original ChennaiSQL still targets the unchanged legacy database.

Final executed tests and preservation results are in `verification.json`; field types/null percentages are in `data_profile.json`. All original raw snapshots remain manifest-linked. `chennai_preservation.json` covers 120 prior data/output files. This expansion is ready as a documented simulation, with real-data deployment gaps explicit. Stop before Phase 5.
