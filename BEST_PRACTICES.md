# Docker Compose Best Practices Guide

This guide documents the standards and best practices for creating Docker Compose files in this repository.

## Directory Structure

```
/etc/docker-compose/           # Git-managed compose files
  └── <service>/
      └── docker-compose.yml   # Main compose file (symlinked from /opt/<service>/)

/opt/<service>/                # Service runtime directory
  ├── docker-compose.yml       # Symlink to /etc/docker-compose/<service>/docker-compose.yml
  ├── docker-compose.override.yml  # Local machine-specific overrides (not in git)
  ├── .env                     # Local environment variables (not in git)
  └── config/                  # Application config/data
```

## Environment Variables

### Global Variables (`/etc/environment`)

These are available system-wide but NOT automatically loaded by Docker Compose:
```bash
PUID=1000                    # Default user ID
PGID=1000                    # Default group ID
PUID_MEDIA=3001              # Media applications user ID
PGID_MEDIA=3001              # Media applications group ID
TZ=America/New_York          # Timezone
DOMAIN=example.com           # Domain for service URLs
ROOT_DIR=/opt                # Base directory for configs
SCRIPTS_ROOT=/opt/scripts    # Scripts directory
LOCAL_CACHE=/media           # Local media cache path
NFS_OPTS=soft,timeo=50,retrans=3,rsize=1048576,wsize=1048576,noatime,nolock
```

### Local `.env` Files

Each service should have a `.env` file with:
```bash
# Service-specific settings
NFS_SERVER=10.1.0.4
NFS_MEDIA_PATH=/mnt/vol2/media

# Replicate global vars needed at compose-time
TZ=America/New_York
ROOT_DIR=/opt
NFS_OPTS=soft,timeo=50,retrans=3,rsize=1048576,wsize=1048576,noatime,nolock
DOMAIN=example.com

# Service-specific
SERVICE_PORT=8080
SERVICE_TAG=latest
```

### Secrets

Store sensitive data in `/opt/secrets/` with restricted permissions:
```bash
# /opt/secrets/service.env (chmod 640, chown root:docker)
API_KEY=secret_value
DB_PASSWORD=secret_value
```

Reference in `docker-compose.override.yml`:
```yaml
services:
  myservice:
    env_file:
      - /opt/secrets/service.env
```

## Compose File Template

```yaml
---
services:
  myservice:
    image: organization/image:${SERVICE_TAG:-latest}
    container_name: myservice
    hostname: myservice
    environment:
      - TZ=${TZ}
      - PUID=${PUID_MEDIA}
      - PGID=${PGID_MEDIA}
    volumes:
      - ${ROOT_DIR}/myservice/config:/config
      - media:/media
    ports:
      - ${SERVICE_PORT:-8080}:8080
    # Resource Limits (REQUIRED)
    mem_limit: 2g
    mem_reservation: 256m
    cpus: 2.0
    restart: unless-stopped
    # Logging (REQUIRED)
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    # Healthcheck (REQUIRED)
    healthcheck:
      test: curl --fail http://localhost:8080/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    # Labels
    labels:
      - diun.enable=true
    # Networks (if needed)
    networks:
      - arr

volumes:
  media:
    driver: local
    driver_opts:
      type: "nfs4"
      o: "addr=${NFS_SERVER},${NFS_OPTS}"
      device: ":${NFS_MEDIA_PATH}"

networks:
  arr:
    external: true
```

## Resource Limits Guidelines

### Memory Limits

| Service Type | mem_limit | mem_reservation |
|-------------|-----------|-----------------|
| Lightweight (diun, dozzle) | 256m | 64m |
| Standard (arr apps) | 2g | 256m |
| Media servers (emby, jellyfin) | 8g | 2g |
| ML/Processing (immich ML) | 8g | 1g |
| Databases | 2g | 256m |

### CPU Limits

| Service Type | cpus |
|-------------|------|
| Lightweight | 0.5 |
| Standard | 1.0-2.0 |
| Media processing/transcoding | 4.0-8.0 |
| ML inference | 8.0 |
| Multi-service stacks | 2.0 per service |

**Note:** `cpus` limits CPU time, not visible cores. Containers still see all host CPUs but are throttled.

## NFS Mount Options

Always use these options for NFS volumes:
```
soft,timeo=50,retrans=3,rsize=1048576,wsize=1048576,noatime,nolock
```

- `soft` - Return errors instead of hanging on timeout
- `timeo=50` - 5 second timeout (in deciseconds)
- `retrans=3` - 3 retries before failing
- `rsize/wsize=1048576` - 1MB read/write buffer
- `noatime` - Don't update access times (performance)
- `nolock` - Disable NFS locking (use for media files)

## DNS Considerations

If your network has a DNS search domain (e.g., `timepiggy.com`), Docker service names may conflict with external DNS records.

**Problem:** `redis` resolves to `redis.timepiggy.com` instead of the container.

**Solution:** Use Docker network-qualified names in `.env`:
```bash
REDIS_HOSTNAME=redis.servicename_default
DB_HOSTNAME=database.servicename_default
```

## Healthchecks

### HTTP Services
```yaml
healthcheck:
  test: curl --fail http://localhost:8080/health || exit 1
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Services Without curl
```yaml
healthcheck:
  test: wget --spider -q http://localhost:8080/ || exit 1
  interval: 30s
  timeout: 10s
  retries: 3
```

### Redis
```yaml
healthcheck:
  test: redis-cli ping || exit 1
  interval: 30s
  timeout: 10s
  retries: 3
```

### PostgreSQL
```yaml
healthcheck:
  test: pg_isready --dbname='mydb' --username='myuser' || exit 1
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## Override Files

Use `docker-compose.override.yml` for:
- Homepage labels
- Machine-specific settings
- Secret file references
- Hardware acceleration devices

Example:
```yaml
---
services:
  myservice:
    env_file:
      - /opt/secrets/myservice.env
    devices:
      - /dev/dri:/dev/dri  # GPU passthrough
    labels:
      - homepage.group=Media
      - homepage.name=MyService
      - homepage.href=https://myservice.${DOMAIN}
```

## GPU Passthrough

For hardware acceleration:
```yaml
services:
  myservice:
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - "989"   # render group GID
      - "986"   # video group GID
```

## Shared Networks

For inter-container communication (e.g., arr apps):
```yaml
networks:
  arr:
    external: true
```

Create the network once:
```bash
docker network create arr
```

## File Permissions

| Path | Owner | Mode |
|------|-------|------|
| /opt/<service>/ | media:media | 775 |
| /opt/<service>/.env | media:media | 664 |
| /opt/secrets/*.env | root:docker | 640 |
| /etc/docker-compose/ | root:root | 755 |

## Deployment Checklist

1. ☐ Create backup of existing config
2. ☐ Create compose file in `/etc/docker-compose/<service>/`
3. ☐ Create `.env` with all required variables
4. ☐ Create `docker-compose.override.yml` for local settings
5. ☐ Create symlink from `/opt/<service>/docker-compose.yml`
6. ☐ Add secrets to `/opt/secrets/` if needed
7. ☐ Set correct file permissions
8. ☐ Test with `docker compose config`
9. ☐ Deploy with `docker compose up -d`
10. ☐ Verify healthchecks pass
11. ☐ Commit to git repository

## Common Issues

### "Variable not set" warnings
These are normal for global variables from `/etc/environment`. The container will use defaults or values from `.env`.

### Volume "doesn't match configuration"
Old volumes may have different options. Remove with `docker volume rm <volume>` before recreating.

### Container keeps restarting
Check logs with `docker logs <container>`. Common causes:
- Missing environment variables
- DNS resolution issues
- Database connection failures

### DNS conflicts
If hostnames resolve to wrong IPs, use network-qualified names like `service.network_default`.
