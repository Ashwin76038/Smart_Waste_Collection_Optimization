"""Generate DAX reconciliation query from the Phase 5 independent QA receipt."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[2]
mapping={'bins':'[Bin Count]','collected_kg':'1000 * [Total Waste Collected (t)]','daily_collected_kg':'SUM(fact_city_day[collected_kg])','fill_pct':'[Average Bin Fill %]','overflow_slot_pct':'[Overflow Slot %]','generated_l_per_bin_day':'[Generated L per Bin-Day]','overflow_days':'[Overflow Bin-Days]','completed_collections':'[Collections Completed]','early_success_pct':'[Early Collection % (simulated <35%)]','late_risk_attempt_pct':'[Late Risk Attempt %]','required_bins':'[Bins Requiring Collection]','high_priority_bins':'[High Priority Bins]','forecast_trigger_bins':'[Forecast-Triggered Bins]','baseline_km':'[Baseline Route Km]','optimized_km':'[Optimized Route Km]','saved_km':'[Distance Saved Km]','distance_reduction_pct':'[Distance Reduction %]','pilot_bins_serviced':'[Pilot Bins Serviced]','optimized_truck_km':'CALCULATE([Route Distance Km],fact_truck_route[method]="optimized")','reserved_truck_capacity_pct':'[Reserved Truck Capacity %]','fuel_saved_l':'[Fuel Saved L (assumed)]','fuel_cost_saved_inr_proxy':'[Fuel Cost Saved INR (proxy)]','travel_minutes_saved':'[Travel Minutes Saved]','modeled_spill_avoided_l':'[Modeled Spill Avoided L (24h)]','forecast_known_test_mae_pp':'[Forecast MAE (pp)]','forecast_near_full_recall_pct':'[Forecast Near-Full Recall %]'}
score=list(csv.DictReader((R/'12_powerbi/phase5_model/fact_forecast_score.csv').open()))
model=[x['model'] for x in score if x['city_id']=='CHN' and x['split']=='test' and x['evaluation_group']=='known_bins' and abs(float(x['mae_pct_points'])-8.16664987849616)<1e-6][0]
rows=[]
for row in csv.DictReader((R/'12_powerbi/phase5_model/kpi_reconciliation.csv').open()):
    city=row['city_id'];metric=row['metric']; expr=mapping[metric]
    actual=f'CALCULATE({expr}, dim_city[city_id]="{city}", dim_scenario[scenario]="base_3_trucks",fact_forecast_score[model]="{model}",fact_forecast_score[split]="test",fact_forecast_score[evaluation_group]="known_bins")'
    tol=max(float(row['tolerance']),1e-8)
    rows.append(f'ROW("Check", "{city}:{metric}", "Expected", {row["python_export_value"]}, "Actual", {actual}, "Tolerance", {tol:.10f})')
q='// Reconciles executed Desktop DAX to independently calculated export values.\nEVALUATE\nVAR Checks = UNION(\n'+',\n'.join(rows)+'\n)\nVAR Bad = FILTER(Checks, ISBLANK([Actual]) || ABS([Actual]-[Expected]) > [Tolerance])\nRETURN ROW("Checks",COUNTROWS(Checks),"Passed",COUNTROWS(Checks)-COUNTROWS(Bad),"Failed",COUNTROWS(Bad),"Failed checks",CONCATENATEX(Bad,[Check],", "),"Maximum absolute difference",MAXX(Checks,ABS([Actual]-[Expected])))'
(R/'12_powerbi/DESKTOP_RECONCILIATION.dax').write_text(q,encoding='utf-8')
print(f'Created 52-check Desktop reconciliation query; model={model}')
