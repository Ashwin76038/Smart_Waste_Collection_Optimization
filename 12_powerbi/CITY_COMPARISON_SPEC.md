# Phase 5 preparation — city slicer and comparison page

This is the earlier city-comparison planning specification, **not a completed Power BI report**. Phase 5 now provides the smaller, tested import schema in [`phase5_model/`](phase5_model/qa_receipt.json), its [relationship contract](PHASE5_MODEL.md), [DAX](PHASE5_MEASURES.dax) and [build guide](PHASE5_BUILD_GUIDE.md). Use those as the current implementation instructions; the older `two_city_data/` extracts remain reproducible source-serving snapshots. Do not import all 6.57 million sensor records into the report by default.

## Relationships

Use `dim_city[city_id]` (unique CHN/CBE) for the slicer displaying `city_name`. Establish single-direction one-to-many relationships. Avoid multiple active filter paths:

- For bin detail: dim_city → dim_bin → bin_daily_metrics / collection_events / collection_priority, using bin_key. Do not also create a parallel active dim_city→these same facts path. All facts retain city_id for QA and SQL filtering.
- For the overview: dim_city → city_daily_metrics. The dimension date → service_date_local.
- For routes: dim_city → route_scenarios and dim_city → fact_routes. Add independent scenario/method filters; scenario keys include city. Do not link these two facts directly. Import either fact_routes or fact_vehicle_operations, since they represent the same rows.
- For forecast evaluation: dim_city → forecast_evaluation. Require a selected split, group and model. Do not sum model-error metrics across models; a combined-city MAE, if offered, must weight by n and label separately fitted models.
- For weather: dim_city → fact_weather; date → date. Show only in a separate 2025 context view, never align with hypothetical 2026 days as if simultaneous.
- Ward drill-down uses zone_key and city-aware zone labels. Choose a single active city→zone→fact hierarchy in the zone page; do not add a second active hierarchy through bins to the same fact.

The dim_location and dim_vehicle tables provide optional mapping/fleet detail. P (formula proxy) and R (road-routing scenario) vehicle keys are different and must not be merged. Route stop depot rows have no bin_key, so they require a separate depot marker rather than a missing-bin error.

## Weighted measures

```dax
Average Fill % = DIVIDE(SUM(city_daily_metrics[fill_sum_pct]), SUM(city_daily_metrics[received_readings]))
Overflow Slot % = 100 * DIVIDE(SUM(city_daily_metrics[overflow_slots]), SUM(city_daily_metrics[scheduled_readings]))
Generated L per Bin-Day = DIVIDE(SUM(city_daily_metrics[generated_l]), SUM(city_daily_metrics[bins]))
Collections per Bin-Day = DIVIDE(SUM(city_daily_metrics[successful_collections]), SUM(city_daily_metrics[bins]))
Simulated Generated Tonnes = SUM(city_daily_metrics[generated_l]) * 0.12 / 1000
Distance Reduction % = 100 * DIVIDE(SUM(route_scenarios[km_saved]), SUM(route_scenarios[baseline_km]))
```

Distance measures require **one scenario selection**, feasible routes and matched complete baselines. Do not aggregate repeated fuel-only scenarios as additional real trips. Keep infeasible savings BLANK. Bin count uses `DISTINCTCOUNT(dim_bin[bin_key])`, not SUM of repeated daily counts. Forecast demand shows the frozen dispatch prediction as fill percent, not future kilograms without an explicit conversion. Never sum inventory over dates.

## City Comparison page

Display a persistent banner: **Synthetic operations · real geographic context · hypothetical routing pilots**. Two columns, Chennai and Coimbatore, should show:

1. Scenario population: bins (1,000 / 500), dates, scheduled/received readings, model label.
2. Comparable normalized work: litres per bin-day, weighted observed fill, physical-overflow slot share, services per bin-day, retrospective early-success percentage.
3. Independent forecast performance: MAE/RMSE, baseline MAE, validation-band coverage, test n. Unit is fill-percentage points. Include the separate-fit caveat.
4. Route cards: required/served pilot bins, matched baseline and optimized km, percent reduction, reserved volume utilization, shift hours and feasibility status. Explain each pilot has 60 geographically selected bins but different required stops/layouts.
5. Cost cards: assumed km/L, common historical Chennai-price proxy, estimated fuel and tailpipe CO2. Do not label Coimbatore fuel cost as a local sourced rate.
6. Service tradeoff: 24-hour counterfactual spill and terminal inventory; negative avoided spill remains visible.

Maps stay on separate Chennai/Coimbatore pages or swap map extent with a single-city slicer. Do not zoom both distant cities into one operational map. Slicer options: Chennai, Coimbatore, both for tabular normalized comparisons only. Prevent mixed-city route drawing.

## Acceptance checks for later implementation

- Each single-city selection reproduces `14_outputs/tables/city_comparison/01_city_comparison_CHN.csv` or `_CBE.csv` and the corresponding routing query export.
- Both-city weighted fill uses numerator/denominator totals, not the unweighted mean of city means.
- Empty filters produce BLANK, not zero risk. Infeasible scenarios display no savings claim.
- Low-bin/high-bin city comparisons use normalized rates; no per-capita KPI without aligned population and geography.
- Current ward boundaries, POI counts, cost rates and simulated demand are not represented as equally verified inputs.
- No cross-city p-value or causal city ranking is shown. Source/proxy/origin caveats survive exports.

The five-page Phase 5 wireframe places the city comparison matrix on Executive Overview. Power BI Desktop execution and PBIX visual QA remain to be done in a later Desktop session; no completed PBIX is claimed here.
