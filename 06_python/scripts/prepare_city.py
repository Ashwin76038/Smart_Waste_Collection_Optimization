"""Normalize real Coimbatore boundaries/context; place independent synthetic bins."""
from phase4_common import ROOT,PROJECT_ROOT,CFG,GEO,CITY_ID,dump
import pandas as pd,numpy as np,json,xml.etree.ElementTree as ET
from shapely.geometry import Polygon,MultiPolygon,Point,shape,mapping
from shapely import make_valid
from shapely.strtree import STRtree
from pyproj import Transformer
from shapely.ops import transform,unary_union

def run():
    assert CITY_ID=='CBE','Preserve existing Chennai preparation'
    p=ROOT/'03_data/processed';ns={'k':'http://www.opengis.net/kml/2.2'}
    source=next((PROJECT_ROOT/'03_data/raw/S26').rglob('*.kml'));doc=ET.parse(source);features=[];rows=[]
    project=Transformer.from_crs('EPSG:4326',CFG['analysis_crs'],always_xy=True).transform
    def coords(el):return [(float(t.split(',')[0]),float(t.split(',')[1])) for t in el.text.split()]
    for pm in doc.findall('.//k:Placemark',ns):
        attrs={x.attrib['name']:x.text for x in pm.findall('.//k:SimpleData',ns)}
        zone=str(attrs['sourcewardcode']).zfill(3);polys=[]
        for item in pm.findall('.//k:Polygon',ns):
            outer=coords(item.find('./k:outerBoundaryIs/k:LinearRing/k:coordinates',ns))
            holes=[coords(x) for x in item.findall('./k:innerBoundaryIs/k:LinearRing/k:coordinates',ns)]
            polys.append(Polygon(outer,holes))
        geom=make_valid(unary_union(polys));area=transform(project,geom).area
        features.append({'type':'Feature','properties':{**attrs,'ward':zone,'city_id':'CBE','source_id':'S26','data_origin':'real','vintage_note':'2024 per OpenCity metadata; not certified current'},'geometry':mapping(geom)})
        bounds=geom.bounds;rows.append({'zone_id':zone,'city_id':'CBE','city_name':'Coimbatore','admin_zone_name':attrs.get('zone'),'area_m2_source':area,'min_lon':bounds[0],'min_lat':bounds[1],'max_lon':bounds[2],'max_lat':bounds[3],'geometry_wkb':geom.wkb,'data_origin':'real','source_id':'S26','boundary_version':'2024_per_opencity_metadata'})
    zones=pd.DataFrame(rows).sort_values('zone_id');assert len(zones)==100 and zones.zone_id.is_unique
    zones.to_parquet(p/'dim_zone_ward.parquet',index=False);dump(p/'wards.geojson',{'type':'FeatureCollection','features':features})
    geoms=[shape(f['geometry']) for f in features];tree=STRtree(geoms)
    def assign(lon,lat):
        idx=tree.query(Point(lon,lat),predicate='intersects')
        return features[int(idx[0])]['properties']['ward'] if len(idx) else None
    nodes=pd.read_parquet(GEO/'road_nodes.parquet');nodes['zone_id']=[assign(x,y) for x,y in zip(nodes.longitude,nodes.latitude)]
    nodes=nodes[nodes.zone_id.notna()].copy();nodes['city_id']='CBE';nodes['source_id']='S09';nodes['data_origin']='real';nodes.to_parquet(p/'osm_road_nodes.parquet',index=False)
    pois=pd.read_parquet(GEO/'poi_extract.parquet');pois['zone_id']=[assign(x,y) for x,y in zip(pois.longitude,pois.latitude)];pois=pois[pois.zone_id.notna()].copy();pois.to_parquet(p/'osm_poi_nodes.parquet',index=False)
    rng=np.random.default_rng(20260924);chosen=[];short=[]
    for z in zones.zone_id:
        part=nodes[nodes.zone_id==z];n=min(5,len(part))
        if n<5:short.append({'zone_id':z,'available_nodes':len(part)})
        if n:chosen.append(part.loc[rng.choice(part.index,size=n,replace=False)])
    b=pd.concat(chosen).sort_values(['zone_id','osm_node_id'])
    extra=500-len(b)
    if extra:
        pool=nodes[~nodes.osm_node_id.isin(b.osm_node_id)];b=pd.concat([b,pool.loc[rng.choice(pool.index,size=extra,replace=False)]])
    b=b.sort_values(['zone_id','osm_node_id']).reset_index(drop=True);b['bin_id']=np.arange(1,501,dtype=np.int32)
    b['capacity_l']=rng.choice([240,660,1100],500,p=[.1,.6,.3]).astype('int16')
    factors={z:float(rng.lognormal(0,.18)) for z in zones.zone_id}
    b['demand_factor']=[float(np.clip(factors[z]*rng.lognormal(0,.25),.4,1.8)*.9) for z in b.zone_id]
    b['coordinate_origin']='real_osm_road_node';b['data_origin']='synthetic';b['scenario']='independent Coimbatore hypothetical bins; demand scale0.9 assumption';b['city_name']='Coimbatore'
    b.to_parquet(p/'dim_bin.parquet',index=False)
    weather=json.loads(next((PROJECT_ROOT/'03_data/raw/S30').rglob('*.json')).read_text());par=weather['properties']['parameter'];keys=list(par['T2M'])
    w=pd.DataFrame({'date':pd.to_datetime(keys,format='%Y%m%d'),'temperature_c':[par['T2M'][x] for x in keys],'rainfall_mm':[par['PRECTOTCORR'][x] for x in keys],'city_id':'CBE','city_name':'Coimbatore','latitude':11.0168,'longitude':76.9558,'source_id':'S30','data_origin':'proxy'});w.replace(-999,np.nan,inplace=True);w.to_parquet(p/'weather_grid_2025.parquet',index=False)
    dump(ROOT/'14_outputs/reports/geography_preparation.json',{'wards':len(zones),'road_nodes_inside':len(nodes),'pois_inside':len(pois),'poi_categories':pois.poi_type.value_counts().to_dict(),'bins':len(b),'ward_shortfalls':short,'bounds':unary_union(geoms).bounds,'area_km2_derived':sum(transform(project,g).area for g in geoms)/1e6,'bin_demand_scale':.9,'seed':20260924,'data_origin':'synthetic bin locations at real OSM road nodes; boundaries from community portal'})
    print('CBE prepared',len(zones),'wards',len(nodes),'nodes',len(pois),'POIs',len(b),'bins',flush=True)
if __name__=='__main__':run()
