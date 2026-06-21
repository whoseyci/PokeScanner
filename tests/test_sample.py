import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_sample_cli_json():
    out = subprocess.check_output([sys.executable, str(ROOT / 'scan.py'), '0196214137158', '--fixture', '--json'], cwd=ROOT)
    data = json.loads(out)
    assert data['barcode']['valid'] is True
    assert data['candidate_count'] >= 2
    assert data['candidates'][0]['price']['from_price_eur'] == 3.30
