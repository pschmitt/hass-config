#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

HASS_SERVICE=home-assistant

if ! systemctl is-active "$HASS_SERVICE" > /dev/null
then
    echo -n "HASS is not running. Starting it... "
    sudo systemctl daemon-reload
    sudo systemctl start "$HASS_SERVICE"
    echo 'Done!'
elif ./check-config.sh > /dev/null
then
    echo "Config checks out ✓"
    docker-compose -f ../docker-compose.yml restart hass
else
    echo "Config is invalid. Please fix it." >&2
    exit 2
fi
