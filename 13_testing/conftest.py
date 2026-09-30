from pathlib import Path
import duckdb,pytest
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture(scope='session')
def db():
 c=duckdb.connect(str(ROOT/'03_data/processed/waste.duckdb'),read_only=True)
 yield c
 c.close()
