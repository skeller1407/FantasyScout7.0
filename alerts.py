from datetime import datetime, timezone

def build_alerts(news, players):
    favorite_ids = {p["id"] for p in players if p.get("favorite")}
    names = {p.get("id"): p.get("name") for p in players}
    alerts=[]
    for n in news:
        pid=n.get("playerId")
        if not pid or (favorite_ids and pid not in favorite_ids):
            continue
        rel=n.get("relevance")
        if rel in {"high_negative","watch","positive"}:
            alerts.append({"id":n["id"],"playerId":pid,"playerName":names.get(pid),"type":rel,"title":n["title"],"source":n["source"],"url":n["url"],"createdAt":datetime.now(timezone.utc).isoformat()})
    return alerts
