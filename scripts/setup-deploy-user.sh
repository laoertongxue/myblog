#!/usr/bin/env bash
# Run once as administrator: bash setup-deploy-user.sh /path/to/deploy-key.pub
# Does not grant sudo or change Caddy/SSH configuration or administrator keys.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo 'Administrator required' >&2; exit 1; }
KEY_FILE=${1:?public key file required}
ssh-keygen -lf "$KEY_FILE" >/dev/null
USER_NAME=deploy12lab
SITE=/var/www/12lab.cn
[ -L "$SITE/current" ] || { echo 'Existing current symlink required' >&2; exit 1; }
if ! id "$USER_NAME" >/dev/null 2>&1; then
    useradd --system --create-home --user-group --shell /bin/bash "$USER_NAME"
fi
install -d -m 700 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.ssh"
KEYS="/home/$USER_NAME/.ssh/authorized_keys"
if [ -f "$KEYS" ]; then cp -p "$KEYS" "$KEYS.backup.$(date +%Y%m%d-%H%M%S)"; fi
printf 'restrict %s\n' "$(cat "$KEY_FILE")" > "$KEYS"
chown "$USER_NAME:$USER_NAME" "$KEYS"
chmod 600 "$KEYS"
# Deployment needs to rotate old releases, but has no write access outside this site and its own home.
chown -R "$USER_NAME:$USER_NAME" "$SITE"
chmod 755 "$SITE" "$SITE/releases"
id "$USER_NAME"
echo 'Dedicated deployment account configured; administrator access unchanged.'
