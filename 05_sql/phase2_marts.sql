-- Phase 2 serving model. All operational facts are synthetic scenarios.
CREATE OR REPLACE VIEW fact_bin_readings AS
SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/fact_bin_readings/year=*/month=*/*.parquet', hive_partitioning=true);
CREATE OR REPLACE VIEW simulation_truth AS
SELECT * FROM read_parquet('{{ROOT}}/03_data/synthetic/truth/year=*/month=*/*.parquet', hive_partitioning=true);
CREATE OR REPLACE VIEW interim_readings AS
SELECT * FROM read_parquet('{{ROOT}}/03_data/interim/readings/year=*/month=*/*.parquet', hive_partitioning=true);
CREATE OR REPLACE TABLE dim_bin AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/dim_bin.parquet');
CREATE OR REPLACE TABLE dim_zone_ward AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/dim_zone_ward.parquet');
CREATE OR REPLACE TABLE census_chennai_2011_native AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/census_chennai_2011_native.parquet');
CREATE OR REPLACE TABLE weather_chennai_grid_2025 AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/weather_chennai_grid_2025.parquet');
CREATE OR REPLACE TABLE osm_road_nodes_chennai AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/osm_road_nodes_chennai.parquet');
CREATE OR REPLACE TABLE osm_road_segments_chennai AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/osm_road_segments_chennai.parquet');
CREATE OR REPLACE TABLE osm_poi_nodes_chennai AS SELECT * FROM read_parquet('{{ROOT}}/03_data/processed/osm_poi_nodes_chennai.parquet');
CREATE OR REPLACE TABLE collection_events AS
SELECT i.reading_id AS collection_id, i.bin_id, i.zone_id,
       CAST(i.service_date_local AS DATE) AS service_date_local,
       i.timestamp_utc AS attempted_at_utc,
       i.collection_status,
       t.removed_l_true * 0.12 AS collected_kg,
       t.inventory_l_true * 0.12 AS residual_kg,
       'synthetic' AS data_origin
FROM interim_readings i
JOIN simulation_truth t USING (reading_id)
WHERE i.collection_status IN ('collected','partial','missed');
CREATE OR REPLACE TABLE bin_daily_metrics AS
SELECT r.bin_id, CAST(r.service_date_local AS DATE) AS service_date_local,
       b.zone_id,
       COUNT(*) AS scheduled_readings,
       COUNT(r.fill_level_pct) AS received_readings,
       COUNT(*) FILTER (WHERE r.sensor_status='missing') AS missing_readings,
       AVG(r.fill_level_pct) AS mean_observed_fill_pct,
       MAX(r.fill_level_pct) AS max_observed_fill_pct,
       SUM(t.arrivals_l_true) AS arrivals_l_simulated,
       SUM(t.overflow_l_true) AS overflow_l_simulated,
       SUM(t.removed_l_true) * 0.12 AS collected_kg_simulated,
       COUNT(*) FILTER (WHERE r.collection_status IN ('collected','partial')) AS successful_collections,
       COUNT(*) FILTER (WHERE r.collection_status='missed') AS missed_collections,
       'synthetic' AS data_origin
FROM fact_bin_readings r
JOIN simulation_truth t USING (reading_id)
JOIN dim_bin b ON r.bin_id=b.bin_id
GROUP BY r.bin_id, CAST(r.service_date_local AS DATE), b.zone_id;
CREATE OR REPLACE TABLE zone_daily_metrics AS
SELECT zone_id, service_date_local,
       COUNT(*) AS bins,
       SUM(scheduled_readings) AS scheduled_readings,
       SUM(received_readings) AS received_readings,
       SUM(missing_readings) AS missing_readings,
       SUM(arrivals_l_simulated) AS arrivals_l_simulated,
       SUM(overflow_l_simulated) AS overflow_l_simulated,
       SUM(collected_kg_simulated) AS collected_kg_simulated,
       SUM(successful_collections) AS successful_collections,
       SUM(missed_collections) AS missed_collections,
       'synthetic' AS data_origin
FROM bin_daily_metrics GROUP BY zone_id, service_date_local;
CREATE OR REPLACE TABLE route_daily_metrics AS
SELECT service_date_local,
       1 + ((TRY_CAST(zone_id AS INTEGER)-1) % 50) AS vehicle_id,
       CONCAT(CAST(service_date_local AS VARCHAR), '_', CAST(1 + ((TRY_CAST(zone_id AS INTEGER)-1) % 50) AS VARCHAR)) AS route_id,
       COUNT(*) AS service_attempts,
       COUNT(*) FILTER (WHERE collection_status IN ('collected','partial')) AS successful_stops,
       COUNT(*) FILTER (WHERE collection_status='missed') AS missed_stops,
       SUM(collected_kg) AS collected_kg_simulated,
       5.0 + 0.35 * COUNT(*) FILTER (WHERE collection_status IN ('collected','partial')) AS distance_km_assumed,
       'assumption' AS distance_origin,
       'synthetic' AS data_origin
FROM collection_events
GROUP BY service_date_local, 1 + ((TRY_CAST(zone_id AS INTEGER)-1) % 50);
CREATE OR REPLACE TABLE vehicle_daily_metrics AS
SELECT service_date_local, vehicle_id,
       COUNT(*) AS routes,
       SUM(service_attempts) AS service_attempts,
       SUM(successful_stops) AS successful_stops,
       SUM(collected_kg_simulated) AS collected_kg_simulated,
       SUM(distance_km_assumed) AS distance_km_assumed,
       SUM(distance_km_assumed) / 4.5 AS diesel_l_assumed,
       'synthetic' AS data_origin
FROM route_daily_metrics GROUP BY service_date_local,vehicle_id;
