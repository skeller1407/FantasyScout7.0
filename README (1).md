# FantasyScout Android

FantasyScout is an Android companion app for Bundesliga fantasy-manager users.

## v9 live update architecture

- Android WorkManager schedules a 15-minute background sync.
- Configure the backend base URL in the app's SharedPreferences under `backend_url` (or wire it into the Settings UI).
- The backend scheduler can independently poll providers every 15 minutes.
- Meaningful changes are deduplicated using `backend/state.py` before they become alerts.
- Provider credentials must remain on the backend; never ship them in the APK.

## Sources

Kicker RSS can be consumed where its feed terms permit it. LigaInsider status data should be connected only through an authorized feed/API or other permitted access path. Comunio and Kickbase market-value access should likewise use permitted/official access.

## v13 Beta
Die Android-Oberfläche verwendet jetzt den Live-Backend-Vertrag `/v1/data`, cached den letzten Snapshot lokal und zeigt Fantasy-Score, Marktwert, Status und Favoriten-News. Die frühere Demo-Spielerliste ist nicht mehr Bestandteil des produktiven Datenpfads.

## v15
Das Dashboard enthält managerabhängige Kauf-, Halte-, Gewinner-, Verlierer- und Risiko-Rankings.
