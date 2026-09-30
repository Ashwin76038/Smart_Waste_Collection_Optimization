"""Process immutable real GCC/Census/NASA sources; OSM road extraction is optional until PBF completes."""
from pathlib import Path
import json, math, csv, hashlib, sys
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import openpyxl
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'03_data/raw'
OUT=ROOT/'03_data/processed'
OUT.mkdir(exist_ok=True)
def find(sid,glob):return next((RAW/sid).rglob(glob))
def write(df,name):
 p=OUT/name
 df.to_parquet(p,index=False,compression='zstd')
 print(name,len(df),p.stat().st_size)
def process_official():
 gj=json.loads(find('S08','*.geojson').read_text(encoding='utf-8'))
 rows=[]
 for f in gj['features']:
  s=shape(f['geometry']);p=f['properties'];b=s.bounds
  rows.append({'zone_id':str(p['ward']),'source_objectid':int(p['objectid']),'area_m2_source':float(p['st_area(shape)']),'min_lon':b[0],'min_lat':b[1],'max_lon':b[2],'max_lat':b[3],'geometry_wkb':s.wkb,'data_origin':'official','source_id':'S08','boundary_version':'unverified_2026_09_23_snapshot'})
 zones=pd.DataFrame(rows).sort_values('zone_id')
 assert len(zones)==200 and zones.zone_id.is_unique
 write(zones,'dim_zone_ward.parquet')
 wb=openpyxl.load_workbook(find('S05','*.xlsx'),read_only=True,data_only=True)
 ws=wb.active; itr=ws.values;hdr=next(itr); census=pd.DataFrame(itr,columns=hdr)
 census.columns=[str(x) for x in census.columns]
 for c in ['No_HH','TOT_P']:
  census[c]=pd.to_numeric(census[c],errors='coerce')
 census['data_origin']='official';census['source_id']='S05';census['census_year']=2011
 # Native geography. No current-ward crosswalk.
 write(census,'census_chennai_2011_native.parquet')
 j=json.loads(find('S14','*.json').read_text(encoding='utf-8'))
 params=j['properties']['parameter'];d=pd.DataFrame({'date':list(params['T2M']),'temperature_c':list(params['T2M'].values()),'rainfall_mm':[params['PRECTOTCORR'][k] for k in params['T2M']]})
 d['date']=pd.to_datetime(d['date'],format='%Y%m%d').dt.date
 d['data_origin']='proxy';d['source_id']='S14';d['latitude']=13.0827;d['longitude']=80.2707
 write(d,'weather_chennai_grid_2025.parquet')
 return len(zones),len(census),len(d)

def extract_osm():
 import osmium
 p=find('S09','*.osm.pbf')
 class Handler(osmium.SimpleHandler):
  def __init__(self):super().__init__();self.nodes={};self.edges=[];self.pois=[]
  def node(self,n):
   try: lon=float(n.location.lon);lat=float(n.location.lat)
   except Exception:return
   if not (80.15<=lon<=80.38 and 12.9<=lat<=13.25):return
   t=n.tags; amenity=t.get('amenity');shop=t.get('shop');landuse=t.get('landuse')
   if amenity in ('school','hospital','restaurant','marketplace','waste_disposal','recycling') or shop in ('supermarket','convenience'):
    self.pois.append((int(n.id),lon,lat,amenity or shop,'amenity' if amenity else 'shop'))
  def way(self,w):
   h=w.tags.get('highway')
   if h not in ('residential','tertiary','secondary','primary','service','unclassified','living_street'):return
   if w.tags.get('access') in ('no','private'):return
   vals=[]
   for n in w.nodes:
    try:lon=float(n.location.lon);lat=float(n.location.lat)
    except Exception:continue
    vals.append((int(n.ref),lon,lat))
   for a,b in zip(vals,vals[1:]):
    if not (80.15<=a[1]<=80.38 and 12.9<=a[2]<=13.25 and 80.15<=b[1]<=80.38 and 12.9<=b[2]<=13.25):continue
    self.nodes[a[0]]=(a[1],a[2]);self.nodes[b[0]]=(b[1],b[2])
    dy=math.radians(b[2]-a[2]);dx=math.radians(b[1]-a[1]);s=math.sin(dy/2)**2+math.cos(math.radians(a[2]))*math.cos(math.radians(b[2]))*math.sin(dx/2)**2
    length=2*6371000*math.asin(min(1,math.sqrt(s)))
    if length>0:self.edges.append((int(w.id),a[0],b[0],h,w.tags.get('oneway') or '',length))
 h=Handler();h.apply_file(str(p),locations=True)
 print('OSM raw in bbox',len(h.nodes),len(h.edges),len(h.pois))
 # Keep inside actual GCC polygon, including boundary buffer at 100 m for road connectivity.
 zones=json.loads(find('S08','*.geojson').read_text(encoding='utf-8'))
 polys=[shape(f['geometry']) for f in zones['features']];zt=STRtree(polys)
 node_rows=[]
 for node,(lon,lat) in h.nodes.items():
  pt=Point(lon,lat);ix=zt.query(pt,predicate='intersects')
  if len(ix):node_rows.append((node,lon,lat,str(zones['features'][int(ix[0])]['properties']['ward'])))
 nodes=pd.DataFrame(node_rows,columns=['osm_node_id','longitude','latitude','zone_id'])
 nodes['data_origin']='real';nodes['source_id']='S09'
 write(nodes,'osm_road_nodes_chennai.parquet')
 kept=set(nodes.osm_node_id)
 edges=pd.DataFrame([e for e in h.edges if e[1] in kept and e[2] in kept],columns=['osm_way_id','from_node','to_node','highway','oneway_tag','segment_length_m'])
 edges['data_origin']='real';edges['source_id']='S09'
 write(edges,'osm_road_segments_chennai.parquet')
 pois=pd.DataFrame(h.pois,columns=['osm_node_id','longitude','latitude','poi_type','tag_key'])
 if len(pois):pois=pois[pois.apply(lambda r:len(zt.query(Point(r.longitude,r.latitude),predicate='intersects'))>0,axis=1)]
 pois['data_origin']='real';pois['source_id']='S09'
 write(pois,'osm_poi_nodes_chennai.parquet')
 return len(nodes),len(edges),len(pois)
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'official'
 print(process_official() if mode=='official' else extract_osm())
