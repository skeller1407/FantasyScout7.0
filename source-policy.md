# Source policy

FantasyScout uses a provider boundary per source. The Android app does not scrape third-party sites directly.

- Bundesliga: public roster facts only.
- Kicker: RSS where available; show title/summary/source/link and open the original.
- Comunio: public statistics are used only where permitted; verify terms before production deployment.
- Kickbase: only an authorized/offical endpoint. No reverse engineering or credential harvesting.
- LigaInsider/Sport1/Sky: add only through permitted feeds/APIs/licensed access; do not copy full articles.
