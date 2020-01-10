function basebetterweather(widget_id, url, skin, parameters) {
    // Will be using "self" throughout for the various flavors of "this"
    // so for consistency ...

    self = this

    self.weather_icons = {
      "rain": '&#xe009',
      "snow": '&#xe036',
      "sleet": '&#xe003',
      "wind": '&#xe021',
      "fog": '&#xe01b',
      "cloudy": '&#xe000',
      "clear-day": '&#xe028',
      "clear-night": '&#xe02d',
      "partly-cloudy-day": '&#xe001',
      "partly-cloudy-night": '&#xe002'
    }

    // Initialization
    self.widget_id = widget_id
    self.parameters = parameters

    // Define callbacks for entities - this model allows a widget to monitor multiple entities if needed
    // Initial will be called when the dashboard loads and state has been gathered for the entity
    // Update will be called every time an update occurs for that entity

    self.OnStateAvailable = OnStateAvailable
    self.OnStateUpdate = OnStateUpdate
    self.OnButtonClick = OnButtonClick

    var callbacks = [{
        "selector": '#' + widget_id, "action": "click", "callback": self.OnButtonClick
    }]

    var monitored_entities = [
        // {"entity": "sensor.dark_sky_humidity", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        {"entity": "sensor.dark_sky_precip_probability", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        // {"entity": "sensor.dark_sky_precip_intensity", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        // {"entity": "sensor.dark_sky_wind_speed", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        // {"entity": "sensor.dark_sky_pressure", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        // {"entity": "sensor.dark_sky_wind_bearing", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        {"entity": "sensor.dark_sky_apparent_temperature", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        {"entity": "sensor.dark_sky_daytime_high_apparent_temperature_0d", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        {"entity": "sensor.dark_sky_overnight_low_apparent_temperature_0d", "initial": self.OnStateAvailable, "update": self.OnStateUpdate},
        {"entity": "sensor.dark_sky_icon", "initial": self.OnStateAvailable, "update": self.OnStateUpdate}
    ]

    // Finally, call the parent constructor to get things moving
    WidgetBase.call(self, widget_id, url, skin, parameters, monitored_entities, callbacks)

    function OnStateUpdate(self, state) {
        set_view(self, state)
    }

    function OnStateAvailable(self, state) {
        if (state.entity_id == "sensor.dark_sky_apparent_temperature") {
            self.set_field(self, "unit", state.attributes.unit_of_measurement)
        }
        set_view(self, state)
    }

    function OnButtonClick(self) {
        // window.location.href = '/rpi-reboot-weather?timeout=30&return=rpi-reboot&skin=darkpi'
        if ("url" in parameters || "dashboard" in parameters) {
            if ("url" in parameters) {
                url = parameters.url
            } else {
                url = "/" + parameters.dashboard
            }
            var i = 0;

            if ("args" in parameters) {
                url = url + "?";
                for (var key in parameters.args) {
                    if (i != 0) {
                        url = url + "&"
                    }
                    url = url + key + "=" + parameters.args[key];
                    i++
                }
            }
            if ("skin" in parameters) {
                theskin = parameters.ski
            } else {
                theskin = skin
            }

            if (i == 0) {
                url = url + "?skin=" + theskin;
                i++
            } else {
                url = url + "&skin=" + theskin;
                i++
            }

            if ("sticky" in parameters) {
                if (i == 0) {
                    url = url + "?sticky=" + parameters.sticky;
                    i++
                } else {
                    url = url + "&sticky=" + parameters.sticky;
                    i++
                }
            }

            if ("return" in parameters) {
                if (i == 0) {
                    url = url + "?return=" + parameters.return;
                    i++
                } else {
                    url = url + "&return=" + parameters.return;
                    i++
                }
            }

            if ("timeout" in parameters) {
                if (i == 0) {
                    url = url + "?timeout=" + parameters.timeout;
                    i++
                } else {
                    url = url + "&timeout=" + parameters.timeout;
                    i++
                }
            }

            window.location.href = url
        }
    }

    function set_view(self, state) {
        if (state.entity_id == "sensor.dark_sky_icon") {
            self.set_field(self, "dark_sky_icon", self.weather_icons[state.state])
        } else {
            var field = state.entity_id.split(".")[1]
            self.set_field(self, field, Math.round(state.state))
        }
    }
}
