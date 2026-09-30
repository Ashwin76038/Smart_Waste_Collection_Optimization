"""Same-demand baseline versus constrained OR-Tools routes on directed OSM paths."""
from phase4_common import ROOT,CFG,GEO,OPT,MAPS,dump
from phase4_priority import run as priority_run,prioritize
import pandas as pd,numpy as np,json,math,time
from ortools.constraint_solver import pywrapcp,routing_enums_pb2
import folium

def route_metrics(route,dm,tm,loads):
    return {'distance_m':float(sum(dm[a,b] for a,b in zip(route,route[1:]))),
      'travel_seconds':float(sum(tm[a,b] for a,b in zip(route,route[1:]))),
      'load_l':int(sum(loads[x] for x in route[1:-1])),
      'duration_seconds':float(sum(tm[a,b] for a,b in zip(route,route[1:]))+max(0,len(route)-2)*CFG['service_minutes_per_bin_assumed']*60+(CFG['unload_minutes_at_depot_assumed']*60 if len(route)>2 else 0))}

def feasible(route,dm,tm,loads):
    m=route_metrics(route,dm,tm,loads)
    return m['load_l']<=CFG['truck_volume_l_assumed'] and m['load_l']*CFG['density_kg_per_l_assumed']<=CFG['truck_payload_kg_assumed'] and m['duration_seconds']<=CFG['shift_minutes_assumed']*60

def baseline(required,nvehicles,dm,tm,loads):
    remaining=set(required);routes=[]
    for _ in range(nvehicles):
        r=[0]
        while remaining:
            candidates=sorted(remaining,key=lambda k:(dm[r[-1],k],k))
            chosen=next((k for k in candidates if feasible(r+[k,0],dm,tm,loads)),None)
            if chosen is None:break
            r.append(chosen);remaining.remove(chosen)
        routes.append(r+[0])
    return routes,sorted(remaining)

def optimize(required,nvehicles,dm,tm,loads,base):
    ids=[0]+list(required);manager=pywrapcp.RoutingIndexManager(len(ids),nvehicles,0);routing=pywrapcp.RoutingModel(manager)
    node=lambda ix:ids[manager.IndexToNode(ix)]
    dist=routing.RegisterTransitCallback(lambda a,b:int(math.ceil(dm[node(a),node(b)])))
    routing.SetArcCostEvaluatorOfAllVehicles(dist)
    timecb=routing.RegisterTransitCallback(lambda a,b:int(math.ceil(tm[node(a),node(b)]))+(CFG['service_minutes_per_bin_assumed']*60 if node(a)!=0 else 0)+(CFG['unload_minutes_at_depot_assumed']*60 if node(b)==0 and node(a)!=0 else 0))
    routing.AddDimension(timecb,0,CFG['shift_minutes_assumed']*60,True,'Shift')
    vol=routing.RegisterUnaryTransitCallback(lambda a:int(loads[node(a)]))
    routing.AddDimensionWithVehicleCapacity(vol,0,[CFG['truck_volume_l_assumed']]*nvehicles,True,'Volume')
    weight=routing.RegisterUnaryTransitCallback(lambda a:int(math.ceil(loads[node(a)]*CFG['density_kg_per_l_assumed']*1000)))
    routing.AddDimensionWithVehicleCapacity(weight,0,[int(CFG['truck_payload_kg_assumed']*1000)]*nvehicles,True,'PayloadGrams')
    params=pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds=CFG['solver_seconds']
    reverse={g:i for i,g in enumerate(ids)}
    initial=routing.ReadAssignmentFromRoutes([[reverse[x] for x in r[1:-1]] for r in base],True) if base else None
    start=time.perf_counter()
    solution=routing.SolveFromAssignmentWithParameters(initial,params) if initial else routing.SolveWithParameters(params)
    if not solution:return None,{'solver_status':int(routing.status()),'runtime_seconds':time.perf_counter()-start,'optimality':'No solution found within search; not an infeasibility proof'}
    routes=[]
    for vehicle in range(nvehicles):
        i=routing.Start(vehicle);r=[]
        while not routing.IsEnd(i):r.append(node(i));i=solution.Value(routing.NextVar(i))
        r.append(0);routes.append(r)
    return routes,{'solver_status':int(routing.status()),'runtime_seconds':time.perf_counter()-start,'optimality':'Feasible bounded search; global optimality not claimed'}

def validate(routes,required,dm,tm,loads):
    visits=[x for r in routes for x in r[1:-1]]
    assert sorted(visits)==sorted(required) and len(visits)==len(set(visits))
    assert all(r[0]==r[-1]==0 and feasible(r,dm,tm,loads) for r in routes)

def run():
    f=priority_run();loc=pd.read_csv(GEO/'matrix_locations.csv');mat=np.load(GEO/'road_matrix.npz');dm=mat['distance_m'];tm=mat['travel_seconds_assumed'];loads=loc.capacity_l.to_numpy()
    scenarios=[('base_3_trucks',3,80,1.,1.),('one_truck',1,80,1.,1.),('two_trucks',2,80,1.,1.),('trigger_70',3,70,1.,1.),('trigger_90',3,90,1.,1.),('demand_plus20',3,80,1.2,1.),('truck_unavailable',2,80,1.,1.),('fuel_minus20',3,80,1.,.8),('fuel_plus20',3,80,1.,1.2)]
    records=[];details={};route_rows=[];stop_rows=[];cache={}
    for name,fleet,threshold,demand,price in scenarios:
        p=prioritize(f,threshold,90,48,demand);required=loc.loc[loc.bin_id.isin(p.loc[p.required,'bin_id']) & loc.bin_id.ne(0),'matrix_index'].tolist()
        record={'scenario':name,'vehicles_available':fleet,'trigger_pct':threshold,'demand_multiplier':demand,'fuel_price_multiplier':price,'required_bins':len(required),'full_capacity_l_required':int(sum(loads[k] for k in required)),'data_origin':'synthetic','distance_origin':'derived OSM road paths; hypothetical stops/depot'}
        key=(fleet,tuple(required))
        if record['full_capacity_l_required']>fleet*CFG['truck_volume_l_assumed']:
            record.update(status='proven_infeasible_capacity',bins_serviced=0,reason='Total planned volume exceeds fleet capacity; no partial-route savings claimed');records.append(record);continue
        if key not in cache:
            b,unserved=baseline(required,fleet,dm,tm,loads)
            o,meta=optimize(required,fleet,dm,tm,loads,b if not unserved else None)
            cache[key]=(b,unserved,o,meta)
        b,unserved,o,meta=cache[key]
        record.update(meta)
        if o is None:record.update(status='search_no_solution',bins_serviced=0);records.append(record);continue
        validate(o,required,dm,tm,loads)
        if not unserved:validate(b,required,dm,tm,loads)
        details[name]={'required_matrix_indices':required,'baseline':b,'baseline_unserved':unserved,'optimized':o,'metadata':meta}
        record.update(status='feasible',bins_serviced=len(required),baseline_complete=not unserved)
        for method,routes in [('baseline',b),('optimized',o)]:
            stats=[route_metrics(r,dm,tm,loads) for r in routes]
            record[method+'_km']=sum(m['distance_m'] for m in stats)/1000
            record[method+'_vehicle_hours']=sum(m['duration_seconds'] for m in stats)/3600
            record[method+'_travel_hours']=sum(m['travel_seconds'] for m in stats)/3600
            for vehicle,(r,m) in enumerate(zip(routes,stats),1):
                route_rows.append({'scenario':name,'method':method,'vehicle':vehicle,'bins':len(r)-2,**m,'load_kg_assumed':m['load_l']*CFG['density_kg_per_l_assumed'],'matrix_indices':json.dumps(r),'data_origin':'synthetic'})
                elapsed=0
                for seq,x in enumerate(r):
                    if seq:elapsed+=tm[r[seq-1],x]/60+(CFG['service_minutes_per_bin_assumed'] if r[seq-1]!=0 else 0)
                    stop_rows.append({'scenario':name,'method':method,'vehicle':vehicle,'stop_sequence':seq,'matrix_index':x,'bin_id':int(loc.iloc[x].bin_id),'arrival_minutes_after_0800':elapsed,'planned_capacity_l':int(loads[x]),'data_origin':'synthetic'})
        if not unserved:
            saved=record['baseline_km']-record['optimized_km'];fuel=saved/CFG['fuel_economy_km_per_l_assumed']
            record.update(km_saved=saved,distance_reduction_pct=100*saved/record['baseline_km'],travel_hours_saved=record['baseline_travel_hours']-record['optimized_travel_hours'],vehicle_hours_saved=record['baseline_vehicle_hours']-record['optimized_vehicle_hours'],fuel_l_saved_assumed=fuel,fuel_cost_inr_saved_historical_proxy=fuel*CFG['diesel_price_inr_per_l_historical_proxy']*price,tailpipe_co2_kg_saved_proxy=fuel*CFG['co2_kg_per_l_proxy'])
        records.append(record);print(name,record['status'],record.get('km_saved'),flush=True)
    pd.DataFrame(records).to_csv(OPT/'scenario_comparison.csv',index=False)
    pd.DataFrame(route_rows).to_csv(OPT/'route_summary.csv',index=False);pd.DataFrame(stop_rows).to_csv(OPT/'route_stops.csv',index=False);dump(OPT/'route_solutions.json',details)
    base=next(r for r in records if r['scenario']=='base_3_trucks')
    pd.DataFrame([{'km_per_l_assumed':eff,'fuel_l_saved':base.get('km_saved',0)/eff,'historical_cost_inr_saved':base.get('km_saved',0)/eff*CFG['diesel_price_inr_per_l_historical_proxy'],'data_origin':'assumption'} for eff in [3,4.5,6]]).to_csv(OPT/'fuel_sensitivity.csv',index=False)
    paths=json.loads((GEO/'matrix_paths.json').read_text());nodes=pd.read_parquet(GEO/'road_nodes.parquet').set_index('osm_node_id')
    m=folium.Map(location=[CFG['pilot_center_lat'],CFG['pilot_center_lon']],zoom_start=14)
    colors=['#0072B2','#D55E00','#009E73'];features=[]
    for method in ['baseline','optimized']:
        group=folium.FeatureGroup(name=method+' — same required bins',show=method=='optimized')
        for veh,r in enumerate(details['base_3_trucks'][method]):
            for a,b in zip(r,r[1:]):
                ids=paths[f'{a},{b}'];coords=nodes.loc[ids,['longitude','latitude']].to_numpy().tolist()
                if len(coords)<2:continue
                folium.PolyLine([[lat,lon] for lon,lat in coords],color=colors[veh%3],weight=4,tooltip=f'{method} vehicle {veh+1}: {a} → {b}').add_to(group)
                features.append({'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'method':method,'vehicle':veh+1,'from_index':a,'to_index':b,'distance_m':float(dm[a,b]),'data_origin':'derived','operational_origin':'synthetic'}})
        group.add_to(m)
    required=set(details['base_3_trucks']['required_matrix_indices'])
    for r in loc.itertuples():
        folium.CircleMarker([r.latitude,r.longitude],radius=7 if r.matrix_index==0 else 4,color='black' if r.matrix_index==0 else ('#c22' if r.matrix_index in required else '#999'),tooltip='Hypothetical depot/receiving site' if r.matrix_index==0 else f'Synthetic bin {r.bin_id}; required={r.matrix_index in required}; road snap {r.snap_m:.1f}m').add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:30px;left:10px;z-index:9999;background:white;padding:12px;max-width:520px"><b>SIMULATED dispatch · 23 Sep 2026, 08:00 IST</b><br>Real OSM road geometry; hypothetical bins, depot and trucks. Toggle baseline/optimized. Roads require field access verification.<br>Vehicles: blue 1, orange 2, green 3. Red bins required; grey monitored.<br>© OpenStreetMap contributors.</div>'))
    m.save(str(MAPS/'phase4_routes.html'));dump(OPT/'route_paths.geojson',{'type':'FeatureCollection','features':features})
    print(pd.DataFrame(records).to_string(index=False))
if __name__=='__main__':run()
