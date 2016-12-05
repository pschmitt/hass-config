#!/usr/bin/env bash

docker exec -it hass python -m homeassistant -c /config --script check_config
