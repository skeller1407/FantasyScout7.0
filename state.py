import json, os, tempfile
from datetime import datetime, timezone

STATE_FILE = os.environ.get('FANTASYSCOUT_STATE', os.path.join(os.path.dirname(__file__), 'runtime', 'state.json'))

def _load():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'players': {}, 'news': {}, 'updatedAt': None}

def _save(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    fd, path = tempfile.mkstemp(prefix='state-', suffix='.json', dir=os.path.dirname(STATE_FILE))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(path, STATE_FILE)

def detect_changes(payload):
    old = _load()
    changed = []
    for p in payload.get('players', []):
        pid = p.get('id')
        if not pid:
            continue
        before = old['players'].get(pid, {})
        if before.get('status') and before.get('status') != p.get('status'):
            changed.append({'kind':'status_change','playerId':pid,'from':before.get('status'),'to':p.get('status')})
    for n in payload.get('news', []):
        nid = n.get('id')
        if nid and nid not in old['news']:
            changed.append({'kind':'new_news','newsId':nid,'playerId':n.get('playerId'),'relevance':n.get('relevance')})
    state = {'players': {p.get('id'): p for p in payload.get('players', []) if p.get('id')},
             'news': {n.get('id'): n for n in payload.get('news', []) if n.get('id')},
             'updatedAt': datetime.now(timezone.utc).isoformat()}
    _save(state)
    return changed
