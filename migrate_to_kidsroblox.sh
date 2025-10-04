#!/usr/bin/env bash
set -euo pipefail

echo "[migrate] Starting migration to KidsRoblox group..."

SQLITE=(sqlite3 -cmd "PRAGMA busy_timeout=5000;")
DB="/etc/pihole/gravity.db"

# Ensure KidsRoblox group exists and get IDs for groups
GID_RBLX="$("${SQLITE[@]}" "$DB" "SELECT id FROM 'group' WHERE name='KidsRoblox';" || true)"
if [[ -z "${GID_RBLX}" ]]; then
  echo "[migrate] Creating KidsRoblox group..."
  "${SQLITE[@]}" "$DB" "INSERT OR IGNORE INTO 'group'(name,enabled) VALUES('KidsRoblox',0);"
  GID_RBLX="$("${SQLITE[@]}" "$DB" "SELECT id FROM 'group' WHERE name='KidsRoblox';")"
fi
GID_YT="$("${SQLITE[@]}" "$DB" "SELECT id FROM 'group' WHERE name='KidsRestricted';")"
if [[ -z "${GID_YT}" ]]; then
  echo "[migrate] ERROR: KidsRestricted group not found. Aborting." >&2
  exit 1
fi

echo "[migrate] KidsRoblox id=${GID_RBLX}, KidsRestricted id=${GID_YT}"

# Collect domainlist ids for Roblox/Playhop rules (type 1 exact or type 3 regex)
IDS=( $("${SQLITE[@]}" "$DB" "SELECT id FROM domainlist WHERE (domain LIKE '%roblox%' OR domain LIKE '%rbx%' OR domain LIKE '%playhop%');") )
COUNT=${#IDS[@]}
echo "[migrate] Found ${COUNT} domainlist entries matching Roblox/Playhop"

if (( COUNT > 0 )); then
  for ID in "${IDS[@]}"; do
    # Reassign mapping exclusively to KidsRoblox
    "${SQLITE[@]}" "$DB" "DELETE FROM domainlist_by_group WHERE domainlist_id=$ID; INSERT OR IGNORE INTO domainlist_by_group(domainlist_id,group_id) VALUES($ID,$GID_RBLX);"
  done
else
  echo "[migrate] No matching domainlist entries found; skipping reassignment"
fi

# Ensure clients assigned to KidsRestricted are also assigned to KidsRoblox
echo "[migrate] Mirroring client assignments from KidsRestricted -> KidsRoblox"
CLIENT_IDS=( $("${SQLITE[@]}" "$DB" "SELECT client_id FROM client_by_group WHERE group_id=$GID_YT;") )
for CID in "${CLIENT_IDS[@]:-}"; do
  "${SQLITE[@]}" "$DB" "INSERT OR IGNORE INTO client_by_group(client_id,group_id) VALUES($CID,$GID_RBLX);"
done

echo "[migrate] Reloading pihole-FTL"
systemctl reload pihole-FTL 2>/dev/null || systemctl restart pihole-FTL 2>/dev/null || true

echo "[migrate] Done. Roblox/Playhop rules now scoped to KidsRoblox; clients mirrored."


