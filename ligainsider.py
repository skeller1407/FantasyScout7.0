"""LigaInsider provider boundary.

The provider intentionally does not scrape LigaInsider by default. Set
FANTASYSCOUT_LIGAINSIDER_URL to an authorized/licensed JSON endpoint or feed
provided for your deployment. This keeps the app independent from protected
web pages while allowing the source to be integrated cleanly.
"""
import os, json
from urllib.request import Request, urlopen

class LigaInsiderProvider:
    def __init__(self, url=None):
        self.url = url or os.getenv("FANTASYSCOUT_LIGAINSIDER_URL")

    def fetch_statuses(self):
        if not self.url:
            return {}, "LigaInsider: kein autorisierter Feed/Endpoint konfiguriert"
        req = Request(self.url, headers={"User-Agent": "FantasyScout/1.0"})
        try:
            with urlopen(req, timeout=10) as r:
                payload = json.loads(r.read())
            return payload.get("players", payload), None
        except Exception as e:
            return {}, f"LigaInsider: {e}"
