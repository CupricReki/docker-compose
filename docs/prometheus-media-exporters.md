# Optional Prometheus sidecars (Emby / Jellyfin)

The **`embyserver`** stack includes **`emby-exporter`** (`williamclot/emby_exporter`). Set
**`EMBY_EXPORTER_API`** via `/opt/secrets` (sourced by `dc`) or `docker-compose.override.yml`
`env_file` — do not commit the token.

The **`jellyfin`** stack includes the main app plus jellysearch/meilisearch; a Jellyfin
Prometheus sidecar can stay in **`docker-compose.override.yml`** so API tokens stay out of git.

## Jellyfin (example)

Pick an exporter image you trust (e.g. `ghcr.io/stefanabl/jellyfin-prometheus-exporter` or
`rebelcore/jellyfin-exporter`). Add a service on the same Docker network as Jellyfin (`arr`).

```yaml
services:
  jellyfin-exporter:
    image: ghcr.io/stefanabl/jellyfin-prometheus-exporter:${JELLYFIN_EXPORTER_TAG:-latest}
    container_name: jellyfin-exporter
    environment:
      - JF_URL=http://jellyfin:8096/
      - TOKEN=${JELLYFIN_EXPORTER_TOKEN}
    ports:
      - ${JELLYFIN_EXPORTER_PORT:-9594}:8080
    networks:
      - arr
    restart: unless-stopped
```

Put `JELLYFIN_EXPORTER_TOKEN` in `/opt/secrets/jellyfin.env` (create a Jellyfin API key in the
admin UI). Reference that file from the override with `env_file`.

Healthcheck: use `curl -f http://localhost:<exporter-port>/metrics` (or the image’s documented
path).

## Emby (in-repo)

`embyserver/docker-compose.yml` defines **`emby-exporter`**, scraping Emby at
`http://emby.arr:8096` on network **`arr`**. Add an Emby API key to the host environment as
**`EMBY_EXPORTER_API`** (e.g. `/opt/secrets/emby.env` or `embyserver` stack `.env`, not git).
Prometheus scrapes **`${EMBY_EXPORTER_PORT:-9162}`** (metrics path per upstream image docs).

## qBittorrent stack

The `prometheus-qbittorrent-exporter` service in `qbittorrent/docker-compose.yml` exposes
metrics on **`/metrics`**; the healthcheck uses that path (not `/`).
