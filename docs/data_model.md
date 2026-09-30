# Analytical data model

Design contract only; no analytical tables or operational facts have been created.
## Table grains and cardinalities

| Table | Grain | Primary key | Expected rows |
|---|---|---|---|
| dim_source | One catalog source | source_id | 22 research sources; grows by acquisition |
| dim_date | One Asia/Kolkata calendar day | date_key | 365 per scenario year plus forecast history |
| dim_zone | One administrative area and boundary version | zone_key | State/city/zone/ward versions; counts unverified |
| dim_location | One versioned physical or hypothetical point | location_key | Bins plus depots/facilities/grid points |
| dim_waste_type | One compatible waste stream | waste_type_key | Small controlled vocabulary |
| dim_bin | One bin installation version | bin_key | 1000 scenario bins planned; actual registry unknown |
| dim_vehicle | One vehicle/specification version | vehicle_key | Scenario fleet size TBD |
| dim_facility | One receiving site/depot version | facility_key | Verified sites plus explicit hypothetical sites |
| dim_scenario | One frozen policy and assumption set | scenario_key | At least fixed/threshold/forecast designs later |
| dim_simulation_run | One scenario replication | simulation_run_id | Seeds x scenarios; no runs now |
| fact_bin_readings | One scheduled bin timestamp in one simulation run or observed stream | reading_id | 4380000 scheduled readings for baseline design |
| fact_routes | One executed or planned vehicle trip in a run | route_id | Vehicles x operating days x trips x runs |
| fact_route_stops | One ordered visit or facility stop on a route | stop_id | Visits plus depot/disposal stops |
| fact_route_legs | One directed travel leg between consecutive route stops | leg_id | Stops minus one per route |
| fact_collections | One service attempt for a bin and waste stream at a route stop | collection_id | Policy-dependent; no fixed count assumed |
| fact_vehicle_operations | One vehicle shift in a simulation run | operation_id | Vehicles x shifts x runs |
| fact_weather | One grid/station local day and source version | weather_id | Locations x days x source versions |
| fact_costs | One cost component for one vehicle operation and valuation version | cost_id | Operations x non-overlapping components |
| fact_waste_summary | One source geography/period/stream/measure and release | summary_id | Official records; unknown until acquired |
| fact_population | One census geography/reference date/source release | population_id | Census units x releases |
| bridge_facility_waste | One facility and accepted waste stream | facility_key, waste_type_key | Many-to-many facility compatibility |
| bridge_zone_crosswalk | One source-target boundary-version pair and allocation method | from_zone_key, to_zone_key, method | Many-to-many geographic mappings |

## Relationships

Each foreign key below is many-to-one from the child to the referenced unique parent. A parent may have zero or many children. Composite bridge keys implement explicit many-to-many relationships.

| Child FK | Parent key |
|---|---|
| dim_location.zone_key | dim_zone.zone_key |
| dim_bin.location_key | dim_location.location_key |
| dim_bin.waste_type_key | dim_waste_type.waste_type_key |
| dim_facility.location_key | dim_location.location_key |
| dim_simulation_run.scenario_key | dim_scenario.scenario_key |
| fact_bin_readings.simulation_run_id | dim_simulation_run.simulation_run_id |
| fact_bin_readings.bin_key | dim_bin.bin_key |
| fact_bin_readings.date_key | dim_date.date_key |
| fact_routes.simulation_run_id | dim_simulation_run.simulation_run_id |
| fact_routes.vehicle_key | dim_vehicle.vehicle_key |
| fact_routes.date_key | dim_date.date_key |
| fact_routes.start_facility_key | dim_facility.facility_key |
| fact_routes.end_facility_key | dim_facility.facility_key |
| fact_route_stops.route_id | fact_routes.route_id |
| fact_route_stops.location_key | dim_location.location_key |
| fact_route_stops.bin_key | dim_bin.bin_key |
| fact_route_legs.route_id | fact_routes.route_id |
| fact_route_legs.from_stop_id | fact_route_stops.stop_id |
| fact_route_legs.to_stop_id | fact_route_stops.stop_id |
| fact_collections.stop_id | fact_route_stops.stop_id |
| fact_collections.bin_key | dim_bin.bin_key |
| fact_collections.waste_type_key | dim_waste_type.waste_type_key |
| fact_vehicle_operations.simulation_run_id | dim_simulation_run.simulation_run_id |
| fact_vehicle_operations.vehicle_key | dim_vehicle.vehicle_key |
| fact_vehicle_operations.date_key | dim_date.date_key |
| fact_weather.location_key | dim_location.location_key |
| fact_weather.date_key | dim_date.date_key |
| fact_weather.source_id | dim_source.source_id |
| fact_costs.operation_id | fact_vehicle_operations.operation_id |
| fact_waste_summary.zone_key | dim_zone.zone_key |
| fact_waste_summary.waste_type_key | dim_waste_type.waste_type_key |
| fact_waste_summary.source_id | dim_source.source_id |
| fact_population.zone_key | dim_zone.zone_key |
| fact_population.source_id | dim_source.source_id |
| bridge_facility_waste.facility_key | dim_facility.facility_key |
| bridge_facility_waste.waste_type_key | dim_waste_type.waste_type_key |
| bridge_zone_crosswalk.from_zone_key | dim_zone.zone_key |
| bridge_zone_crosswalk.to_zone_key | dim_zone.zone_key |
| fact_routes.operation_id | fact_vehicle_operations.operation_id |

## Keys and nullability

Surrogate BIGINT keys decouple source IDs from changing vintages. VARCHAR event IDs are deterministic hashes/UUIDs from the documented natural event key; never depend on ingest order. PKs, natural keys, timestamps defining grain, data_origin and lineage_id are required. Foreign keys are required except route_stops.bin_key for depot/disposal stops. Simulated runs require a run key; future real data should use a documented observed-stream run record, never silently reuse a synthetic run.

Measured fields may be null only with a quality/status reason. Missing sensor messages have null measurements, not zero. Missing cost rates block complete cost totals. Do not coerce missing official statistics to zero. Intervals use [valid_from, valid_to); valid_to may be null for current records. Enforce no overlapping effective intervals and resolve historical dimension versions at event time. Repeated official publications are revisions, not additive new waste.

Fact_route_stops is the visit-grain table; fact_collections can have several attempts/streams per stop. Routes, stops and legs must agree on route ownership and sequence; collection bin must match its stop. Vehicle-shift rollups must reconcile to trips assigned to that shift; fact_routes.operation_id references the exact shift. Route vehicle, date and simulation run must agree with that operation record. Multiple trips per shift are allowed; shift totals are summed once.

## Origins and lineage

Allowed data_origin values: official (unmodified official observation), real (non-official observed/map record), derived (computed from documented inputs), proxy (substitute for intended measurement), synthetic (generated operational record), assumption (chosen scenario parameter). For modified official measurements use derived and retain source origin in lineage. Origins do not imply data quality.

Each lineage_id resolves to a manifest entry listing parent source_ids, parent artifact hashes, transformation and field origins. A synthetic reading at a real coordinate remains synthetic; dim_location.coordinate_origin separately preserves the coordinate's evidence. Capacity assumptions have capacity_origin. Derived scenario metrics must carry contains_synthetic=true in output manifests; do not promote them to observed results.

## Units and geography

Canonical mass kg, volume litres for bins / m3 for trucks, distance km, time minutes or explicitly named hours, temperature Celsius, rainfall mm and currency INR. 1 metric tonne = 1000 kg; 1 m3 = 1000 litres. Original source values and unit text are retained. Never infer whether an unqualified ton is metric. Monetary scaling (lakh/crore) is recorded before conversion. Do not mix cost price years.

UTC timestamps are stored; date_key reflects Asia/Kolkata service day. GIS storage carries CRS; display coordinates are WGS84. Store bin coordinates once in dim_location, rather than repeating them millions of times. An export can join latitude, longitude and zone to reading fields for inspection. Geographic hierarchy is not assumed to align across vintages.

## Avoid fanout

Never directly join readings to collections, weather and routes then sum measures. Aggregate each fact to the intended reporting grain first. Join weather by unique location/day/source through a versioned bin-to-weather assignment outside the BI fact path. Population and official tonnage stay at native geographic grain; do not repeat them per reading. Crosswalk weights must sum to 1 per source zone/method or report unallocated weight; area-weighted population is proxy, not census truth.

## BI serving model

Use daily bin, vehicle-day, route-trip and scenario-summary marts with conformed date/zone/bin/vehicle/scenario dimensions. Prefer single-direction one-to-many dimension-to-fact filters. Keep geographic crosswalks out of automatic bidirectional relationships. Import aggregates into Power BI; raw reading drill-through uses a bounded extract. Location/zone attributes can be flattened into serving dimensions to avoid ambiguous snowflake paths. Define weighted ratios from sums, not averages of percentages.

## Extensions deferred

Forecast output grain will be bin/run/issue_time/target_time/model_version/quantile; record availability time for features. Road graph edges use (u,v,key,snapshot); manifests reference graph artifacts. POI features use zone-or-bin/buffer/version. Holiday/event tables need date/geography/event identity. Latent simulation truth is isolated under synthetic/truth with access limited to evaluation scripts. These extensions are designed conceptually, not populated now.

## Two-city expansion — 25 September 2026

The initial design above remains historical context. `model_contract.json` now adds the city dimension and city FKs to the target design. The populated implementation differs from that planned model; use `two_city_model.md` and `data_dictionary_two_city.csv` for the actual DuckDB contract. Never join CHN/CBE using unqualified local IDs. City-specific serving tables carry city_id and global keys; dim_date is shared. The preserved Chennai-only files are not silently migrated.
