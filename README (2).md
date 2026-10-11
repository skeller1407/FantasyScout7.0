# FantasyScout Live Backend – v7

## Neu in v7
- Spieler-Matching für News anhand von Namen + Verein.
- Klassifizierung der News: `positive`, `watch`, `high_negative`, `info`.
- Erklärbarer Fantasy-Score als eigener Dienst.
- Alert-Objekte werden nur für relevante Spieler-News erzeugt.
- Keine Push-Mitteilung für normale Informationsartikel.

## Datenquellen
- Bundesliga: öffentliche Spieler-Stammdaten.
- Comunio: öffentliche Statistikseite für Marktwerte; für Community-spezifische Funktionen kann der offizielle Comunio-Webservice mit Service-Key genutzt werden.
- Kicker: RSS-Feeds für News.
- Kickbase: kein Scraping; produktiv nur über eine autorisierte/offizielle Schnittstelle.

## Beispiel-API
`GET /v1/sync` liefert:
- `players`
- `news` inklusive `playerId`, `matchConfidence`, `relevance`, `relevanceScore`
- `alerts`
- `warnings`
- `syncedAt`

## Push-Regel
Ein Alert wird nur erzeugt, wenn eine News einem Spieler sicher genug zugeordnet werden konnte und die Relevanz `positive`, `watch` oder `high_negative` ist. Normale `info`-Meldungen lösen keinen Push aus.

## Sicherheit
Keine Drittanbieter-Zugangsdaten in die Android-App einbauen. Provider-Zugangsdaten gehören ausschließlich auf den Server. Nutzungsbedingungen und Lizenzen jeder Quelle müssen vor produktivem Betrieb geprüft werden.

## LigaInsider
The app includes a dedicated provider boundary for LigaInsider. For production, configure `FANTASYSCOUT_LIGAINSIDER_URL` only with an authorized/licensed feed or API endpoint. The default build does not scrape protected LigaInsider pages.
