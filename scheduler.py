"""Simple production-friendly polling loop.
Run with: python scheduler.py
Set FANTASYSCOUT_INTERVAL_SECONDS (default 900) to change the interval.
Use a process manager/systemd/container in production.
"""
import os, time, json
from server import sync
from state import detect_changes

INTERVAL = int(os.environ.get('FANTASYSCOUT_INTERVAL_SECONDS', '900'))

if __name__ == '__main__':
    print(f'FantasyScout scheduler: every {INTERVAL}s')
    while True:
        try:
            payload = sync()
            changes = detect_changes(payload)
            payload['changes'] = changes
            print(json.dumps({'syncedAt': payload['syncedAt'], 'changes': len(changes), 'warnings': payload['warnings']}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        time.sleep(INTERVAL)
