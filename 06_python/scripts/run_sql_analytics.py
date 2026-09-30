"""Run named, read-only Phase 3 business questions and reconcile the marts."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / '05_sql/phase3_business_questions.sql'
DB = ROOT / '03_data/processed/waste.duckdb'
OUT = ROOT / '14_outputs/tables/phase3_sql'


def named_queries():
    source = SQL.read_text(encoding='utf-8')
    matches = list(re.finditer(r'^-- query_id: ([a-z0-9_]+)\s*$', source, re.M))
    if len(matches) != 14:
        raise ValueError(f'Expected 14 named questions; found {len(matches)}')
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        statement = source[match.end():end].strip()
        if not statement.endswith(';') or 'BUSINESS PURPOSE:' not in statement:
            raise ValueError(f'Incomplete query {match.group(1)}')
        yield match.group(1), statement


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(DB), read_only=True)
    manifest = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                'database': str(DB.relative_to(ROOT)),
                'source_sql': str(SQL.relative_to(ROOT)),
                'data_origin': 'synthetic operations; official ward identifiers only',
                'queries': []}
    try:
        for name, statement in named_queries():
            frame = connection.execute(statement).df()
            if frame.empty and name != '10_local_anomalies':
                raise AssertionError(f'{name} unexpectedly returned no rows')
            if name != '12_reconciliation':
                frame['data_origin'] = 'synthetic'
            path = OUT / f'{name}.csv'
            frame.to_csv(path, index=False)
            manifest['queries'].append({'query_id': name, 'rows': len(frame),
                                        'columns': list(frame.columns),
                                        'local_path': str(path.relative_to(ROOT))})
            print(name, len(frame), flush=True)
            if name == '12_reconciliation':
                values = frame.iloc[0]
                counts = [int(values[x]) for x in ['fact_scheduled_readings',
                    'truth_scheduled_readings', 'bin_mart_scheduled_readings',
                    'zone_mart_scheduled_readings']]
                if counts != [4_380_000] * 4:
                    raise AssertionError(f'Reading-count reconciliation failed: {counts}')
                if int(values['collection_attempts']) != int(values['bin_mart_attempts']):
                    raise AssertionError('Collection-attempt reconciliation failed')
                litres = [float(values[x]) for x in ['truth_arrivals_l',
                    'bin_mart_arrivals_l', 'zone_mart_arrivals_l']]
                if max(litres) - min(litres) > 0.001 * max(litres):
                    raise AssertionError(f'Arrival-volume reconciliation failed: {litres}')
                manifest['reconciliation'] = {'reading_counts': counts,
                    'collection_attempts': int(values['collection_attempts']),
                    'arrival_litres': litres, 'passed': True}
    finally:
        connection.close()
    (OUT / 'query_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    run()
