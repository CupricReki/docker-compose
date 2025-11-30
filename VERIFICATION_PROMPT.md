# Docker Compose Deployment Verification Prompt

Use this prompt to have an AI verify the deployment status of all Docker Compose files.

---

## Prompt

```
Verify the Docker Compose deployment in this system by checking:

1. **Git Repository Status** (`/etc/docker-compose/`)
   - List all service directories containing docker-compose.yml
   - Check git status for uncommitted changes
   - Verify remote is up to date

2. **Symlink Verification** (`/opt/`)
   - For each service in the git repo, check if /opt/<service>/docker-compose.yml exists
   - Verify it's a symlink pointing to /etc/docker-compose/<service>/docker-compose.yml
   - Flag any broken symlinks or regular files that should be symlinks

3. **Environment Files**
   - Check each /opt/<service>/.env exists and has required variables
   - Verify NFS_SERVER, NFS_OPTS, TZ, ROOT_DIR are defined where needed
   - Check /opt/secrets/*.env files exist with proper permissions (640, root:docker)

4. **Running Containers**
   - List all running containers
   - Cross-reference with deployed compose files
   - Identify services that are deployed but not running
   - Identify running containers not managed by our compose files

5. **Health Status**
   - Check health status of all containers with healthchecks
   - Flag any unhealthy or restarting containers
   - Show recent logs for problematic containers

6. **Resource Limits**
   - Verify all compose files have mem_limit, mem_reservation, and cpus defined
   - Flag any services missing resource limits

7. **Best Practices Compliance**
   - Check for logging configuration
   - Verify healthchecks are defined
   - Check for diun.enable label
   - Verify restart policy is set

Generate a report with:
- ✅ Passing checks
- ⚠️ Warnings (non-critical issues)
- ❌ Failures (critical issues requiring attention)

Commands to use:
- `ls /etc/docker-compose/*/docker-compose.yml` - List repo compose files
- `ls -la /opt/*/docker-compose.yml` - Check symlinks
- `docker ps --format "{{.Names}}: {{.Status}}"` - Container status
- `docker compose -f /opt/<service>/docker-compose.yml config` - Validate config
- `grep -l "cpus:" /etc/docker-compose/*/docker-compose.yml` - Check CPU limits
```

---

## Quick Verification Script

Run this to get a quick status overview:

```bash
#!/bin/bash
echo "=== Docker Compose Deployment Verification ==="
echo ""

echo "1. Git Repository Status"
cd /etc/docker-compose
git status --short
echo ""

echo "2. Symlink Status"
for dir in /etc/docker-compose/*/; do
  svc=$(basename "$dir")
  if [ -f "$dir/docker-compose.yml" ]; then
    target="/opt/$svc/docker-compose.yml"
    if [ -L "$target" ]; then
      echo "✅ $svc: symlinked"
    elif [ -f "$target" ]; then
      echo "⚠️  $svc: regular file (should be symlink)"
    else
      echo "❌ $svc: missing in /opt"
    fi
  fi
done
echo ""

echo "3. Running Containers Health"
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "(healthy|unhealthy|starting)" | head -20
echo ""

echo "4. Resource Limits Check"
missing=""
for f in /etc/docker-compose/*/docker-compose.yml; do
  svc=$(dirname "$f" | xargs basename)
  if ! grep -q "cpus:" "$f" 2>/dev/null; then
    missing="$missing $svc"
  fi
done
if [ -z "$missing" ]; then
  echo "✅ All compose files have CPU limits"
else
  echo "❌ Missing CPU limits:$missing"
fi
echo ""

echo "5. Secrets Permissions"
ls -la /opt/secrets/*.env 2>/dev/null | awk '{print $1, $3, $4, $9}'
echo ""

echo "=== Verification Complete ==="
```

---

## Expected Services (Currently Deployed)

These services should have symlinks from /opt to /etc/docker-compose:

| Service | Status | Notes |
|---------|--------|-------|
| sonarr | ✅ | Arr app |
| sonarr-4k | ✅ | Arr app |
| sonarr-anime | ✅ | Arr app |
| radarr | ✅ | Arr app |
| radarr-4k | ✅ | Arr app |
| prowlarr | ✅ | Arr app |
| bazarr | ✅ | Arr app |
| bazarr-4k | ✅ | Arr app |
| bazarr-anime | ✅ | Arr app |
| readarr | ✅ | Arr app |
| readarr-audio | ✅ | Arr app |
| whisparr | ✅ | Arr app |
| whisparr-v3 | ✅ | Arr app |
| lidarr-stack | ✅ | Lidarr + slskd |
| sabnzbd | ✅ | Downloader |
| qbittorrent | ✅ | VPN + torrent stack |
| qbit_manage | ✅ | qBittorrent manager |
| embyserver | ✅ | Media server |
| jellyfin | ✅ | Media server |
| stash | ✅ | Media server |
| audiobookshelf | ✅ | Audiobooks |
| bookshelf | ✅ | Ebooks |
| immich | ✅ | Photos |
| diun | ✅ | Image updates |
| dozzle-agent | ✅ | Log viewer |
| fileflows | ✅ | Media processing |
| vector | ✅ | Log collector |

## Not Migrated (Intentionally)

| Service | Reason |
|---------|--------|
| aurcache | Uses local build |
| musicbrainz | Complex multi-service with builds |
| immich (partial) | Has DNS fixes in .env |

