from pathlib import Path
import duckdb,json,time
R=Path(__file__).resolve().parents[2]
DB=R/'03_data/processed/waste.duckdb'
SQL=(R/'05_sql/phase2_marts.sql').read_text(encoding='utf-8').replace('{{ROOT}}',R.as_posix())
con=duckdb.connect(str(DB))
con.execute('SET threads=4')
con.execute("SET memory_limit='4GB'")
(R/'work/duckdb_tmp').mkdir(parents=True,exist_ok=True)
con.execute("SET temp_directory='"+(R/'work/duckdb_tmp').as_posix()+"'")
started=time.perf_counter();con.execute(SQL)
counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['fact_bin_readings','simulation_truth','collection_events','bin_daily_metrics','zone_daily_metrics','route_daily_metrics','vehicle_daily_metrics']}
plan=con.execute("EXPLAIN ANALYZE SELECT bin_id, AVG(fill_level_pct) FROM fact_bin_readings WHERE year=2026 AND month='01' AND fill_level_pct IS NOT NULL GROUP BY bin_id").fetchall()
(R/'14_outputs/reports/duckdb_query_plan.txt').write_text(plan[0][1],encoding='utf-8')
if 'Total Files Read: 1' not in plan[0][1]: raise AssertionError('Partition pruning failed')
report={'counts':counts,'build_seconds':round(time.perf_counter()-started,2),'database_bytes':DB.stat().st_size,'query':'January 2026 filter + selected columns + aggregation; see duckdb_query_plan.txt','execution':'local DuckDB'}
(R/'14_outputs/reports/duckdb_build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(report)
con.close()
