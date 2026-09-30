"""Observed-only transparent dispatch rules; no arbitrary weighted composite."""
from phase4_common import ROOT,CFG,GEO,FC,OPT,dump
import pandas as pd,numpy as np

def prioritize(frame,trigger=80,interval=90,gap=48,demand_multiplier=1.0):
    d=frame.copy()
    # Stress forecast increment, not current stored volume. A scenario, not retrained accuracy.
    d['risk_upper_pct']=(d.current_fill_pct+(d[f'upper{interval}_pct']-d.current_fill_pct).clip(lower=0)*demand_multiplier).clip(0,100)
    d['current_trigger']=d.current_fill_pct.ge(trigger)
    d['forecast_trigger']=d.risk_upper_pct.ge(trigger)
    d['gap_trigger']=d.hours_since_collection.ge(gap)|d.hours_since_collection.isna()
    d['telemetry_trigger']=d.sensor_age_hours.gt(CFG['stale_sensor_hours_assumed'])|d.current_fill_pct.isna()|d.sensor_age_hours.isna()
    d['required']=d[['current_trigger','forecast_trigger','gap_trigger','telemetry_trigger']].any(axis=1)
    d['tier']=np.select([d.current_trigger,d.telemetry_trigger,d.gap_trigger,d.forecast_trigger],[1,2,3,4],default=5)
    d['reasons']=d.apply(lambda r:';'.join(k for k in ['current_trigger','telemetry_trigger','gap_trigger','forecast_trigger'] if r[k]) or 'below_rules',axis=1)
    d['dispatch_status']=np.select([d.required&~d.network_accessible,d.required&d.in_routing_pilot,d.required],['access_review','pilot_required','required_outside_pilot'],default='monitor')
    d=d.sort_values(['tier','risk_upper_pct','current_fill_pct','hours_since_collection','bin_id'],ascending=[True,False,False,False,True])
    d['priority_rank']=range(1,len(d)+1)
    d['trigger_pct']=trigger;d['interval_level']=interval;d['max_gap_hours']=gap;d['demand_multiplier']=demand_multiplier
    return d

def run():
    f=pd.read_csv(FC/'dispatch_forecasts.csv',dtype={'zone_id':str})
    s=pd.read_parquet(GEO/'bin_spatial_features.parquet')
    f=f.merge(s[['bin_id','network_accessible','in_routing_pilot','snap_m']],on='bin_id',validate='one_to_one')
    base=prioritize(f);base.to_csv(OPT/'collection_priority.csv',index=False)
    rows=[]
    for t in [70,80,90]:
      for level in [80,90,95]:
       for gap in [36,48,72]:
        p=prioritize(f,t,level,gap)
        rows.append({'trigger_pct':t,'interval_level':level,'max_gap_hours':gap,'required_bins':int(p.required.sum()),'pilot_required_bins':int((p.required&p.in_routing_pilot).sum()),'access_exceptions':int((p.required&~p.network_accessible).sum()),'full_capacity_l_required_pilot':int(p.loc[p.required&p.in_routing_pilot,'capacity_l'].sum()),'data_origin':'synthetic'})
    pd.DataFrame(rows).to_csv(OPT/'priority_sensitivity.csv',index=False)
    print(base.dispatch_status.value_counts().to_dict())
    return f
if __name__=='__main__':run()
