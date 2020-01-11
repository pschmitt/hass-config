#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")" || exit 9

while true
do
  docker-compose logs -f --tail=10 hass
  sleep 2
done
