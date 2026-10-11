import re
import unicodedata
from collections import defaultdict

SOURCE_WEIGHTS = {
    "LigaInsider": 1.25,
    "Kicker": 1.15,
    "Bundesliga.com": 1.10,
    "Sky Sport": 1.00,
    "Sport1": 0.95,
}

STOP = {"der","die","das","den","dem","des","und","oder","ein","eine","einer","einem","einen","mit","von","für","bei","nach","vor","aus","auf","zur","zum","im","in","am","an","ist","sind","wird","hat","haben","noch","nun","mehr","über","gegen","wie","als","auch"}

def norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()

def tokens(text):
    return {t for t in norm(text).split() if len(t) > 2 and t not in STOP}

def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def cluster_news(news):
    """Merge near-duplicate reports while retaining source evidence."""
    clusters = []
    for item in sorted(news, key=lambda x: x.get("publishedAt") or "", reverse=True):
        best = None
        best_score = 0.0
        for cluster in clusters:
            representative = cluster[0]
            same_player = item.get("playerId") and item.get("playerId") == representative.get("playerId")
            same_team = item.get("team") and item.get("team") == representative.get("team")
            sim = similarity(item.get("title", ""), representative.get("title", ""))
            threshold = 0.38 if same_player else 0.55
            score = sim + (0.18 if same_player else 0) + (0.05 if same_team else 0)
            if score >= threshold and score > best_score:
                best, best_score = cluster, score
        if best is None:
            clusters.append([item])
        else:
            best.append(item)

    result = []
    for idx, cluster in enumerate(clusters):
        # Prefer the strongest source as the canonical headline.
        cluster.sort(key=lambda x: (SOURCE_WEIGHTS.get(x.get("source"), 0.5), len(x.get("summary", ""))), reverse=True)
        primary = dict(cluster[0])
        sources = []
        for item in cluster:
            source = item.get("source") or "Unbekannt"
            if source not in sources:
                sources.append(source)
        primary["sources"] = sources
        primary["sourceCount"] = len(sources)
        primary["reportCount"] = len(cluster)
        primary["clusterId"] = f"news-{idx+1}"
        primary["sourceWeight"] = round(sum(SOURCE_WEIGHTS.get(x.get("source"), 0.5) for x in cluster), 2)
        primary["evidence"] = " · ".join(sources)
        # Combine useful snippets without copying full articles.
        snippets = []
        for item in cluster:
            summary = (item.get("summary") or "").strip()
            if summary and summary not in snippets:
                snippets.append(summary[:240])
        primary["summary"] = snippets[0] if snippets else primary.get("summary", "")
        result.append(primary)
    return result

def daily_player_digest(news):
    grouped = defaultdict(list)
    for item in news:
        if item.get("playerId"):
            grouped[item["playerId"]].append(item)
    digests = {}
    for player_id, items in grouped.items():
        items = sorted(items, key=lambda x: (x.get("relevanceScore", 0), x.get("sourceWeight", 0)), reverse=True)
        negative = sum(1 for x in items if x.get("relevance") == "high_negative")
        watch = sum(1 for x in items if x.get("relevance") == "watch")
        positive = sum(1 for x in items if x.get("relevance") == "positive")
        if negative:
            headline = "Kritische Entwicklung"
        elif watch:
            headline = "Einsatzlage beobachten"
        elif positive:
            headline = "Positive Signale"
        else:
            headline = "Aktuelle Meldungen"
        sources = []
        for item in items:
            for source in item.get("sources", [item.get("source")]):
                if source and source not in sources:
                    sources.append(source)
        digests[player_id] = {
            "headline": headline,
            "newsCount": len(items),
            "sourceCount": len(sources),
            "sources": sources,
            "topTitle": items[0].get("title", ""),
            "hasInjurySignal": any(x.get("injury") for x in items),
            "relevance": "high_negative" if negative else "watch" if watch else "positive" if positive else "info",
        }
    return digests
