#!/usr/bin/env bash

set -e

usage() {
  echo "Usage: $(basename "$0") USERNAME PASSWORD"
}

if [[ $# -lt 2 ]]
then
  usage
  exit 0
fi

USERNAME="$1"
PASSWORD="$2"

docker run -it --rm \
  -v /srv/hass/config/mqtt:/config \
  --entrypoint mosquitto_passwd \
  eclipse-mosquitto:latest \
  -b /config/passwd "$USERNAME" "$PASSWORD"

sudo docker-compose -f /srv/hass/docker-compose.yml restart mqtt
