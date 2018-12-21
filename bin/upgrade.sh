#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

docker-compose pull

docker-compose stop hass
docker-compose rm -f hass
docker-compose up -d hass
