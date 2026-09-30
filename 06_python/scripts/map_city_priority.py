"""City-wide operational priority map, separate from the 60-bin routing pilot."""
import os
os.environ['SMART_WASTE_CITY']='CBE'
from phase4_common import ROOT
import pandas as pd
import folium

def run():
    priority=pd.read_csv(ROOT/'10_optimization/phase4/collection_priority.csv')
    bins=pd.read_parquet(ROOT/'03_data/processed/dim_bin.parquet')
    data=priority.merge(bins[['bin_id','latitude','longitude']],on='bin_id',validate='one_to_one')
    m=folium.Map(location=[11.0168,76.9558],zoom_start=12,tiles='OpenStreetMap')
    colors={'monitor':'#54798d','required_outside_pilot':'#d97706','required_in_pilot':'#b91c1c','required_pilot':'#b91c1c'}
    for status,rows in data.groupby('dispatch_status'):
        group=folium.FeatureGroup(name=f'{status.replace("_"," ")} ({len(rows)})').add_to(m)
        for r in rows.itertuples():
            folium.CircleMarker([r.latitude,r.longitude],radius=5,color=colors.get(status,'#b91c1c'),fill=True,fill_opacity=.8,tooltip=f'CBE:{r.bin_id} | {status}',popup=f'<b>Synthetic bin CBE:{r.bin_id}</b><br>Current fill: {r.current_fill_pct:.1f}%<br>Forecast: {r.prediction_pct:.1f}%<br>Rank within city: {r.priority_rank}<br>Rules: {r.reasons}<br>As of 23 Sep 2026, 08:00 IST').add_to(group)
    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:28px;left:12px;z-index:9999;background:white;padding:12px;max-width:540px;font:14px Arial;box-shadow:0 1px 8px #888"><b>Coimbatore · synthetic collection priorities</b><br>500 hypothetical bins on real OSM road nodes. Orange bins need service outside the routing pilot; red bins are required within it. Blue bins are monitored.<br>Frozen issue: 23 Sep 2026, 08:00 IST. No municipal deployment claim.</div>'))
    m.fit_bounds([[data.latitude.min(),data.longitude.min()],[data.latitude.max(),data.longitude.max()]])
    m.save(ROOT/'14_outputs/maps/phase4_priority.html')
    print('Coimbatore city-wide priority map:',len(data),'bins; counts:',data.dispatch_status.value_counts().to_dict())

if __name__=='__main__':run()
