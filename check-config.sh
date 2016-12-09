#!/usr/bin/env bash

[[ -z $(docker exec -it hass \
    python -m homeassistant -c /config --script check_config | \
    grep -v "Testing configuration at" | tee /dev/stderr) ]]
