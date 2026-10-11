from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
import json, re, hashlib, os
from providers.bundesliga import fetch_players, normalize as norm_player
from providers.comunio import fetch_player_rows as fetch_comunio_players
from providers.kickbase import KickbaseProvider
from providers.ligainsider import LigaInsiderProvider
from providers.standings import fetch_standings, strength_from_rank
from alerts import build_alerts
from matching import match_player, classify
from store import save, load
from fantasy_score import calculate
from news_engine import cluster_news, daily_player_digest

HOST="0.0.0.0"; PORT=int(os.environ.get("PORT", "8080"))
KICKER_FEEDS={
 "bayern":"https://newsfeed.kicker.de/team/fc-bayern-muenchen",
 "dortmund":"https://newsfeed.kicker.de/team/borussia-dortmund",
 "leverkusen":"https://newsfeed.kicker.de/team/bayer-04-leverkusen",
 "stuttgart":"https://newsfeed.kicker.de/team/vfb-stuttgart",
 "frankfurt":"https://newsfeed.kicker.de/team/eintracht-frankfurt",
 "freiburg":"https://newsfeed.kicker.de/team/sc-freiburg",
}

def clean(x): return re.sub(r"\s+"," ",x or "").strip()

def fetch_kicker(team,url,limit=12):
 req=Request(url,headers={"User-Agent":"FantasyScout/1.0 RSS reader"})
 with urlopen(req,timeout=10) as r: root=ET.fromstring(r.read())
 out=[]
 for item in root.findall(".//item")[:limit]:
  title=clean(item.findtext("title")); link=clean(item.findtext("link")); pub=clean(item.findtext("pubDate")); desc=clean(item.findtext("description"))
  if title and link:
   relevance, score, injury = classify(title, desc)
   out.append({"id":hashlib.sha1(link.encode()).hexdigest(),"playerId":None,"source":"Kicker","title":title,"summary":desc[:400],"url":link,"publishedAt":pub,"relevance":relevance,"relevanceScore":score,"injury":injury,"team":team})
 return out

def sync():
 warnings=[]
 previous = load()
 try: players=fetch_players()
 except Exception as e: players=[]; warnings.append(f"Bundesliga-Spieler: {e}")
 try:
  comstats_rows=fetch_comunio_players()
  comunio={key: row["marketValue"] for key,row in comstats_rows.items()}
 except Exception as e:
  comunio={}; comstats_rows={}; warnings.append(f"Comstats: {e}")
 # Comstats also supplies a real-player fallback for names missing from the
 # Bundesliga roster parser. Unknown club/position stay explicitly unknown.
 known={norm_player(p.name) for p in players}
 for key,row in comstats_rows.items():
  if key not in known:
   from providers.bundesliga import Player
   players.append(Player(key, row["name"], "Verein unbekannt", "UNKNOWN"))
   known.add(key)
 kickbase,kerr=KickbaseProvider().fetch_values()
 if kerr: warnings.append(kerr)
 pdata=[]
 previous_players = {p.get("id"): p for p in previous.get("players", []) if p.get("id")}
 for p in players:
  key=norm_player(p.name)
  old = previous_players.get(p.id, {})
  cv = comunio.get(key)
  kv = kickbase.get(key)
  old_cv = old.get("comunioValue")
  old_kv = old.get("kickbaseValue")
  history = list(old.get("marketHistory", []))[-13:]
  history.append({"at": datetime.now(timezone.utc).isoformat(), "comunioValue": cv, "kickbaseValue": kv})
  pdata.append({"id":p.id,"name":p.name,"club":p.club,"position":p.position,"status":"unknown",
                "comunioValue":cv,"kickbaseValue":kv,
                "comunioDelta": (cv-old_cv) if isinstance(cv,(int,float)) and isinstance(old_cv,(int,float)) else None,
                "kickbaseDelta": (kv-old_kv) if isinstance(kv,(int,float)) and isinstance(old_kv,(int,float)) else None,
                "marketHistory":history})
 news=[]
 for team,url in KICKER_FEEDS.items():
  try: news.extend(fetch_kicker(team,url))
  except Exception as e: warnings.append(f"Kicker {team}: {e}")
 for item in news:
  player, confidence = match_player(item["title"], item["summary"], pdata)
  if player:
   item["playerId"] = player["id"]
   item["matchConfidence"] = confidence
 # Optional authorized LigaInsider status feed. No protected-page scraping is performed.
 li_status, li_error = LigaInsiderProvider().fetch_statuses()
 if li_error: warnings.append(li_error)
 for p in pdata:
  status = li_status.get(p["name"]) if isinstance(li_status, dict) else None
  if status:
   p["status"] = status.get("status", status) if isinstance(status, dict) else status

 # Enrich players with the next official Bundesliga fixture.
 fixture_map, fixture_errors = next_fixtures_for_clubs([p["club"] for p in pdata])
 warnings.extend(fixture_errors[:6])
 try:
  standings = fetch_standings()
 except Exception as e:
  standings = {}; warnings.append(f"Bundesliga-Tabelle: {e}")
 for p in pdata:
  rows = fixture_map.get(p["club"], [])
  if rows:
   f = rows[0]
   p["opponent"] = f["awayClub"] if f["homeClub"] == p["club"] else f["homeClub"]
   p["homeMatch"] = f["homeClub"] == p["club"]
   p["matchday"] = f["matchday"]
   p["fixtureSource"] = f["source"]
   p["opponentRank"] = standings.get(p["opponent"])
   p["opponentStrength"] = strength_from_rank(p["opponentRank"])
   p["startingProbability"] = None
  else:
   p["opponent"] = None; p["homeMatch"] = None; p["opponentRank"] = None; p["opponentStrength"] = None; p["startingProbability"] = None

# Explainable fantasy score based on current status and matched news.
 by_player = {}
 for n in news:
  if n.get("playerId"):
   by_player.setdefault(n["playerId"], []).append(n)
 for p in pdata:
  matched = by_player.get(p["id"], [])
  news_scores = []
  for n in matched:
   rel = n.get("relevance")
   if rel == "positive": news_scores.append(5)
   elif rel == "watch": news_scores.append(-4)
   elif rel == "high_negative": news_scores.append(-8)
  market_delta = p.get("comunioDelta") or p.get("kickbaseDelta") or 0
  result = calculate(status=p.get("status", "unknown"), news_scores=news_scores, market_delta=market_delta)
  p["fantasyScore"] = result["score"]
  p["fantasyLabel"] = result["label"]
  p["fantasyReasons"] = result["reasons"]

 # Keep exact duplicates out of the feed.
 dedup = {}
 for item in news:
  key = (item["url"], item["title"].lower())
  dedup[key] = item
 news = list(dedup.values())
 # Aggregate near-duplicate reports and retain source evidence.
 news = cluster_news(news)
 digests = daily_player_digest(news)
 for p in pdata:
  p["dailyNewsDigest"] = digests.get(p["id"], {"headline":"Keine neuen Meldungen","newsCount":0,"sourceCount":0,"sources":[],"topTitle":"","hasInjurySignal":False,"relevance":"info"})
 # Alerts are generated for meaningful items; favorites can be supplied by the client later.
 alerts = build_alerts(news, pdata)
 payload = {"players":pdata,"news":news,"alerts":alerts,"syncedAt":datetime.now(timezone.utc).isoformat(),"warnings":warnings}
 save(payload)
 return payload

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=="/health": self.send_json({"ok":True}); return
  if self.path=="/v1/sync": self.send_json(sync()); return
  if self.path=="/v1/data": self.send_json(load()); return
  if self.path=="/v1/health/providers":
   self.send_json({"providers":["bundesliga","comunio","kickbase-authorized","kicker-rss","ligainsider-authorized"]}); return
  self.send_response(404); self.end_headers()
 def send_json(self,data):
  raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)

if __name__=="__main__":
 print(f"FantasyScout backend listening on http://{HOST}:{PORT}"); ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
