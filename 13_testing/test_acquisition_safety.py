"""Offline acquisition regressions; HTTP is always mocked."""
import importlib.util
from pathlib import Path
import pytest

@pytest.fixture
def acquisition(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / '06_python/scripts/acquire_sources.py'
    spec = importlib.util.spec_from_file_location('acquisition_under_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path / '02_research').mkdir()
    monkeypatch.setattr(module, 'MAN', tmp_path / '02_research/manifest.csv')
    monkeypatch.setattr(module, 'ATT', tmp_path / '02_research/attempts.csv')
    monkeypatch.setattr(module, 'JOBS', [('S05', 'sample.html', 'https://censusindia.gov.in/sample', 'context', 'India', 'NA', 'NA', 'review')])
    def forbidden(*args, **kwargs):
        pytest.fail('Unexpected network request')
    monkeypatch.setattr(module.requests, 'get', forbidden)
    return module


def register(module, content=b'original'):
    destination = module.ROOT / f'03_data/raw/S05/{module.DAY}/sample.html'
    destination.parent.mkdir(parents=True)
    destination.write_bytes(content)
    row = dict.fromkeys(module.FIELDS, '')
    row.update(local_path=destination.relative_to(module.ROOT).as_posix(), sha256=module.sha(destination), extraction_notes='Historical TLS exception retained')
    module.save(module.MAN, module.FIELDS, [row])
    return destination


def test_registered_hash_mismatch_stops_without_network(acquisition):
    destination = register(acquisition)
    manifest = acquisition.MAN.read_bytes()
    destination.write_bytes(b'changed')
    with pytest.raises(ValueError, match='Snapshot integrity failure'):
        acquisition.run()
    assert destination.read_bytes() == b'changed'
    assert acquisition.MAN.read_bytes() == manifest
    assert not acquisition.ATT.exists()


def test_verified_snapshot_preserves_historical_manifest(acquisition):
    register(acquisition)
    manifest = acquisition.MAN.read_bytes()
    acquisition.run()
    assert acquisition.MAN.read_bytes() == manifest


def test_unregistered_snapshot_cannot_be_overwritten(acquisition):
    destination = register(acquisition)
    acquisition.MAN.unlink()
    with pytest.raises(ValueError, match='unregistered raw snapshot'):
        acquisition.run()
    assert destination.read_bytes() == b'original'


def test_fresh_download_creates_work_and_verifies_census_tls(acquisition, monkeypatch):
    calls = []
    class Response:
        headers = {'Content-Type': 'text/html'}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def raise_for_status(self): pass
        def iter_content(self, size): yield b'example public source'
    def fake_get(url, **kwargs):
        calls.append(kwargs)
        return Response()
    monkeypatch.setattr(acquisition.requests, 'get', fake_get)
    assert not (acquisition.ROOT / 'work').exists()
    acquisition.run()
    assert calls[0]['verify'] is True
    rows = acquisition.load(acquisition.MAN, acquisition.FIELDS)
    assert len(rows) == 1
    assert (acquisition.ROOT / rows[0]['local_path']).read_bytes() == b'example public source'
    assert rows[0]['extraction_notes'] == 'Raw untouched. TLS certificate validation enabled.'
    assert not list((acquisition.ROOT / 'work').glob('*.part'))
