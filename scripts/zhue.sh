#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")" || exit 9

HUE_HOSTNAME=philips-hue.lan
HUE_PORT=80
HUE_USERNAME=$(awk '/hue_username/ { print $2 }' ../config/secrets.yaml)

declare -A SENSOR_BATTERY=( [bathroom]=5 [hallway]=11 [kitchen]=8 [toilet]=2 )
declare -A SENSOR_TEMPERATURE=( [bathroom]=5 [hallway]=11 [kitchen]=8 [toilet]=2 )
declare -A SENSOR_PRESENCE=( [bathroom]=6 [hallway]=12 [kitchen]=9 [toilet]=3 )
declare -A SENSOR_LIGHT_LEVEL=( [bathroom]=7 [hallway]=13 [kitchen]=10 [toilet]=4 )
declare -A SENSOR_SWITCH=( [master]=17 [living_room]=21 )
declare -A SENSOR_SWITCH_BUTTONS=(
    [1000]=INITIAL_PRESSED_1 [1001]=HOLD_1 [1002]=SHORT_RELEASED_1 [1003]=LONG_RELEASED_1
    [2000]=INITIAL_PRESSED_2 [2001]=HOLD_2 [2002]=SHORT_RELEASED_2 [2003]=LONG_RELEASED_2
    [3000]=INITIAL_PRESSED_3 [3001]=HOLD_3 [3002]=SHORT_RELEASED_3 [3003]=LONG_RELEASED_3
    [4000]=INITIAL_PRESSED_4 [4001]=HOLD_4 [4002]=SHORT_RELEASED_4 [4003]=LONG_RELEASED_4
)

__raw_rq() {
    local url="http://${HUE_HOSTNAME}:${HUE_PORT}/api/${HUE_USERNAME}/sensors/$1"
    curl -qqs "$url"
}

rq() {
    local res
    if [[ -z "$1" ]]
    then
        echo "No such room found. Available rooms: " "${!SENSOR_TEMPERATURE[@]}" >&2
        exit 3
    # elif [[ "$1" == "-e" ]]
    # then
    #     local extract=1
    fi
    res=$(__raw_rq "$1")
    if [[ -n "$EXTRACT" ]]
    then
        case "$2" in
            state)
                __json_extract_state_value "$res" "$3"
                ;;
            config)
                __json_extract_config_value "$res" "$3"
                ;;
        esac
    else
        echo "$res"
    fi
}

__json_extract_config_value() {
    if command -v jq > /dev/null 2>&1
    then
        jq -r ".|.config.$2" <<< "$1"
    else
        sed 's/{"config":.*"'"$2"'":\([^,]\+\),".*/\1/' <<< "$1"
    fi
}

__json_extract_state_value() {
    if command -v jq > /dev/null 2>&1
    then
        jq -r ".|.state.$2" <<< "$1"
    else
        sed 's/{"state":.*"'"$2"'":\([^,]\+\),".*/\1/' <<< "$1"
    fi
}

usage() {
    echo "$(basename "$0") battery|temperature|presence|lightlevel HUE_ID"
}

battery() {
    local hue_id=${SENSOR_BATTERY[$1]}
    rq "$hue_id" config battery
}

temperature() {
    local hue_id=${SENSOR_TEMPERATURE[$1]}
    rq "$hue_id" state temperature
}

presence() {
    local hue_id=${SENSOR_PRESENCE[$1]}
    rq "$hue_id" state presence
}

light_level() {
    local hue_id=${SENSOR_LIGHT_LEVEL[$1]}
    rq "$hue_id" state lightlevel
}

switch_cache() {
    local sensor_data lastupdated button
    local hue_id=${SENSOR_SWITCH[$1]}
    local cache_file="/tmp/.zhue_${hue_id}_lastupdated"
    local previous
    previous=$(cat "$cache_file" 2>/dev/null)
    sensor_data=$(rq "$hue_id")
    lastupdated=$(__json_extract_state_value "$sensor_data" lastupdated)
    button=$(__json_extract_state_value "$sensor_data" buttonevent)
    # Save to update time and button event to cache file
    echo "$lastupdated $button" > "$cache_file"
    if [[ "$previous" != "$(cat "$cache_file")" ]]
    then
        echo changed!
    fi
}

switch_cache_read() {
    local hue_id=${SENSOR_SWITCH[$1]}
    local cache_file="/tmp/.zhue_${hue_id}_lastupdated"
    cat "$cache_file"
}

switch_last_updated() {
    local hue_id=${SENSOR_SWITCH[$1]}
    rq "$hue_id" lastupdated
}

switch_pressed() {
    switch_cache "$1" | grep -q 'changed!'
}

__switch_button_translate() {
    echo "${SENSOR_SWITCH_BUTTONS[$1]}"
}

switch_check() {
    if switch_pressed "$1" > /dev/null
    then
        read -r _ button_event <<< "$(switch_cache_read "$1")"
        # button=$(sed -r 's/.*_([0-9]+)/\1/' <<< "$button_event")
        button=$(__switch_button_translate "$button_event")
        if [[ "$previous" != "$button" ]]
        then
            # echo "$(date): Button $button pressed ($button_event)"
            # Fire Home Assistant Event
            ./hass.sh event "zhue_switch_${switch_name}_button_${button}"
        fi
        previous="$button"
    fi
}

switch_daemon_multi() {
    local interval=1
    local switch_name
    while :
    do
        for switch_name in "${!SENSOR_SWITCH[@]}"
        do
            switch_check "$switch_name"
        done
        sleep "$interval"
    done
}

switch_daemon_single() {
    local interval=1
    while :
    do
        switch_check "$1"
        sleep "$interval"
    done
}

switch() {
    local translate sensor_data
    if [[ "$1" == "-t" ]]
    then
        translate=1
        shift
    fi
    local hue_id=${SENSOR_SWITCH[$1]}
    sensor_data=$(rq "$hue_id" state buttonevent)
    if [[ -z "$translate" ]]
    then
        echo "$sensor_data"
    else
        __switch_button_translate "$sensor_data"
    fi
}

if [[ "$1" == "-e" ]]
then
    EXTRACT=1
    shift
fi

case "$1" in
    battery|bat|b)
        battery "$2"
        ;;
    temperature|temp|t)
        temperature "$2"
        ;;
    presence|p)
        presence "$2"
        ;;
    lightlevel|light|lux|l|ll)
        light_level "$2"
        ;;
    switch|s)
        shift
        switch "$@"
        ;;
    swd)
        if [[ -n "$2" ]]
        then
            switch_check "$2"
        else
            switch_daemon_multi
        fi
        ;;
    help|--help|-h|h)
        usage
        ;;
    *)
        usage
        exit 2
esac
