"""Retained evidence must fail closed on tampering and invalid paired trials."""
import hashlib
import json
import shutil

import pytest

from dynnav_dashboard.audit_evidence import AUDIT, FILES, ROOT, load_audit


def copy_packet(tmp_path):
    shutil.copy(AUDIT / 'artifact_index.json', tmp_path)
    for name in FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(AUDIT / name, target)
    return tmp_path


def reindex(directory, name):
    path = directory / 'artifact_index.json'
    index = json.loads(path.read_text())
    data = (directory / name).read_bytes()
    for entry in index['artifacts']:
        if entry['path'] == name:
            entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    path.write_text(json.dumps(index))


def test_retained_packet_has_real_paired_rows_and_uncertainty():
    packet = load_audit()
    assert packet['trial_rows'] == 96 * 250 * 4
    assert packet['effect']['sample_size'] == 96
    assert packet['effect']['lower'] < packet['effect']['estimate'] < packet['effect']['upper']
    assert len(packet['code_revision']) == 40


@pytest.mark.parametrize('name', FILES)
def test_corruption_is_rejected(tmp_path, name):
    root = copy_packet(tmp_path)
    with (root / name).open('ab') as f:
        f.write(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        load_audit(root)


def test_duplicate_raw_pair_rejected_even_with_updated_checksum(tmp_path):
    root = copy_packet(tmp_path)
    name = 'unavoidable_96/trials.csv'
    lines = (root / name).read_text().splitlines()
    lines[2] = lines[1]
    (root / name).write_text('\n'.join(lines) + '\n')
    reindex(root, name)
    with pytest.raises(ValueError, match='duplicate'):
        load_audit(root)


def test_missing_pair_rejected_even_with_updated_checksum(tmp_path):
    root = copy_packet(tmp_path)
    name = 'unavoidable_96/trials.csv'
    lines = (root / name).read_text().splitlines()
    (root / name).write_text('\n'.join(lines[:-1]) + '\n')
    reindex(root, name)
    with pytest.raises(ValueError, match='Incomplete'):
        load_audit(root)


def test_results_and_publication_pages_render_verified_audit():
    from streamlit.testing.v1 import AppTest
    for page in ['11_Results_Reports.py', '14_Publication_Evidence.py']:
        app = AppTest.from_file(str(ROOT / 'app/pages' / page)).run(timeout=30)
        assert not app.exception
        assert any('paired raw-trial' in item.value for item in app.success)
