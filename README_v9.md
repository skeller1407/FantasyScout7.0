# Live update operation

1. Configure authorized provider endpoints in environment variables.
2. Start the API with `python server.py`.
3. Start the scheduler with `python scheduler.py`.
4. The default polling interval is 900 seconds (15 minutes).
5. `state.json` stores the last observed player/news state and is used to detect actual changes.
6. Only favorite-player changes with meaningful relevance should become Android pushes.

For production, run the scheduler behind systemd, Docker, or another process supervisor. Do not expose provider credentials to the Android client.
