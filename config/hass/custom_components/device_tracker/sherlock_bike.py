"""
Support for Sherlock.bike GPS trackers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.sherlock_bike/
"""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.device_tracker import (
    ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SOURCE_TYPE_GPS)
from homeassistant.const import (ATTR_BATTERY_LEVEL, ATTR_FRIENDLY_NAME,
                                 ATTR_NAME, CONF_PASSWORD, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import slugify, dt as dt_util

REQUIREMENTS = ["sherlockbikepy==0.2.1"]

_LOGGER = logging.getLogger(__name__)

ATTR_EMAIL = "email"
ATTR_FIRMWARE_VERSION = "firmware_version"
ATTR_FULL_NAME = "full_name"
ATTR_IMEI = "imei"
ATTR_LAST_SEEN = "last_seen"
ATTR_BIKE_FRAME_NUMBER = "bike_frame_number"
ATTR_BIKE_SERIAL_NUMBER = "bike_serial_number"
ATTR_STATE = "state"
ATTR_USER_ID = "user_id"

EVENT_SHERLOCK_ALARM = "sherlock_alarm"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
})

STATE_ALARM = 'ALARMED'


def setup_scanner(hass, config: ConfigType, see, discovery_info=None):
    """Set up the Google Maps Location sharing scanner."""
    scanner = SherlockBikeScanner(hass, config, see)
    return scanner.success_init


class SherlockBikeScanner:
    """Representation of a Sherlock.bike account."""

    def __init__(self, hass, config: ConfigType, see) -> None:
        """Initialize the scanner."""
        from sherlockbikepy import Sherlock, LoginFailedException

        self.hass = hass
        self.see = see
        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]

        try:
            self.service = Sherlock(self.username, self.password)
            self._update_info()

            track_time_interval(
                hass, self._update_info, MIN_TIME_BETWEEN_SCANS)

            self.success_init = True

        except LoginFailedException:
            _LOGGER.error("You have specified invalid login credentials")
            self.success_init = False

    def _update_info(self, now=None):
        for dev in self.service.devices:
            dev_id = "sherlock_{0}".format(dev.sherlock_id)
            entity_id = ENTITY_ID_FORMAT.format(dev_id)

            # Get previous values.
            entity = self.hass.states.get(entity_id)
            prev_lat = entity.attributes.get("latitude") if entity else None
            prev_lon = entity.attributes.get("longitude") if entity else None
            prev_last_seen = (entity.attributes.get("last_seen") if entity
                              else None)
            prev_state = entity.attributes.get("state") if entity else None

            # Default to prev lat/lon/last_seen values if they are not
            # currently determined.
            fullname = "{0} {1}".format(self.service.user.get("name"),
                                        self.service.user.get("surname"))
            lat = dev.location.latitude if dev.location else prev_lat
            lon = dev.location.longitude if dev.location else prev_lon
            last_seen = (dev.location.last_update if dev.location
                         else prev_last_seen)

            attrs = {
                ATTR_BATTERY_LEVEL: dev.battery_level,
                ATTR_BIKE_FRAME_NUMBER: dev.bike_frame_number,
                ATTR_BIKE_SERIAL_NUMBER: dev.bike_serial_number,
                ATTR_EMAIL: self.service.user.get("email"),
                ATTR_FIRMWARE_VERSION: dev.firmware_version,
                ATTR_FRIENDLY_NAME: dev.bike_model,
                ATTR_FULL_NAME: fullname,
                ATTR_IMEI: dev.imei,
                ATTR_LAST_SEEN: last_seen,
                ATTR_NAME: dev.bike_model,
                ATTR_STATE: dev.state,
                ATTR_USER_ID: self.service.user.get("user_id"),
            }
            self.see(
                dev_id=dev_id,
                gps=(lat, lon),
                picture=dev.bike_picture_url,
                source_type=SOURCE_TYPE_GPS,
                # gps_accuracy=dev.accuracy,
                attributes=attrs
            )
            # Fire an event in case the state updated to ALARMED.
            if dev.state == STATE_ALARM and prev_state != STATE_ALARM:
                _LOGGER.info("Sherlock alarm fired")
                event_data = {
                    'latitude': lat,
                    'longitude': lon,
                    'sherlock_id': dev.sherlock_id,
                    'entity_id': entity_id
                }
                self.hass.bus.fire(EVENT_SHERLOCK_ALARM, event_data)
