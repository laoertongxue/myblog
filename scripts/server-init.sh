#!/bin/bash
# Idempotent setup: never copy the default Caddy page over a deployed release.
set -euo pipefail

SITE_DIR=/var/www/12lab.cn
mkdir -p "$SITE_DIR/releases"
if [ ! -e "$SITE_DIR/current" ] && [ ! -L "$SITE_DIR/current" ]; then
    mkdir -p "$SITE_DIR/current"
    cp -r /usr/share/caddy/. "$SITE_DIR/current/"
fi

CONFIG="$(dirname "$0")/Caddyfile"
caddy validate --config "$CONFIG" --adapter caddyfile
BACKUP="/etc/caddy/Caddyfile.backup.$(date +%Y%m%d-%H%M%S)"
cp -p /etc/caddy/Caddyfile "$BACKUP"
rollback() {
    echo "Caddy reload or health check failed; restoring $BACKUP" >&2
    install -m 644 "$BACKUP" /etc/caddy/Caddyfile
    systemctl reload caddy
}
trap rollback ERR
install -m 644 "$CONFIG" /etc/caddy/Caddyfile
systemctl reload caddy
systemctl is-active --quiet caddy
curl --fail --silent --show-error --max-time 20 https://12lab.cn/ -o /dev/null
trap - ERR
printf 'Caddy configuration applied. Backup: %s\n' "$BACKUP"
