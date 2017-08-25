#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")" || exit 9

SECRETS_FILE=../config/secrets.yaml
PHONE_SSH_PORT=2222
PHONE_PORT=8080

usage() {
    echo "Usage: $(basename "$0") cam|torch|ffc|battery|reboot PARAMS"
}

usage_stateful() {
    echo "Usage: $(basename "$0") $1 [on|off|toggle|state]"
}

__extract_names() {
    sed -rn 's/android_cam_(.*)_hostname.*/\1/p' "$SECRETS_FILE"
}

__extract_value() {
   awk '/android_cam_'"$1"'_'"$2"'/ {print $2; exit}' "$SECRETS_FILE"
}

__get_hostname() {
    __extract_value "$1" hostname
}

__get_username() {
    __extract_value "$1" username
}

__get_password() {
    __extract_value "$1" password
}

resolve() {
    # dig "$1" | awk '/^;; ANSWER SECTION:$/ { getline ; print $5 }'
    getent hosts "$1" | awk '{ print $1;exit }'
}

adb_connect() {
    local phone_ip
    phone_ip=$(resolve "$PHONE_HOSTNAME")
    if ! adb devices | grep -q "${PHONE_HOSTNAME}\|${phone_ip}"
    then
        adb connect "$PHONE_HOSTNAME"
    fi
}

ssh_su_exec() {
    ssh -q -o StrictHostKeyChecking=no -p "$PHONE_SSH_PORT" \
        "${PHONE_HOSTNAME}" 'su -c "'"$1"'"'
}

get_main_activity() {
    # ssh_su_exec 'pm dump com.pas.webcam.pro' | \
    #     grep -A1 -m 1 MAIN | awk 'END { print $2 }' | tr -dc '[[:print:]]'
    echo 'com.pas.webcam.pro/com.pas.webcam.Rolling'
}

cam_on() {
    # adb_connect
    # /home/pschmitt/dev/adb.sh/adb.sh app start cam
    local main_activity
    main_activity=$(get_main_activity)
    ssh_su_exec "am start $main_activity"
}

cam_off() {
    # adb_connect
    # # Stop app
    # /home/pschmitt/dev/adb.sh/adb.sh app stop cam
    # # lock screen
    # ~/dev/adb.sh/adb.sh lock
    # Stop app
    ssh_su_exec "am force-stop com.pas.webcam.pro"
    # TODO Lock screen?
}

cam_toggle() {
    if cam_state
    then
        cam_off
    else
        cam_on
    fi
}

cam_state() {
    rq 2>/dev/null | grep -q '<title>IP Webcam</title>' #> /dev/null 2>&1
}

rq() {
    curl -qqs -m 3 -u "${PHONE_USERNAME}:${PHONE_PASSWORD}" \
        "http://${PHONE_HOSTNAME}:${PHONE_PORT}/${1}"
}

torch_on() {
    rq enabletorch
}

torch_off() {
    rq disabletorch
}

torch_toggle() {
    if torch_state
    then
        torch_off
    else
        torch_on
    fi
}

torch_state() {
    if ! cam_state
    then
        return 1
    fi
    rq status.json | grep -q '"torch":"on"'
}

ffc_on() {
    rq 'settings/ffc?set=on'
}

ffc_off() {
    rq 'settings/ffc?set=off'
}

ffc_toggle() {
    if ffc_state
    then
        ffc_off
    else
        ffc_on
    fi
}

ffc_state() {
    if ! cam_state
    then
        return 1
    fi
    rq status.json | grep -q '"ffc":"on"'
}

do_stateful() {
    case "$2" in
        on) "${1}_on" ;;
        off) "${1}_off" ;;
        toggle) "${1}_toggle" ;;
        state)
            if "${1}_state"
            then
                echo on
            else
                echo off
                return 1
            fi
            ;;
        -h|--help|h|help) usage_stateful "$1" ;;
        *) usage_stateful "$1"; exit 2 ;;
    esac
}

cam_names=$(__extract_names)
if ! grep -q -w "$1" <<< "$cam_names"
then
    echo "No device named $1 found. Available cameras: $(tr '\n' ' ' <<< $cam_names)"
    exit 3
fi
PHONE_HOSTNAME=$(__get_hostname "$1")
PHONE_USERNAME=$(__get_username "$1")
PHONE_PASSWORD=$(__get_password "$1")

case "$2" in
    cam|torch|ffc) do_stateful "$2" "$3" ;;
    battery) ssh_su_exec "cat /sys/class/power_supply/battery/capacity" ;;
    reboot) ssh_su_exec "reboot" &;;
    *)
        usage
        exit 2
        ;;
esac
