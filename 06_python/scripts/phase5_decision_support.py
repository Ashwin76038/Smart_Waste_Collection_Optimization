"""Persist the two decision-support SQL result sets used in Phase 5 guidance."""
from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parents[2]

def run():
    sql=(ROOT/'05_sql/phase5_decision_support.sql').read_text(encoding='utf-8')
    parts=[s.strip() for s in sql.split(';') if s.strip()]
    assert len(parts)==2
    c=duckdb.connect(str(ROOT/'03_data/processed/two_city/two_city.duckdb'),read_only=True)
    out=ROOT/'12_powerbi/phase5_model'
    for q,name in zip(parts,['ward_audit_candidates.csv','threshold_tradeoffs.csv']):
        d=c.execute(q).df();d.to_csv(out/name,index=False)
        print(name,len(d))
    c.close()

if __name__=='__main__':run()
