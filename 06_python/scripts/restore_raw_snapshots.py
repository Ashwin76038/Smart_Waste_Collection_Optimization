"""Restore recorded immutable raw assets; refuse changed remote bytes."""
from pathlib import Path
import csv,hashlib,requests
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 for row in csv.DictReader((ROOT/'02_research/acquisition_manifest.csv').open(encoding='utf-8-sig')):
  p=ROOT/row['local_path'];p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():
   if sha(p)!=row['sha256']:raise ValueError('Existing snapshot mismatch: '+str(p))
   continue
  temp=p.with_suffix(p.suffix+'.part')
  try:
   with requests.get(row['resource_url'],stream=True,timeout=(20,120)) as response:
    response.raise_for_status()
    with temp.open('wb') as f:
     for chunk in response.iter_content(1024*1024):f.write(chunk)
   if sha(temp)!=row['sha256']:raise ValueError('Remote bytes changed; obtain recorded snapshot or create a versioned new acquisition: '+row['source_id'])
   temp.replace(p)
  finally:
   if temp.exists():temp.unlink()
if __name__=='__main__':main()
