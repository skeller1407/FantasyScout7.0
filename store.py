import json, os, tempfile
from datetime import datetime, timezone

DATA_FILE = os.environ.get('FANTASYSCOUT_DATA', os.path.join(os.path.dirname(__file__), 'runtime', 'latest.json'))

def save(payload):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='latest-', suffix='.json', dir=os.path.dirname(DATA_FILE))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)

def load():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'players': [], 'news': [], 'alerts': [], 'syncedAt': None, 'warnings': ['Noch kein erfolgreicher Sync vorhanden.']}
