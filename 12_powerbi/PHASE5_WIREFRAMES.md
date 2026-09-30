# Five-page dashboard wireframes

Audience: municipal operations lead reviewing a **synthetic planning demonstration**. At the top of every page show `Synthetic operations | real geographic context | hypothetical route pilots`, the selected city, and the relevant date or frozen snapshot. Use the [theme](phase5_theme.json), Segoe UI, teal for primary series, amber for attention and red only for adverse outcomes. Use `CHN` and `CBE` as stable city IDs; show readable city names. Navigation buttons: Overview, Bins, Geography, Routes, Planning. Tooltips show numerator/denominator, unit, origin and scope; round displays while preserving exact exported values.

## 1. Executive Overview — where is service pressure and what is the pilot worth?

```text
┌─────────────────────── City [both/CHN/CBE] · 2026 date range ───────────────────────┐
│ Synthetic operations · route cards require one city; dispatch as of 23 Sep 2026      │
├── Bin count ── Collected tonnes ── Average fill % ── Overflow slot % ── Completed ───┤
│ Daily generated L/bin-day (line; CHN/CBE)    │ Collection completion % (line)         │
│ City Comparison matrix: bins, L/bin-day, fill, overflow slots, completions/bin-day │
│ One-city base-pilot inset: km saved and route scope; blank for both cities          │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

The city comparison matrix uses normalized metrics and denominators; it does not rank municipalities. The date slicer changes historical cards and lines. The route inset is labelled frozen 23 Sep and is independent of the historical date slicer. Default city: Chennai, with Coimbatore and both available for historical comparison.

## 2. Waste & Bin Analysis — which wards and bins need investigation?

```text
┌────────────────── City [one/both] · date range · ward label ─────────────────────────┐
│ Average bin fill %     Overflow bin-day %     Early collection % (<35% simulated)    │
│ Ward comparison: generated L/bin-day and overflow L/bin-day (ordered bar)            │
│ Fill distribution: bin-day fill bands (or mean-fill histogram)                       │
│ Detail table: ward, bin, capacity, generated L, overflow days, completions           │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Ward visuals use `dim_bin[ward_label]` with `fact_bin_day`, or `dim_zone[ward_label]` with `fact_zone_day`, never duplicate both facts in one summed total. `Overflow Bin-Day %` is based on bin-days, whereas page 1 `Overflow Slot %` is based on two-hour slots. The early flag is a retrospective diagnostic, not an operational judgement about hygiene needs.

## 3. Geographic Intelligence — where should a field team look first?

```text
┌────────────────── City [single select] · date range ──────────────────────────────────┐
│ Bin point map: latitude/longitude; bubble size = overflow bin-days                   │
│ Ward audit candidate table: rank, ward, overflow L/bin-day, issue-date required bins │
│ Snapshot queue: priority tier, current/predicted fill, access review status          │
│ Buttons/links to separate Chennai and Coimbatore interactive HTML maps               │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Use `dim_bin` coordinates at real OSM nodes with clear `hypothetical bin` tooltip. Map uses one city at a time so the two distant extents stay usable. Existing city-specific HTML maps show ward outlines and retrospective hotspots; the priority map shows the frozen dispatch queue. Ward polygon source/vintage is in the tooltip. OSM amenity counts are not compared because the city extraction scopes differ. Local HTML files can be opened alongside the report; do not assume a PBIX web button can open local files on another machine.

## 4. Route Optimization — does a feasible plan improve the matched pilot?

```text
┌──────────── City [single select] · scenario [single select; base_3_trucks] ─────────┐
│ Required/served bins · baseline km · optimized km · km saved · reduction %            │
│ Matched two-bar distance chart                  │ Truck route table by method/vehicle   │
│ Reserved capacity % · travel minutes saved · fuel L saved · cost INR proxy            │
│ 24-hour modeled spill: baseline vs optimized, with negative avoided values visible   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Show feasibility status and reason before any savings card; infeasible scenarios have blank savings. Draw routes only from the selected city’s HTML map; no cross-city polyline. The base scenario is a 60-bin geographic pilot, with 36 Chennai and 34 Coimbatore required stops. Cost carries the historical Chennai common-price qualifier; vehicle capacity is reserved volume, not observed fill. Scenario alternatives are one-at-a-time counterfactuals, not additive trips.

## 5. Forecasting & Operations Planning — which bins should be reviewed next?

```text
┌──────────── City [single select] · issue 23 Sep 2026 · 20-hour horizon ─────────────┐
│ Required bins · forecast-triggered bins · access-review bins · near-full recall      │
│ Test MAE by model (known bins; ridge versus simple baselines)                         │
│ Priority queue: bin, ward, current/predicted fill, tier, reasons, access flag         │
│ Planning note: interval coverage below nominal; human review of missed risks         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Set forecast score filters `split=test`, `evaluation_group=known_bins`; show model on the x-axis and MAE percentage points, not a summed error. The priority queue is one fixed issue snapshot. Forecast-triggered bins are a trigger count; do not present them as a future collection count or calibrated overflow probability.

The prior [City Comparison specification](CITY_COMPARISON_SPEC.md) remains a detailed source for the overview matrix. This five-page design incorporates it into page 1 to match the Phase 5 page target.
