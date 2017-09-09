"""
Support for interface with a Sony SRS speaker.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.sonyavr/
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.util as util
from homeassistant.components.media_player import (
    MediaPlayerDevice, PLATFORM_SCHEMA, SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF, SUPPORT_TURN_ON, SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_MUTE)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, CONF_PORT, STATE_UNKNOWN)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pysonyavr==1.4']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Sony SRS Speaker'
DEFAULT_PORT = 54480

SUPPORT_SONYAVR = SUPPORT_TURN_OFF | SUPPORT_TURN_ON | \
    SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | SUPPORT_SELECT_SOURCE | \
    SUPPORT_VOLUME_SET

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Orange Livebox Play TV platform."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    name = config.get(CONF_NAME)

    sonyavr_devices = []

    try:
        device = SonyAvrDevice(host, port, name)
        sonyavr_devices.append(device)
    except IOError:
        _LOGGER.error("Failed to connect to Sony AVR at %s:%s. "
                      "Please check your configuration", host, port)
    add_devices(sonyavr_devices, True)


class SonyAvrDevice(MediaPlayerDevice):
    """Representation of an Orange Livebox Play TV."""

    def __init__(self, host, port, name):
        """Initialize the Livebox Play TV device."""
        from pysonyavr import SonyAvr
        self._client = SonyAvr(host, port)
        # Assume that the appliance is not muted
        self._name = name
        self._state = STATE_UNKNOWN
        self._source_list = None
        self._current_source = None
        self._volume = None
        self._muted = False

    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update(self):
        """Retrieve the latest data."""
        self._volume = self._client.volume_percent
        self._current_source = self._client.current_input
        self._source_list = self._client.ext_inputs
        if self._client.is_on:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def source(self):
        """Return the current input source."""
        return self._current_source

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_list

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_SONYAVR

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    def turn_off(self):
        """Turn off media player."""
        self._state = STATE_OFF
        self._client.turn_off()

    def turn_on(self):
        """Turn on the media player."""
        self._state = STATE_ON
        self._client.turn_on()

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._client.set_volume(volume)

    def volume_up(self):
        """Volume up the media player."""
        self._client.raise_volume()

    def volume_down(self):
        """Volume down media player."""
        self._client.lower_volume()

    def mute_volume(self, mute):
        """Send mute command."""
        self._muted = mute
        self._client.mute(mute)

    def select_source(self, source):
        """Select input source."""
        self._current_source = source
        self._client.set_input(source)
