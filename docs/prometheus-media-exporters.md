# Optional Prometheus sidecars (Emby / Jellyfin)

Git-standard `embyserver` and `jellyfin` compose files intentionally include **only** the main
app (plus Jellyfin’s jellysearch/meilisearch). Prometheus scrape targets for Emby/Jellyfin
belong in **`docker-compose.override.yml`** so API tokens stay out of git.

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

## Emby (example)

Emby has several community exporters (Go or Python); none are standardized in this repo.
Typical pattern: small sidecar on `arr`, `EMBY_SERVER` + API key from `/opt/secrets/emby.env`,
scrape `:metrics` from Prometheus.

## qBittorrent stack

The `prometheus-qbittorrent-exporter` service in `qbittorrent/docker-compose.yml` exposes
metrics on **`/metrics`**; the healthcheck uses that path (not `/`).
