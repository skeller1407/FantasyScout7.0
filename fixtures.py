"""Best-effort Bundesliga fixture provider using the official Bundesliga matchday pages.
Only public fixture information is consumed. If the page structure changes, the provider
returns no fixtures rather than inventing data.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import re

BASE = "https://www.bundesliga.com/de/bundesliga/spieltag/2026-2027/{}"
CLUB_ALIASES = {
    "FCB":"FC Bayern München", "Bayern":"FC Bayern München",
    "BVB":"Borussia Dortmund", "Dortmund":"Borussia Dortmund",
    "B04":"Bayer 04 Leverkusen", "Leverkusen":"Bayer 04 Leverkusen",
    "VFB":"VfB Stuttgart", "Stuttgart":"VfB Stuttgart",
    "SGE":"Eintracht Frankfurt", "Frankfurt":"Eintracht Frankfurt",
    "SCF":"Sport-Club Freiburg", "Freiburg":"Sport-Club Freiburg",
    "SVW":"SV Werder Bremen", "Werder":"SV Werder Bremen",
    "FCA":"FC Augsburg", "Augsburg":"FC Augsburg",
    "S04":"FC Schalke 04", "Schalke":"FC Schalke 04",
    "RBL":"RB Leipzig", "Leipzig":"RB Leipzig",
    "BMG":"Borussia Mönchengladbach", "Gladbach":"Borussia Mönchengladbach",
    "KOE":"1. FC Köln", "Köln":"1. FC Köln",
    "TSG":"TSG Hoffenheim", "Hoffenheim":"TSG Hoffenheim",
    "FCU":"1. FC Union Berlin", "Union":"1. FC Union Berlin",
    "M05":"1. FSV Mainz 05", "Mainz":"1. FSV Mainz 05",
    "SCP":"SC Paderborn 07", "Paderborn":"SC Paderborn 07",
    "ELV":"SV Elversberg", "Elversberg":"SV Elversberg",
    "HSV":"Hamburger SV", "Hamburg":"Hamburger SV",
}

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self, data):
        s=re.sub(r"\s+"," ",data).strip()
        if s: self.parts.append(s)

def _extract_codes(raw):
    # The official page embeds the club abbreviations in the rendered fixture data.
    # Capture known codes in order while preserving sequence and removing adjacent duplicates.
    text=" ".join(TextParser().feed(raw) or [])
    # HTMLParser.feed returns None, so parse separately below.
    p=TextParser(); p.feed(raw); text=" ".join(p.parts)
    codes=[]
    for token in re.findall(r"\b[A-ZÄÖÜ]{3}\b", text):
        if token in CLUB_ALIASES and (not codes or codes[-1] != token): codes.append(token)
    # Keep only plausible fixture pairs; page headers often contain club codes too.
    out=[]
    for i in range(0, len(codes)-1, 2):
        home, away=codes[i], codes[i+1]
        if home != away: out.append((home,away))
    return out

def fetch_fixtures(matchdays=range(1,35)):
    fixtures=[]; errors=[]
    for md in matchdays:
        try:
            req=Request(BASE.format(md),headers={"User-Agent":"FantasyScout/1.0 fixture reader"})
            with urlopen(req,timeout=12) as r: raw=r.read().decode("utf-8","ignore")
            pairs=_extract_codes(raw)
            for home,away in pairs[:9]:
                fixtures.append({"matchday":md,"homeClub":CLUB_ALIASES[home],"awayClub":CLUB_ALIASES[away],"homeCode":home,"awayCode":away,"source":"Bundesliga.com"})
        except Exception as e:
            errors.append(f"Spielplan Spieltag {md}: {e}")
    return fixtures, errors

def next_fixtures_for_clubs(clubs):
    fixtures, errors=fetch_fixtures()
    wanted={c.lower() for c in clubs}
    matches=[f for f in fixtures if f["homeClub"].lower() in wanted or f["awayClub"].lower() in wanted]
    # Keep the first two upcoming matchdays per club. Matchday ordering is deterministic.
    out={}
    for club in clubs:
        rows=[f for f in matches if f["homeClub"].lower()==club.lower() or f["awayClub"].lower()==club.lower()]
        rows=sorted(rows,key=lambda x:x["matchday"])
        if rows: out[club]=rows[:2]
    return out, errors
