from html.parser import HTMLParser
from urllib.request import Request, urlopen
import re

URL = "https://stats.comunio.de/"

def money(value):
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_row=False; self.cells=[]; self.rows=[]; self.in_cell=False; self.buf=[]
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.in_row=True; self.cells=[]
        elif self.in_row and tag in ("td","th"): self.in_cell=True; self.buf=[]
    def handle_data(self, data):
        if self.in_cell: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag in ("td","th") and self.in_cell:
            self.cells.append(re.sub(r"\s+", " ", "".join(self.buf)).strip()); self.in_cell=False
        elif tag == "tr" and self.in_row:
            if self.cells: self.rows.append(self.cells)
            self.in_row=False

def fetch_player_rows():
    """Read player market values from the public Comstats statistics tables.

    The tables include several rank columns before the player name. Do not use
    the first column as the player name or the first number as the market value.
    """
    req = Request(URL, headers={"User-Agent":"FantasyScout/1.0"})
    with urlopen(req, timeout=20) as r: raw=r.read()
    p=TableParser(); p.feed(raw.decode("utf-8","ignore"))
    result={}
    ignored={"spieler", "player", "club", "verein", "marktwert", "market value", "rang", "punkte", "veränderung"}
    for row in p.rows:
        if len(row) < 3: continue
        # Rank cells are usually just numbers; the first non-rank text cell is
        # the player name (e.g. rows contain 1. | 1. | 1. | Kane | | 23.840.000).
        name = next((c for c in row if c and re.search(r"[A-Za-zÀ-ž]", c)
                     and c.strip().lower() not in ignored
                     and not re.search(r"(?:marktwert|spieler|veränderung|punkte)", c, re.I)), None)
        if not name: continue
        candidates=[]
        for cell in row:
            value=(cell or "").strip()
            if "€" in value or re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", value):
                amount=money(value)
                if amount and amount >= 1000: candidates.append(amount)
        if candidates:
            # Market values are the large grouped numbers; point/rank columns
            # are deliberately excluded by the grouped-number check.
            result[normalize(name)] = {"name": name, "marketValue": max(candidates)}
    return result

def fetch_values():
    return {key: row["marketValue"] for key, row in fetch_player_rows().items()}

def normalize(value):
    import unicodedata
    value=unicodedata.normalize("NFKD",value).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","",value)
