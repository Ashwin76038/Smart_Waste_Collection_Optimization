"""Run reviewed business queries for both cities and each single-city filter."""
from phase4_common import PROJECT_ROOT as ROOT,dump
import duckdb
def run():
    out=ROOT/'14_outputs/tables/city_comparison';out.mkdir(parents=True,exist_ok=True)
    c=duckdb.connect(str(ROOT/'03_data/processed/two_city/two_city.duckdb'),read_only=True);receipt=[]
    for path in sorted((ROOT/'05_sql/city').glob('*.sql')):
        sql=path.read_text(encoding='utf-8')
        for cid in [None,'CHN','CBE']:
            d=c.execute(sql,{'city_id':cid}).df();dest=out/(path.stem+'_'+(cid or 'BOTH')+'.csv');d.to_csv(dest,index=False)
            receipt.append({'query':path.name,'city_filter':cid,'rows':len(d),'output':dest.relative_to(ROOT).as_posix()})
    dump(out/'query_receipt.json',receipt);c.close();print('24 city-aware query executions completed')
if __name__=='__main__':run()
