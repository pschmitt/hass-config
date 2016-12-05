#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

HASS_SERVICE=home-assistant

ha_restart() {
    echo -n "Restarting Home Assistant... "
    sudo systemctl daemon-reload
    sudo systemctl restart "$HASS_SERVICE"
    echo 'Done !'
}

if ! systemctl is-active "$HASS_SERVICE" > /dev/null
then
    echo -n "HASS is not running. Starting it..."
    sudo systemctl start "$HASS_SERVICE"
    echo 'Done!'
elif ./check-config.sh > /dev/null
then
    echo "Config checks out ✓"
    ha_restart
else
    echo "Config is invalid. Please fix it." >&2
    exit 2
fi
