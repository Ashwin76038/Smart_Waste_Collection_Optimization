"""Create hypothetical bins at real OSM road nodes; never claim these are observed bins."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'03_data/processed'
def main():
 nodes=pd.read_parquet(P/'osm_road_nodes_chennai.parquet')
 zones=pd.read_parquet(P/'dim_zone_ward.parquet')
 rng=np.random.default_rng(20260923)
 chosen=[];short=[]
 for zone in zones.zone_id:
  part=nodes[nodes.zone_id==zone]
  if len(part)<5:short.append((zone,len(part)));continue
  ix=rng.choice(part.index.to_numpy(),size=5,replace=False)
  chosen.append(nodes.loc[ix].sort_values('osm_node_id'))
 if short:
  extra=sum(5-count for _,count in short)
  target=nodes.zone_id.value_counts().index[0]
  eligible=nodes[nodes.zone_id==target]
  already=set(pd.concat(chosen).osm_node_id)
  eligible=eligible[~eligible.osm_node_id.isin(already)]
  chosen.append(eligible.loc[rng.choice(eligible.index.to_numpy(),size=extra,replace=False)])
  print('OSM coverage shortfall',short,'extra bins assigned to ward',target)
 b=pd.concat(chosen,ignore_index=True).sort_values(['zone_id','osm_node_id']).reset_index(drop=True)
 b['bin_id']=np.arange(1,len(b)+1,dtype=np.int32)
 b['capacity_l']=rng.choice([240,660,1100],size=len(b),p=[.1,.6,.3]).astype(np.int16)
 ward_factors={z:float(rng.lognormal(mean=0,sigma=.18)) for z in zones.zone_id}
 b['demand_factor']=[float(np.clip(ward_factors[z]*rng.lognormal(mean=0,sigma=.25),.4,1.8)) for z in b.zone_id]
 b['coordinate_origin']='real_osm_road_node';b['data_origin']='synthetic';b['source_id']='S09';b['scenario']='hypothetical community bins'
 b=b[['bin_id','zone_id','latitude','longitude','osm_node_id','capacity_l','demand_factor','coordinate_origin','data_origin','source_id','scenario']]
 out=P/'dim_bin.parquet';b.to_parquet(out,index=False,compression='zstd')
 print('bins',len(b),'wards',b.zone_id.nunique(),'osm node ids unique',b.osm_node_id.is_unique,'bytes',out.stat().st_size)
if __name__=='__main__':main()
