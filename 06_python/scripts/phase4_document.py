"""Build evidence-linked Phase4 report, charts, dictionary and run receipt."""
from phase4_common import ROOT,CFG,GEO,FC,OPT,REPORT,MAPS,dump,format_prose
import json,hashlib,csv,platform,importlib.metadata
from datetime import datetime,timezone
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run():
    s=pd.read_csv(OPT/'scenario_comparison.csv');b=s[s.scenario=='base_3_trucks'].iloc[0]
    g=json.loads((GEO/'geospatial_summary.json').read_text());card=json.loads((FC/'model_card.json').read_text())
    p=pd.read_csv(OPT/'collection_priority.csv');ct=pd.read_csv(OPT/'counterfactual_totals.csv')
    ev=pd.read_csv(FC/'forecast_evaluation.csv');chosen=ev[(ev.split=='test')&(ev.model=='ridge')&(ev.group=='known_bins')].iloc[0]
    simple=ev[(ev.split=='test')&(ev.model==card['best_simple'])&(ev.group=='known_bins')].iloc[0]
    chart=ROOT/'14_outputs/charts/phase4';chart.mkdir(parents=True,exist_ok=True)
    good=s[s.scenario.isin(['base_3_trucks','trigger_70','trigger_90','demand_plus20'])]
    fig,ax=plt.subplots(figsize=(9,4.8));x=np.arange(len(good));ax.bar(x-.18,good.baseline_km,.36,label='Matched nearest-neighbor baseline',color='#7d8995');ax.bar(x+.18,good.optimized_km,.36,label='OR-Tools feasible solution',color='#087f8c');ax.set_xticks(x,['80% base','70% trigger','90% trigger','Demand +20%']);ax.set(ylabel='Total fleet road distance (km)',title='Synthetic single-trip scenarios · three hypothetical trucks');ax.legend();fig.tight_layout();fig.savefig(chart/'route_comparison.png',dpi=150);plt.close(fig)
    totals=ct.pivot(index='scenario',columns='method',values='overflow_l');order=good.scenario.tolist();totals=totals.loc[order]
    fig,ax=plt.subplots(figsize=(9,4.8));ax.bar(x-.18,totals.baseline,.36,label='Baseline order',color='#7d8995');ax.bar(x+.18,totals.optimized,.36,label='Optimized distance order',color='#b35634');ax.set_xticks(x,['80% base','70% trigger','90% trigger','Demand +20%']);ax.set(ylabel='24-hour simulated spill (L)',title='Shorter distance does not guarantee lower overflow');ax.legend();fig.tight_layout();fig.savefig(chart/'overflow_tradeoff.png',dpi=150);plt.close(fig)
    monthly=pd.read_parquet(FC/'test_predictions.parquet');monthly['target_month']=monthly.target_time_utc.dt.to_period('M').astype(str) # use IST target month below
    monthly['target_month']=(monthly.target_time_utc+pd.Timedelta(hours=5,minutes=30)).dt.to_period('M').astype(str)
    monthly['absolute_error_pp']=abs(monthly.prediction_pct-monthly.target_fill_pct)
    monthly.groupby(['target_month','group'],as_index=False).agg(rows=('bin_id','size'),mae_pct_points=('absolute_error_pp','mean')).to_csv(FC/'monthly_test_metrics.csv',index=False)
    rows=[]
    for scenario,r in totals.iterrows():rows.append({'scenario':scenario,'baseline_overflow_l':r.baseline,'optimized_overflow_l':r.optimized,'overflow_l_avoided_modelled':r.baseline-r.optimized,'data_origin':'synthetic','scope':'24h isolated intervention; all60 pilot bins; no other collections'})
    pd.DataFrame(rows).to_csv(OPT/'overflow_comparison.csv',index=False)
    report=f'''# Phase 4 — advanced analytics evidence report

Completed 2026-09-24. **Simulation demonstration; no realized Chennai savings.** Frozen dispatch: 23 September 2026 at08:00 IST. Real OSM/GCC geography; hypothetical bins, fleet, facility and demand. Read the [methodology](../../docs/phase4_methodology.md) for assumptions and rerun commands.

## Decision and results
The model identifies {int(p.required.sum())} bins requiring attention among1,000: {int((p.dispatch_status=='pilot_required').sum())} in the routing pilot, {int((p.dispatch_status=='required_outside_pilot').sum())} outside its scope, and {int((p.dispatch_status=='access_review').sum())} requiring access review. It does not claim citywide collection coverage.

For the geographically selected60-bin pilot, all{int(b.required_bins)} required bins are visited once by three trucks. Total road distance falls from **{b.baseline_km:.2f} to {b.optimized_km:.2f} km**, a **{b.distance_reduction_pct:.2f}%** improvement against a feasible deterministic nearest-neighbor baseline with the same stops, capacities and shift limits. This is a bounded solver result, not proof of the global optimum and not a comparison with observed municipal routes.

Estimated vehicle time falls by **{b.vehicle_hours_saved*60:.1f} minutes**. At the explicit4.5km/L assumption, fuel savings are **{b.fuel_l_saved_assumed:.2f} L**. Historical retail-price savings are **INR{b.fuel_cost_inr_saved_historical_proxy:.2f}** at Chennai IOCL diesel INR92.39/L effective1March2026 (S23); this is not a September procurement price. Tailpipe fossil-CO2 savings are **{b.tailpipe_co2_kg_saved_proxy:.2f} kg** using S24's US factor proxy. No wage, idling/PTO fuel, lifecycle emissions, annualized cash savings or realized benefit is asserted.

## Forecasting
The observed-only ridge regression was chosen on July–August validation, before September–December scoring. It predicts next-day04:00 fill from information available at08:00 today (20hours), before the next scheduled06:00 collection. Training uses January–June; the selected model is refitted through31August. Two hundred bins are held out from fitting and model selection.

Known-bin test MAE is **{chosen.mae_pct_points:.2f} percentage points**, RMSE **{chosen.rmse_pct_points:.2f}**, versus **{simple.mae_pct_points:.2f}** MAE for the best simple baseline (seven-day average). Unseen-bin MAE is8.19points. MAPE is omitted because near-empty bins make it unstable; WAPE is included. Near-full recall is only{chosen.near_full_recall:.1%}, so a low overall error does not establish a reliable overflow alarm.

The nominal90% empirical interval covers **{card['test_interval_coverage90']:.2%}** of test observations, below nominal. It is a validation-residual risk band, not a calibrated overflow probability or guaranteed conformal interval. The refitted model can have different residuals; repeated bins, sensor noise and one synthetic year limit inference. Future policy changes require a new state-transition forecast. No future truth, annual summary or generator demand factor enters dispatch.

![Forecast errors](../../09_forecasting/phase4/forecast_test_mae.png)

## Geography and accessibility
The derived network has{g['all_graph_nodes']:,} nodes and{g['directed_edges']:,} directed edges. {g['network_accessible_within100m']} of1,000 bins snap within100m to its largest strongly connected component;{g['inaccessible_bins']} do not. All1,000 assigned ward IDs intersect their official polygons. EPSG32644 is used for local proximity calculations.

Among1,507 mapped POIs, {g['poi_within250m_hypothetical_bin_pct']:.1f}% lie within250m and {g['poi_within500m_hypothetical_bin_pct']:.1f}% within500m of a hypothetical bin. These are straight-line OSM-POI proxies, not resident access or a municipal service-coverage estimate. Commercial proximity uses827 mapped restaurant/market/shop nodes; residential proximity uses1,025 closed OSM land-use ways. Missing mapped activity is not evidence of absent activity. Census2011 ward numbers remain unjoined to current wards.

Interactive maps: [geospatial context](../maps/phase4_geospatial.html) and [baseline/optimized routes](../maps/phase4_routes.html). Toggle layers and inspect tooltips. Basemaps/CDN scripts require internet. The hotspot map is a retrospective full-year simulation and is not a dispatch feature.

## Priority and scenario tradeoffs
No weighted composite is used. Current-fill risk, missing/stale telemetry, long service gap and upper-forecast risk form documented lexicographic tiers. A bin meeting any rule is mandatory for this scenario; ranking never silently removes it from the VRP. Threshold80%, gap48hours and stale6hours are policy assumptions, not empirically optimal or municipal mandates. A27-combination sensitivity grid covers70/80/90% triggers,80/90/95% uncertainty bands and36/48/72-hour gaps.

The base required load reserves each selected bin's full capacity:25,160L. Thus one12,000L truck or two24,000L trucks cannot serve it in a single trip. This is conservative planning infeasibility, not proof that actual waste volume exceeds two trucks. Truck-unavailable inherits this constraint. Multi-trip unloading and smaller-risk-reserve policies are future extensions. At70% the pilot requires46 bins; at90%,27; the+20% demand stress requires48. Higher thresholds reduce work but leave more bins unserved; they are not a free efficiency gain.

![Route comparison](../charts/phase4/route_comparison.png)

## Overflow counterfactual
The isolated evaluator replays the same latent arrivals and initial inventories for all60 pilot bins over24hours. Arrivals accrue uniformly within each two-hour interval; a visit removes95% after four minutes. There are no other collections in the horizon. It recomputes inventory/spill and checks mass balance; it never reuses the unchanged baseline fill trace after an intervention.

Base optimized order reduces modelled spill by **{totals.loc['base_3_trucks','baseline']-totals.loc['base_3_trucks','optimized']:.2f} L**. But the70% trigger and+20% demand scenarios increase spill relative to their matched baseline order. Distance is the solver objective, not overflow or collected tonnes. Report terminal stock and collected volume alongside spill; earlier collection may remove less waste and allow later overflow. These outcomes do not establish avoided real overflow, comparative policy superiority or a sustainable daily schedule.

![Overflow tradeoff](../charts/phase4/overflow_tradeoff.png)

## Validation and readiness
All31 pytest checks passed after implementing Phase4, including every saved matrix path, exact required-bin coverage, no duplicate visits, depot returns, volume/payload/shift constraints, forecast availability, metric recomputation, factor equations and counterfactual mass balance. Original asset hashes remain checked. The final verification receipt records the rerun status.

**Share with caveats:** suitable for a portfolio simulation and review of methods. Deployment needs real inventory, observed histories, verified truck/depot/receiving-site access, local restrictions, service times, fuel calibration and monitored trials. Missing OSM restrictions cannot be tested into existence. No route-optimization significance test is performed on this one-date deterministic scenario. Power BI, cloud execution and final presentation remain outside this phase.

## Source evidence
- S09: preserved Geofabrik Southern Zone OSM2026-09-22 PBF, ©OpenStreetMap contributors, ODbL.
- S08: acquired official GCC ward GeoJSON; effective boundary date unverified.
- S23: [Lok Sabha Q3336,12March2026, Annexures I–II](https://sansad.in/getFile/loksabhaquestions/annex/187/AU3336_YCAaF0.pdf?source=pqals), PPAC historical Chennai diesel reference.
- S24: [US EPA diesel equivalency methodology](https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references),10,180gCO2/USgallon, divided by3.785411784L/USgallon, rounded to2.689kg/L.
- [OR-Tools capacity constraints](https://developers.google.com/optimization/routing/cvrp) and [time dimensions](https://developers.google.com/optimization/routing/vrptw).
'''
    (REPORT/'phase4_advanced_analytics_report.md').write_text(format_prose(report),encoding='utf-8')
    # Field-level dictionary for bounded handoff tables; raw road schema documented in methodology.
    files=[FC/'dispatch_forecasts.csv',FC/'forecast_evaluation.csv',GEO/'bin_spatial_features.csv',OPT/'collection_priority.csv',OPT/'scenario_comparison.csv',OPT/'route_summary.csv',OPT/'route_stops.csv',OPT/'counterfactual_bin_results.csv']
    dictionary=[]
    for path in files:
        frame=pd.read_csv(path)
        for name,dtype in frame.dtypes.items():
            unit='identifier/category/boolean'
            if 'pct' in name or name.endswith('_pp'):unit='percentage points or percent as field name indicates'
            elif name.endswith('_km'):unit='kilometres'
            elif name.endswith('_m'):unit='metres'
            elif 'seconds' in name:unit='seconds'
            elif 'hours' in name:unit='hours'
            elif 'minutes' in name:unit='minutes'
            elif '_inr' in name:unit='Indian rupees, historical proxy'
            elif name.endswith('_l') or '_l_' in name:unit='litres'
            elif '_kg' in name:unit='kilograms'
            elif 'latitude' in name or 'longitude' in name:unit='WGS84 decimal degrees'
            elif 'utc' in name:unit='UTC timestamp'
            dictionary.append({'table':path.stem,'field':name,'dtype':str(dtype),'unit':unit,'source_file':path.relative_to(ROOT).as_posix(),'operational_origin':'synthetic; geographic features derived from S08/S09; factors explicit proxies'})
    pd.DataFrame(dictionary).to_csv(ROOT/'docs/data_dictionary_phase4.csv',index=False)
    versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','duckdb','scipy','scikit-learn','joblib','matplotlib','folium','networkx','shapely','pyproj','osmium','ortools','pytest']}
    (ROOT/'requirements-phase4.txt').write_text('# Direct versions used; install with prior phase requirements. Clean install not verified.\n'+'\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n',encoding='utf-8')
    artifacts=[]
    for folder in [GEO,FC,OPT,MAPS,chart]:
        for path in sorted(folder.glob('*')):
            if path.is_file():artifacts.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    dump(REPORT/'phase4_run_manifest.json',{'created_at_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'versions':versions,'config':CFG,'artifacts':artifacts,'solver_reproducibility':'5-second wall-clock budget can change solution across hardware; saved routes authoritative for this run','forecast_reproducibility':'Fixed synthetic source and chronological splits; deterministic ridge; no random split','raw_sources':'02_research/acquisition_manifest.csv'})
    print('Phase4 report, charts, dictionary, requirements and run manifest written')
if __name__=='__main__':run()
