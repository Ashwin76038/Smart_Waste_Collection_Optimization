"""Inspectible comparison, descriptive diagnostics, quality profile and source context."""
from phase4_common import PROJECT_ROOT as ROOT,dump
import pandas as pd,numpy as np,duckdb,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run():
    report=ROOT/'14_outputs/reports/city_expansion';out=ROOT/'14_outputs/tables/city_comparison';charts=ROOT/'14_outputs/charts/city_comparison';charts.mkdir(parents=True,exist_ok=True)
    cbe=ROOT/'cities/CBE'
    total=pd.read_csv(cbe/'10_optimization/phase4/counterfactual_totals.csv').pivot(index='scenario',columns='method',values='overflow_l').reset_index()
    total['overflow_l_avoided_modelled']=total.baseline-total.optimized;total['city_id']='CBE';total['city_name']='Coimbatore';total['data_origin']='synthetic';total.to_csv(cbe/'10_optimization/phase4/overflow_comparison.csv',index=False)
    predictions=pd.read_parquet(cbe/'09_forecasting/phase4/test_predictions.parquet');predictions['target_month']=(predictions.target_time_utc+pd.Timedelta(hours=5,minutes=30)).dt.to_period('M').astype(str);predictions['ae']=abs(predictions.prediction_pct-predictions.target_fill_pct)
    monthly=predictions.groupby(['target_month','group'],as_index=False).agg(n=('bin_id','size'),mae_pct_points=('ae','mean'));monthly['city_id']='CBE';monthly['city_name']='Coimbatore';monthly.to_csv(cbe/'09_forecasting/phase4/monthly_test_metrics.csv',index=False)
    # Normalize shared counterfactual export names before loading comparison layer.
    total=total.rename(columns={'baseline':'baseline_overflow_l','optimized':'optimized_overflow_l'});total.to_csv(cbe/'10_optimization/phase4/overflow_comparison.csv',index=False)
    from build_two_city import run as build
    build()
    from run_city_sql import run as queries
    queries()
    c=duckdb.connect(str(ROOT/'03_data/processed/two_city/two_city.duckdb'),read_only=True)
    daily=c.execute('SELECT * FROM city_daily_metrics ORDER BY city_id,service_date_local').df();summary=pd.read_csv(out/'01_city_comparison_BOTH.csv').set_index('city_id');routes=pd.read_csv(out/'05_routing_scenarios_BOTH.csv');base=routes[routes.scenario=='base_3_trucks'].set_index('city_id');evals=pd.read_csv(out/'07_forecast_comparison_BOTH.csv');diagnostics=[]
    for cid,g in daily.groupby('city_id'):
        for metric in ['generated_l_per_bin_day','mean_fill_pct','overflow_slot_pct','collections_per_bin_day']:
            x=g[metric];diagnostics.append({'city_id':cid,'metric':metric,'n_city_days':len(x),'mean':x.mean(),'median':x.median(),'std':x.std(),'q25':x.quantile(.25),'q75':x.quantile(.75),'skewness':x.skew(),'lag1_autocorrelation':x.autocorr(),'inference':'descriptive only; generator assumptions differ; no empirical city-effect test'})
    pd.DataFrame(diagnostics).to_csv(ROOT/'07_statistics/two_city_descriptive_diagnostics.csv',index=False)
    # Important-table profiles: PK duplicates bound exact whole-row duplicates.
    contracts={'dim_city':['city_id'],'dim_bin':['bin_key'],'dim_zone':['zone_key'],'dim_location':['location_key'],'fact_bin_readings':['reading_key'],'fact_collections':['collection_key'],'fact_weather':['city_id','date'],'bin_daily_metrics':['bin_key','service_date_local'],'zone_daily_metrics':['zone_key','service_date_local'],'city_daily_metrics':['city_id','service_date_local'],'fact_routes':['route_key'],'forecast_evaluation':['city_id','split','group','model'],'collection_priority':['bin_key']}
    profiles=[]
    for table,keys in contracts.items():
        cols=c.execute('DESCRIBE '+table).fetchall();names=[x[0] for x in cols]
        null_sql=','.join('count(*) FILTER(WHERE "'+n+'" IS NULL)' for n in names)
        row=c.execute('SELECT count(*),'+null_sql+' FROM '+table).fetchone();n=row[0]
        keyexpr='('+','.join('"'+x+'"' for x in keys)+')';duplicates=c.execute(f'SELECT count(*)-count(DISTINCT {keyexpr}) FROM {table}').fetchone()[0]
        profiles.append({'table':table,'rows':n,'columns':len(cols),'types':{x[0]:x[1] for x in cols},'pk':keys,'duplicate_keys':duplicates,'duplicate_rows_upper_bound':duplicates,'duplicate_method':'A duplicate whole row duplicates its primary key; zero PK duplicates proves zero identical rows','missing_pct':{name:100*row[i+1]/n for i,name in enumerate(names)}})
    ranges=c.execute('''SELECT city_id,min(timestamp_utc) AS first_utc,max(timestamp_utc) AS last_utc,min(fill_level_pct) AS min_fill,max(fill_level_pct) AS max_fill,count(DISTINCT sensor_status) AS sensor_categories,count(DISTINCT collection_status) AS collection_categories FROM fact_bin_readings GROUP BY city_id''').df();ranges.to_csv(report/'event_ranges.csv',index=False)
    dump(report/'data_profile.json',profiles)
    c.close()
    # Small exact-typed Sandbox sample; no paid service or cloud execution.
    upload=daily.copy();integer=['bins','successful_collections','missed_collections','scheduled_readings','received_readings','overflow_slots']
    for col in integer:upload[col]=upload[col].astype('int64')
    upload['service_date_local']=pd.to_datetime(upload.service_date_local).dt.strftime('%Y-%m-%d');upload.to_csv(ROOT/'11_cloud/two_city_daily_upload.csv',index=False)
    pd.DataFrame([{'city_id':'CBE','metric':'population','value':1601000,'unit':'persons, rounded from16.01lakh','reference_period':'2011 as reported','source_id':'S27','page':17,'data_origin':'official','limitation':'Rounded historical city profile; not current population or aligned ward denominator'}, {'city_id':'CBE','metric':'area','value':257,'unit':'km2','reference_period':'historical plan profile; effective date not verified','source_id':'S27','page':17,'data_origin':'official','limitation':'Not used to rescale acquired ward geometry'}, {'city_id':'CBE','metric':'population_density_reference_proxy','value':1601000/257,'unit':'persons/km2','reference_period':'mixed historical profile references','source_id':'S27','page':17,'data_origin':'proxy','limitation':'Rounded population divided by reported area; not current density; not used for demand'}]).to_csv(out/'coimbatore_reference_context.csv',index=False)
    # Two purposeful comparison figures, keeping scale and origin explicit.
    colors={'CHN':'#0072B2','CBE':'#D55E00'}
    fig,axes=plt.subplots(1,2,figsize=(11,4.7))
    for ax,metric,label in zip(axes,['generated_l_per_bin_day','overflow_slot_pct'],['Generated litres per bin-day','Physical overflow slots (%)']):
        for cid,g in daily.groupby('city_id'):
            ax.plot(g.service_date_local,g[metric].rolling(7,min_periods=7).mean(),label=g.city_name.iloc[0],color=colors[cid])
        ax.set_ylabel(label);ax.tick_params(axis='x',rotation=25);ax.legend();ax.set_xlabel('Hypothetical2026;7-day trailing mean')
    fig.suptitle('Synthetic city scenarios: different assumed demand, not observed city effects');fig.tight_layout();fig.savefig(charts/'normalized_city_trends.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for i,cid in enumerate(['CHN','CBE']):
        axes[0].bar([i-.17,i+.17],[base.loc[cid,'baseline_km'],base.loc[cid,'optimized_km']],width=.32,color=['#7b8792',colors[cid]])
        own=evals[(evals.city_id==cid)&(evals.split=='test')&(evals['group']=='known_bins')].set_index('model')
        axes[1].bar([i-.17,i+.17],[own.loc['moving_average7','mae_pct_points'],own.loc['ridge','mae_pct_points']],width=.32,color=['#7b8792',colors[cid]])
    for ax in axes:ax.set_xticks([0,1],['Chennai','Coimbatore'])
    axes[0].set(ylabel='Fleet road distance (km)',title='Grey: matched baseline; color: optimized')
    axes[1].set(ylabel='Test MAE (fill percentage points)',title='Grey: seven-day mean; color: local ridge')
    fig.suptitle('Separate synthetic pilots and independently fitted forecasts');fig.tight_layout();fig.savefig(charts/'routes_forecasts.png',dpi=150);plt.close(fig)
    lines=['| Metric | Chennai | Coimbatore |','|---|---:|---:|']
    for label,col in [('Hypothetical bins','bin_count'),('Scheduled readings','scheduled_readings'),('Mean observed fill (%)','average_observed_fill_pct'),('Generated L/bin-day','generated_l_per_bin_day'),('Overflow slots (%)','overflow_slot_pct'),('Successful services/bin-day','collections_per_bin_day'),('Early successful collections (%)','early_success_pct')]:
        lines.append(f'| {label} | {summary.loc["CHN",col]:,.3f} | {summary.loc["CBE",col]:,.3f} |')
    text='''# Chennai and Coimbatore — expansion evidence

Completed 2026-09-25. **All operational comparisons are synthetic scenarios, not official municipal performance.** Chennai remains the preserved original study; Coimbatore adds the user's home city and a second geographic test of the same methods. No Phase5 dashboard or final presentation was created.

## Coverage and compatible metrics

'''+ '\n'.join(lines)+f'''

The combined canonical fact has **6,570,000 readings**, 1,500 hypothetical bins and300 ward identifiers qualified by city. Both use365days and12scheduled readings/day. Compare normalized rates; annual total generated waste is not a fair ranking with twice as many Chennai bins. Physical overflow uses latent simulation truth, not fill clipped at100%. Early service means successful collection below35% true pre-service fill, an exploratory diagnostic.

![Normalized scenario trends](../../charts/city_comparison/normalized_city_trends.png)

## Independent forecasts and routes

Coimbatore has its own fitted ridge model: known-bin test MAE7.69percentage points versus20.57 for its best simple baseline. Chennai remains8.17 versus19.65. The same time split, target horizon, baseline definitions and every-fifth-bin holdout are used, but separate training and different synthetic scenarios mean the score gap is not evidence of superior city operations. Nominal90% residual-band coverage is88.22% in Coimbatore and88.45% in Chennai, below nominal. Neither is a calibrated overflow probability.

The Coimbatore60-bin geographic pilot selects34required bins. Three hypothetical trucks serve all34once: **{base.loc['CBE','baseline_km']:.2f}km → {base.loc['CBE','optimized_km']:.2f}km**, saving **{base.loc['CBE','km_saved']:.2f}km ({base.loc['CBE','distance_reduction_pct']:.2f}%)**. Chennai's preserved pilot serves36bins:57.34→45.50km (20.66%). Compare each matched baseline-relative improvement; different layouts/stops prohibit ranking real city efficiency from raw route lengths. No route connects cities. One/two-truck base cases exceed the conservative full-bin volume reserve in both cities.

Coimbatore's base estimates save{base.loc['CBE','travel_hours_saved']*60:.2f}vehicle-minutes and{base.loc['CBE','fuel_l_saved_assumed']:.2f}L at assumed4.5km/L. Cost is **INR{base.loc['CBE','fuel_cost_inr_saved_historical_proxy']:.2f} using Chennai's historical common-price proxy**, not an acquired Coimbatore diesel price. Fossil tailpipe CO2 proxy is{base.loc['CBE','tailpipe_co2_kg_saved_proxy']:.2f}kg. No realized/annualized savings, wage savings or local certified emission factor is claimed.

Coimbatore's isolated24-hour replay reduces base spill by{total.loc[total.scenario=='base_3_trucks','overflow_l_avoided_modelled'].iloc[0]:.2f}L, but terminal stock and removed volume also change. This evaluator has no other collections within24hours, so it is not a recurring policy result. Chennai's stress-scenario spill tradeoffs remain unchanged and must remain visible.

![Route and forecast comparisons](../../charts/city_comparison/routes_forecasts.png)

## Sources and geographic limits

Coimbatore uses100real ward geometries distributed by OpenCity (S25/S26;2024per metadata, upstream livingatlas.esri.in). They are not certified current municipal polygons. The official CCMC zone-map PDF (S28), sanitation-plan PDF (S27), and NGT-hosted CCMC filing (S29) are archived separately. Public source does not imply current operational ground truth. S27 page17 reports rounded2011population16.01lakh and area257km²; the context table preserves those references and an explicitly proxy ratio, not a current population/density input. Scanned S29 waste/facility quantities were not loaded as numeric facts without verification.

Real Coimbatore geography includes258,080graph nodes,561,940directed edges,82,523road nodes inside acquired wards and2,662mapped POI features. All500hypothetical bins intersect assigned wards and pass100mnetwork-access screening. Missing OSM truck restrictions and hypothetical depot/receiving access still prevent deployment certification. The independent centers are approximately13.08N80.27E(Chennai) and11.02N76.96E(Coimbatore).

Coimbatore POI coverage includes ways/morecategories while the preserved Chennai extract is narrower/node-only: **raw POI counts and coverage percentages are not compared**. NASA2025grid weather is retained separately from hypothetical2026operations. Official current ward population, true bin inventory, sensors, collection/GPS logs, truck roster, receiving entrances and local procurement costs remain gaps.

## Statistical decision

No Chennai-versus-Coimbatore significance test is reported. Coimbatore has500bins versus1,000, a distinct random seed and an explicit0.9demand-factor multiplier. Apparent mean differences are partly encoded by design. Two synthetic cities, one seed per city and repeated correlated bin/day observations are not independent evidence for a real city effect. `07_statistics/two_city_descriptive_diagnostics.csv` reports365city-days per city, moments, quartiles, skewness and lag-one autocorrelation. These support descriptive comparison, not causal or population inference. Route comparisons use a single fixed planning date; no t-test on individual route legs is justified.

## Model, quality and handoff

Use the [city-aware model contract](../../../docs/two_city_model.md) and [Power BI city-slicer specification](../../../12_powerbi/CITY_COMPARISON_SPEC.md). City-specific and both-city SQL outputs are in `14_outputs/tables/city_comparison/`; eight queries execute with all three filters. Prepared exports have explicitcity_id/globalkeys. A CBE/January predicate reads1of24Parquet files. Original ChennaiSQL still targets the unchanged legacy database.

Final executed tests and preservation results are in `verification.json`; field types/null percentages are in `data_profile.json`. All original raw snapshots remain manifest-linked. `chennai_preservation.json` covers120prior data/output files. This expansion is ready as a documented simulation, with real-data deployment gaps explicit. Stop before Phase5.
'''
    from phase4_common import format_prose
    (report/'comparison_report.md').write_text(format_prose(text),encoding='utf-8')
    (ROOT/'07_statistics/two_city_statistical_scope.md').write_text('''# Statistical scope: Chennai versus Coimbatore

Decision: do not run an inferential city-difference test. The user explicitly ruled out tests that merely recover generator assumptions. Both cities have 365 simulated days, but unequal bin counts (1,000/500), different fixed seeds, geographically distinct bin placements and a Coimbatore demand multiplier of 0.9. Repeated bin slots are autocorrelated and nested in one fixed parameterized scenario. Nominal millions of rows are not millions of independent city replications.

The companion CSV reports per-city daily means, median, SD, quartiles, skewness and lag-one autocorrelation for compatible normalized metrics. These are descriptive distribution/dependence checks. No p-value, city-effect confidence interval or causal claim is attached. A normal-looking histogram would not solve the identification problem. Forecast metrics describe separate synthetic model evaluations, not observed city predictability. One-date route reductions are paired deterministic scenario arithmetic, not a statistical sample of service days.

For later justified inference: acquire comparable real histories with aligned bin capacity/service policy, dates and geographic coverage; predeclare the estimand; account for clustering/serial dependence and confounders. Alternatively, run multiple independent demand-seed replications within the simulator and label conclusions as simulation-policy effects, never empirical city effects. No such replication study was performed in this expansion.
''',encoding='utf-8')
    print('Comparison report, two charts, distribution checks, source context and quality profiles written')
if __name__=='__main__':run()
