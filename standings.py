"""Public Bundesliga standings reader based on Bundesliga.com.
If the page structure changes, return an empty table rather than inventing ranks.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
import re

URL = "https://www.bundesliga.com/de/bundesliga/tabelle/2026-2027/1/table?view=full"

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self, data):
        s=re.sub(r"\s+"," ",data).strip()
        if s: self.parts.append(s)

ALIASES = {
    "BVB Dortmund Borussia Dortmund":"Borussia Dortmund", "FCB Bayern FC Bayern München":"FC Bayern München",
    "SCF Freiburg Sport-Club Freiburg":"Sport-Club Freiburg", "FCA Augsburg FC Augsburg":"FC Augsburg",
    "B04 Leverkusen Bayer 04 Leverkusen":"Bayer 04 Leverkusen", "M05 Mainz 1. FSV Mainz 05":"1. FSV Mainz 05",
    "ELV Elversberg SV Elversberg":"SV Elversberg", "SVW Bremen SV Werder Bremen":"SV Werder Bremen",
    "RBL Leipzig RB Leipzig":"RB Leipzig", "SGE Frankfurt Eintracht Frankfurt":"Eintracht Frankfurt",
    "S04 Schalke FC Schalke 04":"FC Schalke 04", "SCP Paderborn SC Paderborn 07":"SC Paderborn 07",
    "KOE Köln 1. FC Köln":"1. FC Köln", "TSG Hoffenheim TSG Hoffenheim":"TSG Hoffenheim",
    "VFB Stuttgart VfB Stuttgart":"VfB Stuttgart", "HSV Hamburg Hamburger SV":"Hamburger SV",
    "FCU Union Berlin 1. FC Union Berlin":"1. FC Union Berlin", "BMG M'gladbach Borussia Mönchengladbach":"Borussia Mönchengladbach",
}

def fetch_standings():
    req=Request(URL,headers={"User-Agent":"FantasyScout/1.0 standings reader"})
    with urlopen(req,timeout=12) as r: raw=r.read().decode("utf-8","ignore")
    p=TextParser(); p.feed(raw)
    text=" ".join(p.parts)
    result={}
    # Current official page exposes club labels together with the rank.
    for label, club in ALIASES.items():
        pos = text.find(label)
        if pos >= 0:
            before=text[max(0,pos-80):pos]
            nums=re.findall(r"\b(?:[1-9]|1[0-8])\b", before)
            if nums:
                rank=int(nums[-1])
                if 1 <= rank <= 18: result[club]=rank
    return result

def strength_from_rank(rank):
    if not isinstance(rank,int): return None
    if rank <= 4: return 5
    if rank <= 8: return 4
    if rank <= 12: return 3
    if rank <= 15: return 2
    return 1
