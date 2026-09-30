from pathlib import Path
import sys,json,math,re,os
PROJECT_ROOT=Path(__file__).resolve().parents[2]
CITY_ID=os.environ.get('SMART_WASTE_CITY','CHN')
if CITY_ID not in ('CHN','CBE'):raise ValueError('Unknown SMART_WASTE_CITY')
ROOT=PROJECT_ROOT if CITY_ID=='CHN' else PROJECT_ROOT/'cities'/CITY_ID
for part in ['work/pydeps','work/phase4deps']:
    folder=PROJECT_ROOT/part
    if folder.exists(): sys.path.insert(0,str(folder))
CFG=json.loads((ROOT/'config/phase4.json').read_text(encoding='utf-8'))
GEO=ROOT/'08_geospatial/phase4'
FC=ROOT/'09_forecasting/phase4'
OPT=ROOT/'10_optimization/phase4'
REPORT=ROOT/'14_outputs/reports'
MAPS=ROOT/'14_outputs/maps'
for folder in [GEO,FC,OPT,REPORT,MAPS]: folder.mkdir(parents=True,exist_ok=True)
def dump(path,obj): path.write_text(json.dumps(obj,indent=2,default=str)+'\n',encoding='utf-8')
def format_prose(text):
    """Separate numbers/words in narrative while preserving paths, URLs and code."""
    parts=re.split(r'(```[\s\S]*?```|`[^`]*`|\[[^\]]*\]\([^)]*\)|https?://\S+)',text)
    for i in range(0,len(parts),2):
        parts[i]=re.sub(r'(?<=[a-z])(?=\d)|(?<=\d)(?=[A-Za-z])|(?<=INR)(?=\d)', ' ',parts[i])
    return ''.join(parts)
def haversine(lon1,lat1,lon2,lat2):
    p,q=math.radians(lat1),math.radians(lat2)
    a=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(lon2-lon1)/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(a)))
