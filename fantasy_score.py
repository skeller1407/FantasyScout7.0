# Simple explainable fantasy score; later this can be replaced by a trained model.

def calculate(status="unknown", news_scores=None, market_delta=0, starting_probability=None):
    score = 50
    reasons = []
    if status in ("injured", "suspended"):
        score -= 35; reasons.append("Ausfallrisiko")
    elif status in ("doubtful", "questionable"):
        score -= 15; reasons.append("Einsatz fraglich")
    elif status in ("fit", "available"):
        score += 8; reasons.append("einsatzbereit")
    if starting_probability is not None:
        if starting_probability >= 80: score += 15; reasons.append("hohe Startelfchance")
        elif starting_probability < 50: score -= 10; reasons.append("geringe Startelfchance")
    if news_scores:
        score += max(-25, min(25, sum(news_scores)))
    if market_delta > 0: score += 3; reasons.append("Marktwert steigt")
    elif market_delta < 0: score -= 2; reasons.append("Marktwert fällt")
    score = max(0, min(100, score))
    label = "Kaufen/halten" if score >= 70 else "Beobachten" if score >= 45 else "Risiko"
    return {"score": score, "label": label, "reasons": reasons}
