import re, unicodedata

INJURY_TERMS = ["verletz", "ausfall", "angeschlagen", "musk", "knie", "sprunggelenk", "oberschenkel", "wade", "rücken", "schulter", "erkält", "krank"]
POSITIVE_TERMS = ["training", "mannschaftstraining", "zurück", "comeback", "einsatzbereit", "startelf", "fit"]
SUSPENSION_TERMS = ["gesperrt", "sperre", "rote karte", "gelbsperre"]
QUESTION_TERMS = ["fraglich", "unsicher", "entscheidung", "einsatzchance", "belastungssteuerung"]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def tokens(text: str):
    return set(norm(text).split())


def match_player(title: str, summary: str, players):
    hay = f"{title} {summary}"
    nh = norm(hay)
    best = None
    best_score = 0
    for p in players:
        n = norm(p["name"])
        if not n:
            continue
        score = 0
        if re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", nh):
            score += 100
        else:
            pt = tokens(p["name"])
            ht = tokens(hay)
            if pt and pt.issubset(ht):
                score += 70
            elif len(pt) == 1 and next(iter(pt)) in ht:
                score += 25
        club = norm(p["club"])
        if club and club in nh:
            score += 10
        if score > best_score:
            best, best_score = p, score
    return (best, best_score) if best_score >= 25 else (None, 0)


def classify(title: str, summary: str):
    text = norm(f"{title} {summary}")
    injury = any(x in text for x in INJURY_TERMS)
    suspension = any(x in text for x in SUSPENSION_TERMS)
    positive = any(x in text for x in POSITIVE_TERMS)
    question = any(x in text for x in QUESTION_TERMS)
    if suspension or (injury and any(x in text for x in ["ausfall", "verletzt", "fällt", "fehlt"])):
        relevance, score = "high_negative", -3
    elif injury or question:
        relevance, score = "watch", -1
    elif positive:
        relevance, score = "positive", 2
    else:
        relevance, score = "info", 0
    return relevance, score, injury or suspension
