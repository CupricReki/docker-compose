# Optional Prometheus sidecars (Emby / Jellyfin)

The **`embyserver`** stack includes **`emby-exporter`** (`williamclot/emby_exporter`). Set
**`EMBY_EXPORTER_API`** via `/opt/secrets` (sourced by `dc`) or `docker-compose.override.yml`
`env_file` — do not commit the token.

The **`jellyfin`** stack includes **`jellyfin-exporter`** (`rebelcore/jellyfin-exporter`).
Set **`JELLYFIN_EXPORTER_API`** (Jellyfin admin → API keys) via `/opt/secrets` or stack `.env`, not git.
Scrape **`${JELLYFIN_EXPORTER_PORT:-9594}`** (metrics on **`/metrics`** for rebelcore).

Optional host overrides (see `env/hosts/*.env`): **`JELLYFIN_CONFIG_PATH`**, **`JELLYFIN_MEILISEARCH_DATA`**
when config and Meilisearch data live outside `${ROOT_DIR}/jellyfin/`.

## Jellyfin (alternate images)

Other exporters (e.g. `ghcr.io/stefanabl/jellyfin-prometheus-exporter`) can replace the default
service in a **`docker-compose.override.yml`** if you prefer different metrics or ports.

## Emby (in-repo)

`embyserver/docker-compose.yml` defines **`emby-exporter`**, scraping Emby at
`http://emby.arr:8096` on network **`arr`**. Add an Emby API key to the host environment as
**`EMBY_EXPORTER_API`** (e.g. `/opt/secrets/emby.env` or `embyserver` stack `.env`, not git).
Prometheus scrapes **`${EMBY_EXPORTER_PORT:-9162}`** (metrics path per upstream image docs).

## qBittorrent stack

The `prometheus-qbittorrent-exporter` service in `qbittorrent/docker-compose.yml` exposes
metrics on **`/metrics`**; the healthcheck uses that path (not `/`).
