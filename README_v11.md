# FantasyScout v11 – Live-Daten-Backend

## Endpunkte
- `GET /health` – Server erreichbar
- `GET /v1/sync` – Quellen abrufen, normalisieren, matchen und aktuellen Datensatz speichern
- `GET /v1/data` – zuletzt erfolgreich gespeicherter Datensatz; geeignet für mobile Clients
- `GET /v1/health/providers` – aktivierte Provider-Schichten

## Betrieb
`python scheduler.py` führt standardmäßig alle 900 Sekunden einen Sync aus. Der letzte Datensatz wird atomar unter `backend/runtime/latest.json` gespeichert.

Die Provider für Kickbase und LigaInsider bleiben absichtlich autorisierungsabhängig. Es wird kein geschützter Webauftritt als API vorausgesetzt.
