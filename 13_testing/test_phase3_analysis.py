"""Cross-check published Phase 3 extracts at their declared grains."""
from pathlib import Path
import csv
import math

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_phase3_sql_reconciliation_and_origin(db):
    path = ROOT / '14_outputs/tables/phase3_sql/12_reconciliation.csv'
    with path.open(encoding='utf-8', newline='') as source:
        row = next(csv.DictReader(source))
    counts = [int(float(row[key])) for key in ('fact_scheduled_readings',
        'truth_scheduled_readings', 'bin_mart_scheduled_readings', 'zone_mart_scheduled_readings')]
    assert counts == [4_380_000] * 4
    assert int(row['collection_attempts']) == int(float(row['bin_mart_attempts']))
    assert math.isclose(float(row['truth_arrivals_l']), float(row['zone_mart_arrivals_l']), rel_tol=1e-9)
    with (ROOT / '14_outputs/tables/phase3_sql/01_zone_generation.csv').open(encoding='utf-8', newline='') as source:
        assert all(r['data_origin'] == 'synthetic' for r in csv.DictReader(source))
    assert db.execute('SELECT SUM(arrivals_l_simulated) FROM zone_daily_metrics').fetchone()[0] > 0


def test_weekly_contrasts_recompute_from_city_days():
    days = pd.read_csv(ROOT / '14_outputs/tables/phase3_eda/city_daily.csv', parse_dates=['service_date'])
    pairs = pd.read_csv(ROOT / '07_statistics/weekly_paired_contrasts.csv')
    tests = pd.read_csv(ROOT / '07_statistics/hypothesis_tests.csv').set_index('test_id')
    assert len(days) == 365 and set(days.data_origin) == {'synthetic'}
    assert pairs.groupby('test_id').size().to_dict() == {
        'weekend_generated_mass': 51, 'weekend_overflow_slot_share': 51}
    assert ((pairs.weekend_mean - pairs.weekday_mean - pairs.weekend_minus_weekday).abs() < 1e-8).all()
    for test_id, group in pairs.groupby('test_id'):
        actual = group.weekend_minus_weekday.mean()
        published = tests.loc[test_id]
        assert math.isclose(actual, published.mean_difference, rel_tol=1e-10)
        assert published.ci95_lower < actual < published.ci95_upper
        assert published.p_value_holm >= published.p_value_two_sided
    assert days.scheduled_readings.sum() == 4_380_000


def test_eda_zone_totals_match_mart(db):
    zones = pd.read_csv(ROOT / '14_outputs/tables/phase3_eda/zone_annual_summary.csv', dtype={'zone_id': 'string'})
    assert len(zones) == 199 and set(zones.data_origin) == {'synthetic'}
    published = zones.generated_kg_simulated.sum()
    authoritative = db.execute('SELECT SUM(arrivals_l_simulated) * 0.12 FROM zone_daily_metrics').fetchone()[0]
    assert math.isclose(published, authoritative, rel_tol=1e-10)


def test_timing_flags_reconcile_to_summary():
    early = pd.read_csv(ROOT / '14_outputs/tables/phase3_sql/13_early_bins.csv')
    late = pd.read_csv(ROOT / '14_outputs/tables/phase3_sql/14_late_bins.csv')
    metrics = pd.read_json(ROOT / '14_outputs/tables/phase3_eda/phase3_metrics.json', typ='series')
    assert early.early_successes_lt35_pct.sum() == metrics['early_successes_lt35_pct']
    assert early.early_successes_lt35_pct.gt(0).all()
    assert late.attempts.ge(100).all() and late.late_risk_attempt_pct.between(0, 100).all()
