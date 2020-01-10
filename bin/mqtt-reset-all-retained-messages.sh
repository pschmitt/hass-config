#!/usr/bin/env bash

sudo docker-compose -f /srv/hass/docker-compose.yml stop mqtt

sudo mv /srv/hass/data/mqtt/mosquitto.db /srv/hass/data/mqtt/mosquitto.db.bak

sudo docker-compose -f /srv/hass/docker-compose.yml start mqtt
