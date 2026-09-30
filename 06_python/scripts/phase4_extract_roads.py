"""New derived graph extract from immutable S09; preserves one-way/access evidence."""
from phase4_common import ROOT,PROJECT_ROOT,CFG,GEO,dump,haversine,CITY_ID
import osmium,pandas as pd,re,time
from collections import Counter

HIGHWAYS={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street'}
SPEED={'motorway':50,'motorway_link':30,'trunk':40,'trunk_link':25,'primary':35,'primary_link':25,'secondary':30,'secondary_link':20,'tertiary':25,'tertiary_link':20,'unclassified':20,'residential':15,'service':15,'living_street':10}

def numeric_limit(text):
    if not text:return None
    m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(?:t|tonnes?|m|meters?)?\s*',text)
    return float(m.group(1)) if m else -1

class Extractor(osmium.SimpleHandler):
    def __init__(self):
        super().__init__();self.nodes={};self.edges=[];self.landuse=[];self.pois=[]
        self.blocked_nodes=set();self.blocked_ways=set();self.restrictions=[];self.exclusions=Counter()
    def inside(self,x,y):
        a,b,c,d=CFG['graph_bbox_lon_lat'];return a<=x<=c and b<=y<=d
    def node(self,n):
        if not n.location.valid():return
        if not self.inside(n.location.lon,n.location.lat):return
        t=n.tags
        kind=t.get('amenity') or t.get('shop') or t.get('railway') or (t.get('man_made') if t.get('man_made') in ('works','wastewater_plant') else None)
        if kind:self.pois.append((f'n/{n.id}',int(n.id),'node',n.location.lon,n.location.lat,kind,t.get('name') or '', 'S09','real'))
        if t.get('barrier') in ('bollard','block','chain','gate','lift_gate','bus_trap') and t.get('motor_vehicle') not in ('yes','designated','permissive'):
            self.blocked_nodes.add(int(n.id))
    def relation(self,r):
        t=r.tags
        if t.get('type')!='restriction':return
        restriction=t.get('restriction:hgv') or t.get('restriction:motor_vehicle') or t.get('restriction')
        if not restriction:return
        if any(x in (t.get('except') or '').split(';') for x in ('hgv','motor_vehicle','vehicle')):return
        vias=[int(m.ref) for m in r.members if m.role=='via' and m.type=='n']
        ways=[int(m.ref) for m in r.members if m.type=='w']
        # Conservative exclusion avoids silently traversing an unmodelled turn.
        if vias:self.blocked_nodes.update(vias)
        else:self.blocked_ways.update(ways)
        self.restrictions.append({'relation_id':int(r.id),'restriction':restriction,'via_nodes':vias,'ways':ways})
    def way(self,w):
        t=w.tags;h=t.get('highway');land=t.get('landuse')
        kind=t.get('amenity') or t.get('shop') or (t.get('railway') if t.get('railway')=='station' else None) or (t.get('man_made') if t.get('man_made') in ('works','wastewater_plant') else None)
        if h not in HIGHWAYS and land not in ('residential','commercial','retail','industrial') and not kind:return
        vals=[]
        for n in w.nodes:
            if not n.location.valid():return
            vals.append((int(n.ref),float(n.location.lon),float(n.location.lat)))
        if not any(self.inside(x,y) for _,x,y in vals):return
        if kind and vals:
            from shapely.geometry import Polygon,LineString
            geom=Polygon([(x,y) for _,x,y in vals]) if len(vals)>=4 and vals[0][0]==vals[-1][0] else LineString([(x,y) for _,x,y in vals]) if len(vals)>=2 else None
            if geom is not None:
                pt=geom.representative_point();self.pois.append((f'w/{w.id}',None,'way_representative_point',pt.x,pt.y,kind,t.get('name') or '', 'S09','derived'))
        if land in ('residential','commercial','retail','industrial') and len(vals)>=4 and vals[0][0]==vals[-1][0]:
            self.landuse.append({'type':'Feature','properties':{'osm_way_id':int(w.id),'landuse':land,'source_id':'S09'},'geometry':{'type':'Polygon','coordinates':[[[x,y] for _,x,y in vals]]}})
        if h not in HIGHWAYS:return
        for key in ('access','vehicle','motor_vehicle','hgv'):
            if t.get(key) in ('no','private','agricultural','forestry'):
                self.exclusions[key]+=1;return
        if any(t.get(k) for k in ('access:conditional','motor_vehicle:conditional','hgv:conditional','oneway:conditional')):
            self.exclusions['conditional_access_unresolved']+=1;return
        for key,vehicle in [('maxweight',CFG['truck_gross_tonnes_assumed']),('maxheight',CFG['truck_height_m_assumed']),('maxwidth',CFG['truck_width_m_assumed'])]:
            limit=numeric_limit(t.get(key))
            if limit is not None and (limit<0 or limit<vehicle):self.exclusions[key]+=1;return
        oneway=t.get('oneway') or ('yes' if t.get('junction')=='roundabout' or h=='motorway' else '')
        if oneway not in ('','yes','1','true','-1','no','0','false'):
            self.exclusions['oneway_unresolved']+=1;return
        speed=SPEED[h]
        try:
            limit=float(t.get('maxspeed','').split()[0]);speed=min(speed,limit)
        except (ValueError,IndexError):pass
        for a,b in zip(vals,vals[1:]):
            if not (self.inside(a[1],a[2]) and self.inside(b[1],b[2])):continue
            length=haversine(a[1],a[2],b[1],b[2])
            if length<=0 or a[0]==b[0]:continue
            self.nodes[a[0]]=(a[1],a[2]);self.nodes[b[0]]=(b[1],b[2])
            pairs=[(b[0],a[0])] if oneway=='-1' else [(a[0],b[0])]
            if oneway in ('','no','0','false'):pairs.append((b[0],a[0]))
            for u,v in pairs:
                self.edges.append((u,v,int(w.id),h,oneway,length,length/(speed/3.6),speed,t.get('hgv') or 'unknown',t.get('maxwidth') or 'unknown'))

def run():
    start=time.perf_counter();h=Extractor()
    p=next((PROJECT_ROOT/'03_data/raw/S09').rglob('*.osm.pbf'))
    processor=osmium.FileProcessor(str(p)).with_locations().with_filter(
        osmium.filter.KeyFilter('highway','landuse','barrier','restriction','restriction:hgv','restriction:motor_vehicle','amenity','shop','railway','man_made'))
    processed=0
    for item in processor:
        if isinstance(item,osmium.osm.Way):h.way(item)
        elif isinstance(item,osmium.osm.Node):h.node(item)
        elif isinstance(item,osmium.osm.Relation):h.relation(item)
        processed+=1
        if processed%500000==0:print('filtered OSM entities',processed,flush=True)
    edges=pd.DataFrame(h.edges,columns=['u','v','osm_way_id','highway','oneway_tag','length_m','travel_seconds_assumed','speed_kmh_assumed','hgv_tag','maxwidth_tag'])
    before=len(edges)
    mask=~edges.u.isin(h.blocked_nodes)&~edges.v.isin(h.blocked_nodes)&~edges.osm_way_id.isin(h.blocked_ways)
    edges=edges[mask].sort_values(['u','v','length_m']).drop_duplicates(['u','v']).reset_index(drop=True)
    edges['source_id']='S09';edges['data_origin']='derived';edges['time_origin']='assumption'
    kept=set(edges.u)|set(edges.v)
    nodes=pd.DataFrame([(k,*v) for k,v in h.nodes.items() if k in kept],columns=['osm_node_id','longitude','latitude'])
    edges.to_parquet(GEO/'directed_edges.parquet',index=False)
    nodes.to_parquet(GEO/'road_nodes.parquet',index=False)
    if CITY_ID!='CHN':
        pois=pd.DataFrame(h.pois,columns=['osm_feature_id','osm_node_id','geometry_origin','longitude','latitude','poi_type','name','source_id','data_origin'])
        pois['city_id']=CITY_ID;pois.to_parquet(GEO/'poi_extract.parquet',index=False)
    dump(GEO/'landuse_ways.geojson',{'type':'FeatureCollection','features':h.landuse})
    dump(GEO/'road_extraction_report.json',{'source_id':'S09','source_pbf':str(p.relative_to(PROJECT_ROOT)),'nodes':len(nodes),'directed_edges':len(edges),'before_restriction_and_duplicate_filter':before,'landuse_way_polygons':len(h.landuse),'excluded_way_reasons':dict(h.exclusions),'turn_restriction_handling':'remove applicable via nodes; via-way restrictions remove member ways conservatively','turn_restrictions_in_regional_source':len(h.restrictions),'bbox':CFG['graph_bbox_lon_lat'],'seconds':time.perf_counter()-start,'truck_safety':'not field verified; missing tags remain unknown; city regulations and time-dependent traffic not modelled'})
    print('graph extracted',len(nodes),len(edges),flush=True)
if __name__=='__main__':run()
