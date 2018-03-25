import appdaemon.plugins.hass.hassapi as hass


class BatteryWatcher(hass.Hass):

    def initialize(self):
        devices = self.create_battery_devices()
        self.create_battery_groups(devices)
        entities = [(x.get('attributes', {}).get('monitored_entity'),
                     x.get('attributes', {}).get('monitored_attribute'))
                    for x in devices]
        for entity, attr in entities:
            if attr == 'state':
                self.listen_state(self.update_battery_device, entity)
            else:
                self.listen_state(
                    self.update_battery_device, entity, attribute=attr)

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
            self.log('Battery level unchanged for {}: {}'.format(entity, old))
            return
        self.log('Battery level updated: {} -> {}%'.format(old, new))
        threshold = self.args.get('threshold')
        bat_entity = self.battery_entity_name(entity)
        battery_level = self.battery_level_value(new)
        battery_level_old = self.battery_level_value(old)
        if isinstance(battery_level, bool):
            self.create_binary_battery_device(entity, battery_level)
        else:
            self.create_battery_device(entity, battery_level)
        # Update groups
        if battery_level is None:
            return
        if isinstance(battery_level, bool):
            if battery_level:
                self.register_low_battery_devices(bat_entity)
            else:
                self.clear_low_battery_device(bat_entity)
        elif battery_level < threshold:
            self.register_low_battery_devices(bat_entity)
            if battery_level_old >= threshold:
                self.log('Battery of {} is getting low.'.format(entity))
                event = self.fire_event(
                    'battery_low',
                    battery_level=battery_level,
                    entity_id=entity)
                self.log('Fired event: {}'.format(event))
        elif battery_level >= threshold:
            self.clear_low_battery_device(bat_entity)
            if battery_level_old < threshold:
                self.log('Battery of {} is okay again (above '
                         'threshold).'.format(entity))
                event = self.fire_event(
                    'battery_okay',
                    battery_level=battery_level,
                    entity_id=entity,
                    unit_of_measurement='%')
                self.log('Fired event: {}'.format(event))

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
            self.log('Failed to set group state: {}'.format(exc))

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

    def battery_critical(self, battery_level):
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
        entity_friendly_name = attrs.get('friendly_name')
        friendly_name = entity_friendly_name if entity_friendly_name else \
            '{} battery'.format(entity)
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
                    'battery_level_low': self.battery_critical(battery_level)
                })
        except Exception as exc:
            self.log('Failed to set state: {}'.format(exc))

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
            self.log('Failed to set state: {}'.format(exc))

    def create_battery_devices(self):
        devices = self.get_state()
        battery_devices = []
        for device in devices:
            # Skip groups and ignored entities
            if (device.startswith('group.') or
                    device in self.args.get('ignored_entities', [])):
                continue
            battery_level = None
            attrs = devices.get(device, {}).get('attributes')
            if attrs.get('battery_ignore'):
                self.log('Skip entity {} for having `battery_ignore` set '
                         'to true.'.format(device))
                continue
            if 'battery' in attrs:
                battery_level = attrs.get('battery')
                bat_dev = self.create_battery_device(device, battery_level)
            elif 'battery_level' in attrs:
                battery_level = attrs.get('battery_level')
                bat_dev = self.create_battery_device(device, battery_level)
            elif 'battery_critical' in attrs:
                battery_critical = attrs.get('battery_critical')
                bat_dev = self.create_binary_battery_device(device,
                                                            battery_critical)
            elif attrs.get('battery_device'):
                state = devices.get(device, {}).get('state')
                bat_dev = self.create_battery_device(device, state)
            else:
                # No battery attribute. Skip.
                continue
            if bat_dev:
                battery_devices.append(bat_dev)
        return battery_devices


# vim: set et ts=4 sw=4 :
