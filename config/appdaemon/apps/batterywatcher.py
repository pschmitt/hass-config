import datetime
import traceback

import appdaemon.plugins.hass.hassapi as hass


class BatteryWatcher(hass.Hass):

    def initialize(self):
        self.listeners = {}
        devices = self.create_battery_devices()
        self.create_battery_groups(devices)
        entities = [(x.get('attributes', {}).get('monitored_entity'),
                     x.get('attributes', {}).get('monitored_attribute'))
                    for x in devices]
        for entity, attr in entities:
            self.subscribe_to_entity(entity, attr)
        interval = 60 * 5  # every 5 minutes
        start = datetime.datetime.now() + datetime.timedelta(seconds=interval)
        self.cronjob = self.run_every(
            self.check_for_new_devices, start, interval)

    def subscribe_to_entity(self, entity, attribute):
        self.log('Monitor {} - {}'.format(entity, attribute), level='DEBUG')
        if attribute == 'state':
            listener = self.listen_state(self.update_battery_device, entity)
        else:
            listener = self.listen_state(
                self.update_battery_device, entity, attribute=attribute)
        self.listeners[entity] = listener

    def check_for_new_devices(self, kwargs):
        self.log('Checking for new devices', level='DEBUG')
        devices = self.get_state()
        for device in [x for x in devices if x not in self.listeners.keys()]:
            bat_dev = self.process_entity(devices, device)
            if bat_dev:
                self.log('New battery device: {}'.format(bat_dev))
                attrs = bat_dev.get('attributes', {})
                entity_id = attrs.get('monitored_entity')
                attr = attrs.get('monitored_attribute')
                battery_level = self.battery_level_value(bat_dev.get('state'))
                self.subscribe_to_entity(entity_id, attr)
                self.update_battery_groups(entity_id, battery_level)

    def battery_level_value(self, battery_level):
        if battery_level is None:
            return 'unknown'
        if isinstance(battery_level, str):
            try:
                return int(battery_level)
            except ValueError:
                return int(float(battery_level))
            if battery_level.lower() == 'true':
                return True
            if battery_level.lower() == 'false':
                return False

    def set_low_battery_devices(self, members):
        return self.set_state(
            'group.low_battery_devices',
            state='on',
            attributes={
                'view': False,
                'hidden': False,
                'icon': 'mdi:battery',
                'assumed_state': False,
                'friendly_name': 'Low battery devices',
                'entity_id': members
            })

    def clear_low_battery_device(self, entity):
        low_battery_group = self.get_state('group.low_battery_devices',
                                           attribute='all')
        members = low_battery_group.get('attributes', {}).get('entity_id')
        if entity not in members:
            return
        members.remove(entity)
        return self.set_low_battery_devices(members)

    def register_battery_devices(self, devices):
        return self.set_state(
            'group.all_battery_devices',
            state='on',
            attributes={
                'view': False,
                'hidden': False,
                'icon': 'mdi:battery',
                'assumed_state': False,
                'friendly_name': 'All battery devices',
                'entity_id': devices
            })

    def register_low_battery_devices(self, devices):
        low_battery_group = self.get_state('group.low_battery_devices',
                                           attribute='all')
        if low_battery_group:
            attrs = low_battery_group.get('attributes', {})
            members = attrs.get('entity_id', [])
            if isinstance(devices, list):
                new_members = members + devices
            else:
                new_members = members + [devices]
        else:
            new_members = devices
        return self.set_low_battery_devices(new_members)

    def update_battery_device(self, entity, attribute, old, new, kwargs):
        if new == old:
            self.log('Battery level unchanged for {}: {}'.format(entity, old),
                     level='DEBUG')
            return
        self.log('Battery level of {} updated: {} -> {}%'.format(
            entity, old, new))
        attrs = self.get_state(entity, attribute='all').get('attributes', {})
        custom_battery_threshold = attrs.get('battery_threshold')
        if custom_battery_threshold:
            threshold = custom_battery_threshold
        else:
            threshold = self.args.get('threshold')
        bat_entity = self.battery_entity_name(entity)
        battery_level = self.battery_level_value(new)
        battery_level_old = self.battery_level_value(old)
        if isinstance(battery_level, bool):
            self.create_binary_battery_device(entity, battery_level)
        else:
            self.create_battery_device(entity, battery_level)
        # Update groups
        if battery_level in [None, 'unknown']:
            self.log('Unknown battery level for entity: {}'.format(entity),
                     level='WARNING')
            return
        self.update_battery_groups(entity, battery_level, battery_level_old)

    def update_battery_groups(self, entity_id, battery_level,
                              previous_battery_level=None):
        bat_entity_id = self.battery_entity_name(entity_id)
        attrs = self.get_state(bat_entity_id, attribute='all').get('attributes', {})
        custom_battery_threshold = attrs.get('battery_threshold')
        if custom_battery_threshold:
            threshold = custom_battery_threshold
        else:
            threshold = self.args.get('threshold')
        self.log('DEBUG: {} / {}'.format(battery_level, threshold))
        try:
            if isinstance(battery_level, bool):
                if battery_level:
                    self.register_low_battery_devices(bat_entity_id)
                else:
                    self.clear_low_battery_device(bat_entity_id)
            elif battery_level < threshold:
                self.register_low_battery_devices(bat_entity_id)
                if previous_battery_level and previous_battery_level >= threshold:
                    self.log('Battery of {} is getting low.'.format(bat_entity_id))
                    event = self.fire_event(
                        'battery_low',
                        battery_level=battery_level,
                        bat_entity_id=bat_entity_id)
                    self.log('Fired event: {}'.format(event))
            elif battery_level >= threshold:
                self.clear_low_battery_device(bat_entity_id)
                if previous_battery_level and previous_battery_level < threshold:
                    self.log('Battery of {} is okay again (above '
                             'threshold).'.format(bat_entity_id))
                    event = self.fire_event(
                        'battery_okay',
                        battery_level=battery_level,
                        bat_entity_id=bat_entity_id,
                        unit_of_measurement='%')
                    self.log('Fired event: {}'.format(event))
        except Exception as exc:
            self.log('Failed to update groups: {}'.format(exc), level='ERROR')
            traceback.print_exc()

    def create_battery_groups(self, battery_devices):
        # Create groups
        try:
            group_all = self.register_battery_devices(
                [x.get('entity_id') for x in battery_devices])
            low_battery_devices = []
            for dev in battery_devices:
                attrs = dev.get('attributes', {})
                critical = attrs.get('battery_level_low')
                if critical is True:
                    low_battery_devices.append(dev)
            group_low = self.register_low_battery_devices(
                [x.get('entity_id') for x in low_battery_devices])
            return [group_all, group_low]
        except Exception as exc:
            self.log('Failed to set group state: {}'.format(exc), level='ERROR')
            traceback.print_exc()

    def battery_level(self, level):
        if level is None:
            return
        if isinstance(level, str):
            try:
                return int(level)
            except ValueError:
                return int(float())

    def battery_icon(self, battery_level, charging=False):
        icon = 'mdi:battery'
        if battery_level is None:
            return icon + '-unknown'
        if battery_level is False:
            return icon
        try:
            battery_level = int(battery_level)
        except ValueError:
            return icon
        if charging and battery_level > 10:
            icon += '-charging-{}'.format(
                int(round(battery_level / 20 - .01)) * 20)
        elif charging:
            icon += '-outline'
        elif battery_level <= 5:
            icon += '-alert'
        elif 5 < battery_level < 95:
            icon += '-{}'.format(int(round(battery_level / 10 - .01)) * 10)
        return icon

    def battery_entity_name(self, entity):
        namespace, entity_name = entity.split('.')
        return 'battery.{}_{}'.format(namespace, entity_name)

    def battery_critical(self, battery_level, custom_threshold=None):
        if custom_threshold:
            threshold = custom_threshold
        else:
            threshold = self.args.get('threshold', 20)
        if battery_level is None:
            return
        if isinstance(battery_level, bool):
            return battery_level
        try:
            return int(battery_level) < threshold
        except ValueError:
            return int(float(battery_level)) < threshold

    def create_battery_device(self, entity, battery_level):
        bat_entity = self.battery_entity_name(entity)
        attrs = self.get_state(entity, attribute='all').get('attributes', {})
        custom_friendly_name = attrs.get('battery_friendly_name')
        if custom_friendly_name:
            friendly_name = custom_friendly_name
        else:
            entity_friendly_name = attrs.get('friendly_name')
            friendly_name = entity_friendly_name if entity_friendly_name else \
                '{} battery'.format(entity)
        custom_battery_threshold = attrs.get('battery_threshold')
        bat_prop = 'state'
        if 'battery_level' in attrs:
            bat_prop = 'battery_level'
        elif 'battery' in attrs:
            bat_prop = 'battery'
        # Publish state
        try:
            return self.set_state(
                bat_entity,
                state=battery_level if battery_level else 'unknown',
                attributes={
                    'friendly_name': friendly_name,
                    'icon': self.battery_icon(battery_level),
                    'monitored_entity': entity,
                    'monitored_attribute': bat_prop,
                    'unit_of_measurement': '%',
                    'battery_level_low': self.battery_critical(
                        battery_level, custom_battery_threshold)
                })
        except Exception as exc:
            self.log('Failed to set state: {}'.format(exc), level='ERROR')
            traceback.print_exc()

    def create_binary_battery_device(self, entity, battery_critical):
        bat_entity = self.battery_entity_name(entity)
        # Publish state
        try:
            return self.set_state(
                bat_entity,
                state=battery_critical,
                attributes={
                    'friendly_name': '{} battery'.format(entity),
                    'icon': 'mdi:battery-alert' if battery_critical else
                            'mdi:battery',
                    'monitored_entity': entity,
                    'monitored_attribute': 'battery_critical',
                    'battery_level_low': self.battery_critical(
                        battery_critical)
                })
        except Exception as exc:
            self.log('Failed to set state: {}'.format(exc), level='ERROR')
            traceback.print_exc()

    def process_entity(self, devices, entity_id):
        # Skip groups and ignored entities
        if (entity_id.startswith('group.') or
                entity_id in self.args.get('ignored_entities', [])):
            return
        battery_level = None
        attrs = devices.get(entity_id, {}).get('attributes')
        if attrs.get('battery_ignore'):
            self.log('Skip entity {} for having `battery_ignore` set '
                     'to true.'.format(entity_id), level='DEBUG')
            return
        if 'battery' in attrs:
            battery_level = attrs.get('battery')
            return self.create_battery_device(entity_id, battery_level)
        elif 'battery_level' in attrs:
            battery_level = attrs.get('battery_level')
            return self.create_battery_device(entity_id, battery_level)
        elif 'battery_critical' in attrs:
            battery_critical = attrs.get('battery_critical')
            return self.create_binary_battery_device(entity_id,
                                                     battery_critical)
        elif attrs.get('battery_device'):
            state = devices.get(entity_id, {}).get('state')
            return self.create_battery_device(entity_id, state)

    def create_battery_devices(self):
        devices = self.get_state()
        battery_devices = []
        for entity_id in devices:
            bat_dev = self.process_entity(devices, entity_id)
            if bat_dev:
                battery_devices.append(bat_dev)
        return battery_devices


# vim: set et ts=4 sw=4 :
