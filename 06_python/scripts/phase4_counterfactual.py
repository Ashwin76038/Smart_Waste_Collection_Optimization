"""Isolated latent-truth evaluator. Never imported by forecast/priority/solver."""
from phase4_common import ROOT,CFG,OPT,GEO,dump
import duckdb,pandas as pd,numpy as np

def replay(initial,capacity,arrivals,services):
    """Arrivals uniformly spread over each subsequent two-hour interval; remove95%."""
    inventory=float(initial);overflow=removed=0.
    service_times=sorted(services)
    for step,volume in enumerate(arrivals):
        start=step*120.;end=start+120.;cursor=start
        events=[s for s in service_times if start<=s<end]
        for point in events+[end]:
            add=float(volume)*(point-cursor)/120
            spill=max(0,inventory+add-capacity);overflow+=spill;inventory=min(capacity,inventory+add)
            if point!=end:
                take=inventory*.95;removed+=take;inventory-=take
            cursor=point
    return inventory,overflow,removed

def run():
    loc=pd.read_csv(GEO/'matrix_locations.csv');bins=loc.loc[loc.bin_id.ne(0),'bin_id'].astype(int).tolist()
    issue=pd.Timestamp(CFG['issue_date_local'])+pd.Timedelta(hours=2,minutes=30)
    c=duckdb.connect(str(ROOT/'03_data/processed/waste.duckdb'),read_only=True)
    truth=c.execute('SELECT bin_id,timestamp_utc,inventory_l_true,arrivals_l_true,capacity_l FROM simulation_truth WHERE bin_id IN ('+','.join(map(str,bins))+') AND timestamp_utc BETWEEN ? AND ? ORDER BY bin_id,timestamp_utc',[issue,issue+pd.Timedelta(days=1)]).df();c.close()
    stops=pd.read_csv(OPT/'route_stops.csv');rows=[]
    for scenario in ['base_3_trucks','trigger_70','trigger_90','demand_plus20']:
        for method in ['baseline','optimized']:
            visits=stops[(stops.scenario==scenario)&(stops.method==method)&stops.bin_id.ne(0)].set_index('bin_id')
            if visits.empty:continue
            for bid,g in truth.groupby('bin_id'):
                assert len(g)==13
                initial=float(g.iloc[0].inventory_l_true);cap=float(g.iloc[0].capacity_l);arrivals=g.iloc[1:].arrivals_l_true.to_numpy(dtype=float)
                # To avoid adding an unmodelled future fleet, primary comparison is
                # an isolated single-shift intervention: no other collections in24h.
                times=[float(visits.loc[bid,'arrival_minutes_after_0800'])+CFG['service_minutes_per_bin_assumed']] if bid in visits.index else []
                mult=1.2 if scenario=='demand_plus20' else 1.
                final,spill,removed=replay(initial,cap,arrivals*mult,times)
                assert abs(initial+sum(arrivals)*mult-final-spill-removed)<1e-5
                rows.append({'scenario':scenario,'method':method,'bin_id':bid,'initial_l':initial,'arrivals_l':float(sum(arrivals)*mult),'terminal_l':final,'overflow_l':spill,'collected_l':removed,'collection_count':len(times),'capacity_l':cap,'data_origin':'synthetic'})
    out=pd.DataFrame(rows);out.to_csv(OPT/'counterfactual_bin_results.csv',index=False)
    total=out.groupby(['scenario','method'],as_index=False)[['initial_l','arrivals_l','terminal_l','overflow_l','collected_l','collection_count']].sum()
    total.to_csv(OPT/'counterfactual_totals.csv',index=False)
    dump(OPT/'counterfactual_contract.json',{'evaluation_only':True,'initial_time_utc':str(issue),'horizon_hours':24,'population_bins':60,'arrivals':'same latent future increments for baseline/optimized; uniformly accrued in2h intervals; +20% only stress scenario','service':'95% removed at end of4min; no misses; no other collections within24h','policy_scope':'Isolated dispatch intervention, not a replacement weekly municipal policy. All60 pilot bins included, not just served subset.','limitations':'Early collection can worsen later overflow. No causal real-world effect or annualized avoided overflow claimed. Forecast baseline policy is not a counterfactual post-service forecast.'})
    print(total.to_string(index=False))
if __name__=='__main__':run()
