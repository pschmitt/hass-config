#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

hass_restart() {
    docker-compose -f ../docker-compose.yml restart hass
}

HASS_SERVICE=home-assistant

case "$1" in
    -f|--force|force) FORCE=1 ;;
esac

if ! systemctl is-active "$HASS_SERVICE" > /dev/null
then
    echo -n "HASS is not running. Starting it... "
    sudo systemctl daemon-reload
    sudo systemctl start "$HASS_SERVICE"
    echo 'Done!'
elif [[ -n "$FORCE" ]]
then
    hass_restart
elif ./check-config.sh > /dev/null
then
    echo "Config checks out ✓"
    hass_restart
else
    echo "Config is invalid. Please fix it." >&2
    exit 2
fi
