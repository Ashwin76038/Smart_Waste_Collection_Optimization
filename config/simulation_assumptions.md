# Synthetic operational assumptions, version 1

**Synthetic operational data generated for scalability, analytics and optimization demonstration.** These are design choices, not measured Chennai parameters.

| Parameter | Value | Meaning / sensitivity risk |
|---|---:|---|
| Bin count | 1,000 | Five hypothetical bins in 199 wards plus five extra in ward 032; ward 200 had zero eligible mapped road nodes; not observed inventory |
| Two-hour slots | 12/day | Scheduled readings, including explicit missing telemetry |
| Days | 365 | Hypothetical 2026 service year; late 2026 is future as of project creation |
| Random seed | 20260923 | Reproducible single stream; independent simulation replications deferred |
| Capacity | 240/660/1100 L with 10/60/30% sampling | Hypothetical physical capacities, not supplier or GCC registry |
| Density | 0.12 kg/L | Fixed volume-to-mass scenario assumption; not a field measurement |
| Base arrival rate | Capacity / 24 per slot times factors | Mean fill from empty around two days before service, before other effects |
| Arrival distribution | Gamma shape 2 | Nonnegative burstiness; no fitted Chennai coefficient |
| Weekends | 1.12 multiplier | Hypothetical demand effect |
| Intraday | 0.60 before 06:00; 1.25 at 10:00–20:00; 1 otherwise | Hypothetical demand shape |
| Annual seasonality | Cosine amplitude 0.12 | Illustrative annual fluctuation; not estimated from waste data |
| Zone/bin factor | Seeded lognormal, bin factor clipped 0.4–1.8 | Heterogeneity; not inferred from Census or POIs |
| Daily service opportunity | 06:00 local | Generator policy only |
| Due condition | At least 72% physical volume or 24 slots since service | Assumed threshold / max 48-hour service gap trigger |
| Missed due collection | 4% Bernoulli | Illustrative disruptions |
| Partial collection | 3% of successful collections; 45% removal | Otherwise 95% removal |
| Sensor fill noise | Normal 0, 2 percentage points | Clipped 0–100; truth overflow remains separate |
| Missing reading | 1.5% per bin-slot | Scheduled row retained with null measures and missing status |
| Stuck reading | 0.2% per bin-slot | Recorded status and depressed reading |
| Weight noise | Normal 0, 0.35 kg | Nonnegative, simulated measurement |
| Battery use | 0.003 percentage points per slot | Rare reset probability 0.002% per slot |
| Distance proxy | 5 + 0.35 km/successful stop per vehicle-day | Schematic proxy, not routed kilometres |
| Fleet/economy proxy | 50 assumed vehicles, 4.5 km/L | Used only in Phase 2 vehicle-day table |

State equation per bin-slot, in litres: `new_inventory = min(capacity, previous_inventory + arrivals) - removed`; `overflow = max(0, previous_inventory + arrivals - capacity)`. A successful collection removes from the capped inventory. The first slot starts from a seeded 5–35% initial fill. The full CSV has rounded numeric truth to five decimals. The test allows 0.001 L conservation tolerance across slots to account for rounding.

`2026` is a hypothetical scenario year using the 2026-09-22 OSM spatial snapshot as a placement template, not a historically correct 2026 reconstruction. The 2025 NASA grid is a separate real environmental reference and is not used as a realized future predictor or calibration coefficient. No municipal total is allocated to bins. Policy comparison, cost inference and forecasting are reserved for later phases.

The first full-year run had 501,938 bin-slots with positive simulated overflow (11.46% of 4,380,000 scheduled slots). This is a **model-calibration warning**, not an estimate of Chennai overflow. The assumed arrival rate and once-daily service opportunity may create unrealistic operational stress. Before comparing policies or reporting savings, later work must inspect overflow duration and volume, test lower/higher arrival and service-frequency scenarios, and calibrate against real collection volumes or a field pilot if obtained. Keep the uncalibrated baseline visible rather than tuning it silently.
