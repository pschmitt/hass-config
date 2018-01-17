#!/usr/bin/env bash

    # -H "Host: ${OCTOPI_HOST}" \

cd "$(readlink -f "$(dirname "$0")")" || exit 9

HASS_SECRETS=/config/secrets.yaml
if [[ -r ../config/hass/secrets.yaml ]]
then
    HASS_SECRETS="../config/hass/secrets.yaml"
fi

OCTOPRINT_HOST="$(awk '/octoprint_host/ { print $2; exit }' $HASS_SECRETS)"
OCTOPRINT_API_KEY=$(awk '/octoprint_api_key/ { print $2; exit }' $HASS_SECRETS)

send_gcode() {
    curl \
        -H "X-Api-Key: $OCTOPRINT_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$1" \
        "http://${OCTOPRINT_HOST}/api/printer/command"
}

case "$1" in
    on)
        send_gcode '{"command": "M42 P6 S255"}'
        ;;
    off)
        send_gcode '{"command": "M42 P6 S0"}'
        ;;
esac
