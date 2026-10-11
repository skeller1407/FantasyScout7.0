import os, json
from urllib.request import Request, urlopen

class KickbaseProvider:
    """Official-provider boundary. Set KICKBASE_PROVIDER_URL only when an
    authorized/official endpoint is available for the deployment."""
    def fetch_values(self):
        url=os.getenv("KICKBASE_PROVIDER_URL")
        if not url:
            return {}, "Kickbase-Provider nicht konfiguriert (bewusst kein Web-Scraping)."
        req=Request(url, headers={"Accept":"application/json", "User-Agent":"FantasyScout/1.0"})
        try:
            with urlopen(req, timeout=15) as r: data=json.loads(r.read().decode())
            values=data.get("players", data if isinstance(data,list) else [])
            out={}
            for p in values:
                if p.get("name") is not None and p.get("marketValue") is not None:
                    out[normalize(p["name"])] = int(p["marketValue"])
            return out, None
        except Exception as exc:
            return {}, f"Kickbase-Provider: {exc}"

def normalize(value):
    import unicodedata, re
    value=unicodedata.normalize("NFKD",value).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","",value)
