#!/usr/bin/env bash

docker exec -it hass-db su postgres -c "psql hass"
