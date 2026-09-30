"""Validate PBIR files against Microsoft's public JSON schemas."""
from pathlib import Path
import json, requests, jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'work/powerbi_setup/schema_cache'
CACHE.mkdir(parents=True,exist_ok=True)
def get(url):
    rel=url.split('/json-schemas/')[-1].replace('schema.embedded.json','schema-embedded.json')
    p=CACHE/rel
    if not p.exists():
        r=requests.get('https://raw.githubusercontent.com/microsoft/json-schemas/main/'+rel,timeout=45)
        r.raise_for_status();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r.text,encoding='utf-8')
    return json.loads(p.read_text(encoding='utf-8'))
checked=0;errors=[]
for p in (ROOT/'12_powerbi/desktop_project').rglob('*'):
    if p.suffix not in ('.json','.pbir','.pbip','.pbism'):continue
    obj=json.loads(p.read_text(encoding='utf-8'))
    if '$schema' not in obj:continue
    url=obj['$schema'];sc=get(url)
    registry=Registry(retrieve=lambda uri: Resource.from_contents(get(uri), default_specification=DRAFT7))
    es=list(jsonschema.Draft7Validator(sc,registry=registry).iter_errors(obj))
    for e in es:errors.append({'file':str(p.relative_to(ROOT)),'path':list(e.path),'message':e.message})
    checked+=1
receipt={'checked_files':checked,'errors':errors}
(ROOT/'12_powerbi/desktop_project/schema_validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2));assert not errors
