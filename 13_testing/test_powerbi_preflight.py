"""A source-only checkout must not overwrite the saved Desktop report."""
import ast
import csv
import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / '06_python/scripts/build_powerbi_project.py'


def prepare(tmp_path):
    script = tmp_path / '06_python/scripts/build_powerbi_project.py'
    script.parent.mkdir(parents=True)
    script.write_bytes(SCRIPT.read_bytes())
    saved = tmp_path / '12_powerbi/desktop_project/Smart_Waste_Chennai_Coimbatore.pbip'
    saved.parent.mkdir(parents=True)
    saved.write_bytes(b'authored Desktop project')
    return script, saved


def run(script):
    return subprocess.run([sys.executable, str(script)], capture_output=True, text=True)


def test_missing_exports_leave_project_unchanged(tmp_path):
    script, saved = prepare(tmp_path)
    result = run(script)
    assert result.returncode != 0
    assert 'Missing Power BI exports' in result.stderr
    assert saved.read_bytes() == b'authored Desktop project'
    assert list(saved.parent.iterdir()) == [saved]


def test_invalid_header_leaves_project_unchanged(tmp_path):
    script, saved = prepare(tmp_path)
    tree = ast.parse(SCRIPT.read_text(encoding='utf-8-sig'))
    tables = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'EXPECTED_TABLES'
                          for target in node.targets))
    data = tmp_path / '12_powerbi/phase5_model'
    data.mkdir()
    for table in tables:
        (data / (table + '.csv')).write_text('key,key\n1,2\n', encoding='utf-8')
    result = run(script)
    assert result.returncode != 0
    assert 'Invalid CSV header' in result.stderr
    assert saved.read_bytes() == b'authored Desktop project'
    assert list(saved.parent.iterdir()) == [saved]


def test_complete_export_headers_still_build(tmp_path):
    script, saved = prepare(tmp_path)
    root = SCRIPT.parents[2]
    data = tmp_path / '12_powerbi/phase5_model'
    data.mkdir()
    model_path = root / '12_powerbi/desktop_project/Smart_Waste.SemanticModel/model.bim'
    model = json.loads(model_path.read_text(encoding='utf-8-sig'))['model']
    expected = {table['name'] for table in model['tables']
                if table['name'].startswith(('dim_', 'fact_'))}
    for table in model['tables']:
        if table['name'] not in expected:
            continue
        with (data / (table['name'] + '.csv')).open('w', newline='', encoding='utf-8') as handle:
            csv.writer(handle).writerow([column['sourceColumn'] for column in table['columns']])
    for filename in ['PHASE5_MEASURES.dax', 'phase5_theme.json']:
        (tmp_path / '12_powerbi' / filename).write_bytes((root / '12_powerbi' / filename).read_bytes())
    result = run(script)
    assert result.returncode == 0, result.stderr
    built = json.loads((saved.parent / 'Smart_Waste.SemanticModel/model.bim').read_text())['model']
    assert {table['name'] for table in built['tables']} == expected | {'KPI Measures'}
    assert len(built['relationships']) == 16
