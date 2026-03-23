# Pothos: compose stacks not in this repo

These run from host paths under `/opt/<name>/` (or similar) and are **not** tracked in the
[cupric/docker-compose](https://github.com/cupric/docker-compose) repository. Keep their
`docker-compose.yml` and overrides on the host or in a private runbook; do not expect `dcud`
from the standard git checkout to deploy them.

| Stack | Role |
|-------|------|
| **aurcache** | Local AUR / package cache (host tooling) |
| **musicbrainz** | MusicBrainz mirror or related DB stack — import upstream/vendor compose into `/opt/musicbrainz` (or keep a private fork); not fleet-standard in this repo |
| **intel-gpu-exporter** | Node metrics for Intel GPU (Prometheus textfile or exporter) |

When promoting a host-only stack to fleet standard, add a directory under this repo with the
same layout as other stacks (`docker-compose.yml`, optional `.env.example`), wire
`${MEDIA_PATH}` / `${ROOT_DIR}` from [tp-environment](https://gitlab.timepiggy.com/cupric/tp-environment),
and document any secrets in override + `/opt/secrets`.
