"""Spatial context, coverage proxies and auditable directed pilot road matrices."""
from phase4_common import ROOT,CFG,GEO,MAPS,dump,haversine
import json,math
import pandas as pd,numpy as np,networkx as nx
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from pyproj import Transformer
from shapely.geometry import shape,Point,mapping
from shapely.ops import transform
from shapely.strtree import STRtree
from shapely import make_valid
import folium
from folium.plugins import MarkerCluster

def load_graph():
    edges=pd.read_parquet(GEO/'directed_edges.parquet')
    nodes=pd.read_parquet(GEO/'road_nodes.parquet')
    graph=nx.DiGraph()
    graph.add_weighted_edges_from(edges[['u','v','length_m']].itertuples(index=False,name=None))
    return graph,edges,nodes

def run():
    graph,edges,nodes=load_graph();component=max(nx.strongly_connected_components(graph),key=len)
    eligible=nodes[nodes.osm_node_id.isin(component)].copy()
    project=Transformer.from_crs('EPSG:4326',CFG.get('analysis_crs','EPSG:32644'),always_xy=True).transform
    xy=np.column_stack(project(eligible.longitude.to_numpy(),eligible.latitude.to_numpy()))
    bins=pd.read_parquet(ROOT/'03_data/processed/dim_bin.parquet')
    bxy=np.column_stack(project(bins.longitude.to_numpy(),bins.latitude.to_numpy()))
    distances,nearest=cKDTree(xy).query(bxy)
    bins['snap_m']=distances;bins['routing_node_id']=eligible.iloc[nearest].osm_node_id.to_numpy()
    bins['network_accessible']=bins.snap_m<=CFG['max_snap_m']
    bins['center_distance_m']=[haversine(CFG['pilot_center_lon'],CFG['pilot_center_lat'],r.longitude,r.latitude) for r in bins.itertuples()]
    bins['nearest_other_hypothetical_bin_m']=cKDTree(bxy).query(bxy,k=2)[0][:,1]
    pois=pd.read_parquet(ROOT/'03_data/processed'/CFG.get('poi_filename','osm_poi_nodes_chennai.parquet'))
    commercial=pois[pois.poi_type.isin(['restaurant','marketplace','supermarket','convenience'])]
    pxy=np.column_stack(project(commercial.longitude.to_numpy(),commercial.latitude.to_numpy()))
    ptree=cKDTree(pxy)
    bins['nearest_mapped_commercial_poi_m']=ptree.query(bxy)[0]
    bins['mapped_commercial_pois_within500m']=[len(x) for x in ptree.query_ball_point(bxy,500)]
    land=json.loads((GEO/'landuse_ways.geojson').read_text())
    residential=[transform(project,make_valid(shape(f['geometry']))) for f in land['features'] if f['properties']['landuse']=='residential']
    tree=STRtree(residential) if residential else None
    bins['nearest_mapped_residential_landuse_m']=[Point(*p).distance(residential[tree.nearest(Point(*p))]) if tree else np.nan for p in bxy]
    allpxy=np.column_stack(project(pois.longitude.to_numpy(),pois.latitude.to_numpy()))
    pois['nearest_hypothetical_bin_m']=cKDTree(bxy).query(allpxy)[0]
    pois['coverage_origin']='proxy: straight-line distance to synthetic bins, not resident walking access'
    pois.to_csv(GEO/'poi_coverage.csv',index=False)
    # Spatially checked identifiers; do not join Census wards by number.
    raw=ROOT/CFG['boundary_path'] if 'boundary_path' in CFG else next((ROOT/'03_data/raw/S08').rglob('*.geojson'));wards=json.loads(raw.read_text(encoding='utf-8'))
    polygons=[make_valid(shape(f['geometry'])) for f in wards['features']];wardtree=STRtree(polygons)
    matches=[wardtree.query(Point(r.longitude,r.latitude),predicate='intersects') for r in bins.itertuples()]
    bins['ward_match_count']=[len(x) for x in matches]
    bins['assigned_ward_matches_polygon']=[str(r.zone_id) in [str(wards['features'][int(i)]['properties']['ward']) for i in ix] for r,ix in zip(bins.itertuples(),matches)]
    assert bins.assigned_ward_matches_polygon.all()
    pilot=bins[bins.network_accessible].sort_values(['center_distance_m','bin_id']).head(CFG['pilot_bin_count']).copy()
    bins['in_routing_pilot']=bins.bin_id.isin(pilot.bin_id)
    bins.to_parquet(GEO/'bin_spatial_features.parquet',index=False);bins.to_csv(GEO/'bin_spatial_features.csv',index=False)
    pilot.to_csv(GEO/'pilot_bins.csv',index=False)
    centerxy=np.array(project(CFG['pilot_center_lon'],CFG['pilot_center_lat']))
    _,depidx=cKDTree(xy).query(centerxy);depot=eligible.iloc[int(depidx)]
    locations=pd.concat([pd.DataFrame([{'bin_id':0,'routing_node_id':int(depot.osm_node_id),'latitude':depot.latitude,'longitude':depot.longitude,'capacity_l':0,'snap_m':0}]),pilot[['bin_id','routing_node_id','latitude','longitude','capacity_l','snap_m']]],ignore_index=True)
    locations['matrix_index']=range(len(locations));locations.to_csv(GEO/'matrix_locations.csv',index=False)
    node_ids=np.sort(nodes.osm_node_id.to_numpy());index={int(k):i for i,k in enumerate(node_ids)}
    u=edges.u.map(index).to_numpy(dtype=np.int32);v=edges.v.map(index).to_numpy(dtype=np.int32)
    sparse=coo_matrix((edges.length_m,(u,v)),shape=(len(node_ids),len(node_ids))).tocsr()
    edge_time={(int(r.u),int(r.v)):float(r.travel_seconds_assumed) for r in edges.itertuples()}
    target_indices=np.array([index[int(x)] for x in locations.routing_node_id])
    dm=np.zeros((len(locations),len(locations)));tm=dm.copy();paths={}
    for i,source in enumerate(target_indices):
        dist,pred=dijkstra(sparse,directed=True,indices=int(source),return_predecessors=True)
        for j,target in enumerate(target_indices):
            if not np.isfinite(dist[target]):raise ValueError('Unreachable pair survived strong-component filter')
            path=[int(target)]
            while path[-1]!=source:
                previous=int(pred[path[-1]])
                if previous<0:raise ValueError('Broken predecessor path')
                path.append(previous)
            ids=[int(node_ids[k]) for k in reversed(path)]
            dm[i,j]=dist[target];tm[i,j]=sum(edge_time[(a,b)] for a,b in zip(ids,ids[1:]))
            paths[f'{i},{j}']=ids
        if i%20==0:print('road matrix origins',i+1,'/',len(locations),flush=True)
    np.savez_compressed(GEO/'road_matrix.npz',distance_m=dm,travel_seconds_assumed=tm)
    dump(GEO/'matrix_paths.json',paths)
    summary={'all_bins':len(bins),'network_accessible_within100m':int(bins.network_accessible.sum()),'inaccessible_bins':int((~bins.network_accessible).sum()),
      'largest_strong_component_nodes':len(component),'all_graph_nodes':len(nodes),'directed_edges':len(edges),
      'pilot_bins':len(pilot),'pilot_selection':'60 geographically nearest network-accessible bins to fixed city-center coordinate; no fill or outcome used',
      'pilot_furthest_center_m':float(pilot.center_distance_m.max()),'max_pilot_snap_m':float(pilot.snap_m.max()),
      'all_bin_snap_p95_m':float(bins.snap_m.quantile(.95)),'poi_count':len(pois),'commercial_poi_count':len(commercial),
      'poi_within250m_hypothetical_bin_pct':float(100*(pois.nearest_hypothetical_bin_m<=250).mean()),
      'poi_within500m_hypothetical_bin_pct':float(100*(pois.nearest_hypothetical_bin_m<=500).mean()),
      'median_nearest_commercial_m':float(bins.nearest_mapped_commercial_poi_m.median()),'residential_way_polygons':len(residential),
      'geometry_valid_original':sum(shape(f['geometry']).is_valid for f in wards['features']),
      'ward_matches':int(bins.assigned_ward_matches_polygon.sum()),'depot_node_id':int(depot.osm_node_id),
      'depot_latitude':float(depot.latitude),'depot_longitude':float(depot.longitude),'depot_origin':'hypothetical facility at real road node',
      'matrix_asymmetric_pairs':int(np.sum(abs(dm-dm.T)>1)),
      'limitations':'No verified resident coverage, actual bin inventory, truck-safe entrances or municipal receiving facility. Landuse closed ways only; multipolygon relations omitted. Distance buffers are straight-line projected proxies.'}
    dump(GEO/'geospatial_summary.json',summary)
    # Interactive retrospective map: annual metrics explicitly not dispatcher features.
    annual=pd.read_csv(ROOT/'14_outputs/tables/phase3_eda/bin_annual_summary.csv')
    m=folium.Map(location=[CFG['pilot_center_lat'],CFG['pilot_center_lon']],zoom_start=11,tiles='OpenStreetMap')
    folium.GeoJson(wards,name=CFG.get('boundary_label','Official GCC ward boundaries'),style_function=lambda _: {'color':'#456','weight':1,'fillOpacity':.02}).add_to(m)
    group=folium.FeatureGroup(name='Synthetic 2026 overflow hotspots')
    merged=bins.merge(annual[['bin_id','overflow_days','mean_arrival_l_day']],on='bin_id',validate='one_to_one')
    for r in merged.itertuples():
        color='#b2182b' if r.overflow_days>=200 else ('#ef8a62' if r.overflow_days>=100 else '#2166ac')
        folium.CircleMarker([r.latitude,r.longitude],radius=4,color=color,fill=True,fill_opacity=.75,
           tooltip=f'SYNTHETIC bin {r.bin_id}; ward {r.zone_id}; {r.overflow_days} overflow days; {r.mean_arrival_l_day:.0f} L/day; road-access candidate={r.network_accessible}').add_to(group)
    group.add_to(m)
    pg=folium.FeatureGroup(name='Mapped commercial activity (OSM proxy)',show=False)
    for r in commercial.itertuples():folium.CircleMarker([r.latitude,r.longitude],radius=3,color='#874',tooltip=str(r.poi_type)).add_to(pg)
    pg.add_to(m)
    folium.GeoJson(land,name='Mapped land-use ways (incomplete)',show=False,style_function=lambda f:{'color':'#8a7','weight':1,'fillOpacity':.15}).add_to(m)
    roads=folium.FeatureGroup(name='Primary/secondary road sample',show=False)
    coords=nodes.set_index('osm_node_id')[['latitude','longitude']].to_dict('index')
    for r in edges[edges.highway.isin(['primary','secondary']) & (edges.u<edges.v)].head(10000).itertuples():
        folium.PolyLine([[coords[r.u]['latitude'],coords[r.u]['longitude']],[coords[r.v]['latitude'],coords[r.v]['longitude']]],color='#555',weight=1,opacity=.5).add_to(roads)
    roads.add_to(m)
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:30px;left:10px;z-index:9999;background:white;padding:10px;max-width:540px"><b>Synthetic waste/overflow scenario · real GCC/OSM geography</b><br>Annual 2026 retrospective; hypothetical bins.<br>Overflow days: blue &lt;100; coral 100–199; red ≥200.<br>© OpenStreetMap contributors.</div>'))
    folium.LayerControl(collapsed=False).add_to(m);m.save(str(MAPS/'phase4_geospatial.html'))
    print(summary)
if __name__=='__main__':run()
