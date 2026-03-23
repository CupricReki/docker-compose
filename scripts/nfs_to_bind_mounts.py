#!/usr/bin/env python3
"""
Convert Docker Compose NFS driver volumes to bind mounts and comment out the
original volumes: blocks for reference during transition.

Run from repo root: python3 scripts/nfs_to_bind_mounts.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

HEADER = (
    "# Legacy NFS volumes (reference only). Compose uses host bind mounts above;\n"
    "# mount NFS (or other storage) on the host at these paths as needed.\n"
)

BIND_REPLACEMENTS_TP = [
    (re.compile(r"^(\s*)-\s+nas1:/media/nas1\s*$", re.M), r"\1- ${NAS1_PATH}:/media/nas1"),
    (re.compile(r"^(\s*)-\s+nas2:/media/nas2\s*$", re.M), r"\1- ${NAS2_PATH}:/media/nas2"),
    (re.compile(r"^(\s*)-\s+photos:/usr/src/app/upload\s*$", re.M), r"\1- ${PHOTOS_PATH}:/usr/src/app/upload"),
    (re.compile(r"^(\s*)-\s+books:/calibre-library\s*$", re.M), r"\1- ${BOOKS_PATH}:/calibre-library"),
    (re.compile(r"^(\s*)-\s+media:/media/frigate\s*$", re.M), r"\1- /mnt/media/surveillance:/media/frigate"),
    (re.compile(r"^(\s*)-\s+media:/media\s*$", re.M), r"\1- ${MEDIA_PATH}:/media"),
]


def is_top_level_key(line: str) -> bool:
    if not line.strip() or line.lstrip().startswith("#"):
        return False
    if line[0] in " \t":
        return False
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_.-]*:", line))


def find_volumes_section(lines: list[str]) -> tuple[int, int] | None:
    """Top-level volumes: only (not service-level volumes:)."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith("volumes:") and not line[:1].isspace():
            start = i
            break
    if start is None:
        return None
    for j in range(start + 1, len(lines)):
        if is_top_level_key(lines[j]):
            return start, j
    return start, len(lines)


def comment_block(text: str) -> str:
    lines_out = []
    for line in text.splitlines(keepends=True):
        if line.endswith("\n"):
            core, nl = line[:-1], "\n"
        else:
            core, nl = line, ""
        lines_out.append((f"# {core}" + nl) if core.strip() else "#\n")
    return "".join(lines_out)


def device_to_host_path(line: str) -> str:
    if "device:" not in line:
        return ""
    rest = line.split("device:", 1)[1].strip()
    rest = rest.strip().strip('"').strip("'")
    if rest.startswith(":"):
        rest = rest[1:]
    return rest


def parse_legacy_volume_paths(vol_section: str) -> dict[str, str]:
    """Map volume name -> host path from nfs device lines."""
    vol_map: dict[str, str] = {}
    current: str | None = None
    for line in vol_section.splitlines():
        m = re.match(r"^  ([a-zA-Z0-9_-]+):\s*$", line)
        if m:
            current = m.group(1)
            continue
        if current and "device:" in line:
            p = device_to_host_path(line)
            if p:
                vol_map[current] = p
    return vol_map


def apply_bind_replacements_tp(body: str) -> str:
    for pat, repl in BIND_REPLACEMENTS_TP:
        body = pat.sub(repl, body)
    return body


def process_immich(path: Path) -> None:
    raw = path.read_text()
    lines = raw.splitlines(keepends=True)
    span = find_volumes_section(lines)
    assert span is not None
    v0, v1 = span
    vol_yaml = "".join(lines[v0:v1])
    tail = "".join(lines[v1:])
    body = "".join(lines[:v0])

    body = re.sub(
        r"^(\s*)-\s+photos:/usr/src/app/upload\s*$",
        r"\1- ${PHOTOS_PATH}:/usr/src/app/upload",
        body,
        flags=re.MULTILINE,
    )

    new_vol = "volumes:\n  model-cache:\n\n" + HEADER + comment_block(vol_yaml)
    path.write_text(body + new_vol + tail)


def process_tp_env_file(path: Path) -> bool:
    raw = path.read_text()
    if "nfs4" not in raw:
        return False
    if path.parent.name == "immich":
        process_immich(path)
        return True

    lines = raw.splitlines(keepends=True)
    span = find_volumes_section(lines)
    if span is None:
        return False
    v0, v1 = span
    volumes_yaml = "".join(lines[v0:v1])
    body = apply_bind_replacements_tp("".join(lines[:v0]))
    tail = "".join(lines[v1:])
    new_volumes = HEADER + comment_block(volumes_yaml)
    path.write_text(body + new_volumes + tail)
    return True


def process_legacy_hardcoded(path: Path) -> bool:
    raw = path.read_text()
    if "nfs4" not in raw:
        return False
    lines = raw.splitlines(keepends=True)
    span = find_volumes_section(lines)
    if span is None:
        return False
    v0, v1 = span
    vol_section = "".join(lines[v0:v1])
    vol_map = parse_legacy_volume_paths(vol_section)
    if not vol_map:
        return False

    body = "".join(lines[:v0])
    tail = "".join(lines[v1:])

    for vname, bpath in sorted(vol_map.items(), key=lambda x: -len(x[0])):
        pat = re.compile(rf"^(\s*)-\s+{re.escape(vname)}:([^\s]+)\s*$", re.M)

        def make_sub(bp: str):
            def sub(m: re.Match) -> str:
                indent, dest = m.group(1), m.group(2)
                return f"{indent}- {bp}:{dest}"

            return sub

        body = pat.sub(make_sub(bpath), body)

    new_volumes = HEADER + comment_block("".join(lines[v0:v1]))
    path.write_text(body + new_volumes + tail)
    return True


def uses_tp_nfs_vars(raw: str) -> bool:
    return bool(re.search(r"addr=\$\{NFS_", raw) or "${NFS_MEDIA_ADDR}" in raw)


def has_active_nfs4(raw: str) -> bool:
    """True if compose still has a non-commented nfs4 volume driver (not reference-only)."""
    for line in raw.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"type:\s*.*nfs4", line):
            return True
    return False


def main() -> int:
    changed: list[str] = []
    for yml in sorted(REPO.glob("*/docker-compose.yml")):
        raw = yml.read_text()
        if not has_active_nfs4(raw):
            continue
        if uses_tp_nfs_vars(raw):
            if process_tp_env_file(yml):
                changed.append(yml.parent.name)
        else:
            if process_legacy_hardcoded(yml):
                changed.append(yml.parent.name)

    print("Updated:", len(changed), "stacks")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
