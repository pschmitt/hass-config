from pprint import pformat
import appdaemon.plugins.hass.hassapi as hass


class MotionLights(hass.Hass):

    def initialize(self):
        self.handles = {}
        self.timers = {}
        config = self.args.get('config')
        self.log('Config: {}'.format(pformat(config)), level='DEBUG')
        for entry in config:
            name = entry.get('name')
            lights = entry.get('lights')
            sensors = entry.get('sensors')
            duration = entry.get('duration')
            sensor_enable = entry.get('constraints', {}).get('state')
            sensor_enable_state = None
            self.log('{}: Use {} to control {} -> {} secs'.format(
                name,
                sensors,
                lights,
                duration
            ), level='INFO')
            if sensor_enable:
                sensor_enable_state = self.get_state(sensor_enable)
                self.log('Listen for state changes on {}'.format(sensor_enable))
                self.listen_state(self.toggle_motion_sensor, sensor_enable,
                                  config=entry)
            if sensor_enable_state == 'on':
                self.enable_motion_sensor(sensor_enable, entry)
                # for sensor in sensors:
                #     self.log('Listen for changes on {}'.format(sensor))
                #     self.listen_state(self.motion, sensor, config=entry)

    def enable_motion_sensor(self, entity, config):
        self.log('Enable motion sensor: {} - {}'.format(entity, config))
        name = config.get('name')
        sensors = config.get('sensors')
        handlers = []
        for sensor in sensors:
            self.log('Listen for changes on {}'.format(sensor))
            handlers.append(self.listen_state(self.motion, sensor,
                                              config=config))
        self.handles[name] = handlers
        self.log('Current handlers: {}'.format(self.handles))

    def disable_motion_sensor(self, entity, config):
        self.log('Disable motion sensor: {} - {}'.format(entity, config))
        name = config.get('name')
        for handle in self.handles.get(name):
            self.cancel_listen_state(handle)
        self.handles.pop(name)
        self.log('Current handlers: {}'.format(self.handles))

    def toggle_motion_sensor(self, entity, attribute, old, new, kwargs):
        self.log('Toggle motion sensor {} - attr({}): '
                 '{} -> {} - kwargs={}'.format(
                     entity, attribute, old, new, kwargs))
        if new == 'on':
            self.enable_motion_sensor(entity, kwargs.get('config'))
        elif new == 'off':
            self.disable_motion_sensor(entity, kwargs.get('config'))

    def motion(self, entity, attribute, old, new, kwargs):
        self.log('State change detected on {} - attr({}): '
                 '{} -> {} - kwargs={}'.format(
                     entity, attribute, old, new, kwargs))
        config = kwargs.get('config')
        name = config.get('name')
        lights = config.get('lights')
        duration = config.get('duration')
        if new == 'on':
            self.log('Apply {}: turn on {} for {}s'.format(
                name, lights, duration))
            for light in lights:
                self.call_service('light/turn_on', entity_id=light)
            if name in self.timers:
                self.log('Timer already running for {}. Cancelling.'.format(name))
                self.cancel_timer(self.timers[name])
            # Schedule turning off
            self.timers[name] = self.run_in(self.lights_off, duration,
                                             config=config)
            self.log('Current timers: {}'.format(self.timers))

    def lights_off(self, kwargs):
        config = kwargs.get('config')
        name = config.get('name')
        sensors = config.get('sensors')
        lights = config.get('lights')
        duration = config.get('duration')
        for sensor in sensors:
            if self.get_state(sensor) == "on":
                self.log('{}: Motion is still detected. Leave the lights '
                         'on.'.format(name))
                # Reschedule
                self.timers[name] = self.run_in(self.lights_off, duration,
                                                config=config)
                return
        for light in lights:
            self.log('Time! Turn off {}'.format(light))
            self.call_service('light/turn_off', entity_id=light)
        self.timers.pop(name)



class OldSchoolMotionLight(hass.Hass):
    def initialize(self):

        self.handle = None

        if "sensor" in self.args:
            self.sensors = self.args["sensors"]
            for sensor in self.sensors:
                self.listen_state(self.motion, sensor)
        else:
            self.log("No sensor specified, doing nothing")

    def motion(self, entity, attribute, old, new, kwargs):
        if "delay" in self.args:
            delay = self.args["delay"]
        else:
            delay = 60

        if new == "on":
            if self.handle is None:
                if "entity_on" in self.args:
                    on_entities = self.args["entity_on"].split(",")
                    for on_entity in on_entities:
                        self.turn_on(on_entity)
                    self.log("First motion detected: i turned {} on and did "
                             "set timer".format(self.args["entity_on"]))
                else:
                    self.log("First motion detected: i turned nothing "
                             "on, but did set timer")
                self.handle = self.run_in(self.light_off, delay)
        else:
            self.cancel_timer(self.handle)
            self.handle = self.run_in(self.light_off, delay)
            self.log("Motion detected again, i have reset the timer")

    def light_off(self, kwargs):
        motion_still_detected = False
        for sensor in self.sensors:
            if self.get_state(sensor) == "on":
                motion_still_detected = True
        if not motion_still_detected:
            self.handle = None
            if "entity_off" in self.args:
                off_entities = self.args["entity_off"].split(",")
                for off_entity in off_entities:
                    # If it's a scene we need to turn it on not off
                    device, entity = self.split_entity(off_entity)
                    if device == "scene":
                        self.log("I activated {}".format(off_entity))
                        self.turn_on(off_entity)
                    else:
                        self.log("I turned {} off".format(off_entity))
                        self.turn_off(off_entity)
        else:
            self.log("Timer has Ended, but a motion detector is still on. "
                     "This shouldnt happen, probably is the delay to short.")
