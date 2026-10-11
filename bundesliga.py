from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen
import re, unicodedata

URL = "https://www.bundesliga.com/de/bundesliga/spieler"

@dataclass
class Player:
    id: str
    name: str
    club: str
    position: str

class BundesligaParser(HTMLParser):
    """Best-effort parser for the public Bundesliga player page.
    It intentionally extracts only public roster facts; no private/API data."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.current_club = None
        self.position = None
        self.players = []
        self.capture = 0
        self.buf = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        if self.capture == 0 and tag in ("h2", "h3", "h4"):
            self.capture = 1; self.buf = []
        elif tag == "a":
            href = attrs.get("href", "")
            if "/spieler/" in href or "/player/" in href:
                self.capture = 2; self.buf = []
                self.href = href

    def handle_data(self, data):
        s = re.sub(r"\s+", " ", data).strip()
        if not s: return
        if self.capture: self.buf.append(s)

    def handle_endtag(self, tag):
        if self.capture and tag in ("h2", "h3", "h4"):
            value = " ".join(self.buf).strip()
            low = value.lower()
            if low in {"torhüter", "goalkeepers"}: self.position = "TW"
            elif low in {"verteidigung", "defenders"}: self.position = "ABW"
            elif low in {"mittelfeld", "midfielders"}: self.position = "MF"
            elif low in {"angriff", "strikers"}: self.position = "ST"
            elif value and len(value) < 80 and not re.search(r"\d", value):
                # Club headings are usually larger; only change club when no player href is active.
                self.current_club = value
            self.capture = 0
        elif self.capture == 2 and tag == "a":
            name = " ".join(self.buf).strip()
            if name and self.current_club and self.position:
                pid = normalize(name) + "|" + normalize(self.current_club)
                self.players.append(Player(pid, name, self.current_club, self.position))
            self.capture = 0

def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", value)

def fetch_players():
    req = Request(URL, headers={"User-Agent": "FantasyScout/1.0 (data aggregation client)"})
    with urlopen(req, timeout=20) as r:
        raw = r.read()
    parser = BundesligaParser(); parser.feed(raw.decode("utf-8", "ignore"))
    # Deduplicate noisy/duplicate DOM entries.
    out = {p.id: p for p in parser.players}
    return list(out.values())
