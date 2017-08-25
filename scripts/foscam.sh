#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")" || exit 9

SECRETS_FILE=../config/secrets.yaml

usage() {
    echo "Usage: $(basename "$0") CAMERA ir|modect|sodect|state|snap [PARAMS]"
}

usage_stateful() {
    echo "Usage: $(basename "$0") CAMERA $1 [on|off|state|toggle]"
}

__extract_names() {
    sed -rn 's/foscam_(.*)_hostname.*/\1/p' "$SECRETS_FILE"
}

__extract_value() {
    awk '/foscam_'"$1"'_'"$2"'/ {print $2}' "$SECRETS_FILE"
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

rq() {
    local api_url resp
    api_url="http://$hostname:88/cgi-bin/CGIProxy.fcgi?&usr=${username}&pwd=${password}&cmd=${1}"
    resp=$(curl -qqs "$api_url")
    if ! grep -q '<result>0</result>' <<< "$resp"
    then
        echo "WARNING: API call failed" >&2
        echo "URL: $api_url" >&2
    fi
    echo "$resp"
}

dev_state() {
    rq getDevState
}

ir_on() {
    rq openInfraLed
}

ir_off() {
    rq closeInfraLed
}

ir_toggle() {
    ir_state && ir_off || ir_on
}

ir_state() {
    dev_state | grep -q '<infraLedState>1</infraLedState>'
}

modect_on() {
    rq 'setMotionDetectConfig&isEnable=1'
}

modect_off() {
    rq 'setMotionDetectConfig&isEnable=0'
}

modect_toggle() {
    modect_state && modect_off || modect_on
}

modect_state() {
    rq getMotionDetectConfig | grep -q '<isEnable>1</isEnable>'
}

sodect_on() {
    rq 'setAudioAlarmConfig&isEnable=1'
}

sodect_off() {
    rq 'setAudioAlarmConfig&isEnable=0'
}

sodect_toggle() {
    sodect_state && sodect_off || sodect_on
}

sodect_state() {
    rq getAudioAlarmConfig | grep -q '<isEnable>1</isEnable>'
}

do_stateful() {
    case "$2" in
        on) ${1}_on ;;
        off) ${1}_off ;;
        toggle) ${1}_toggle ;;
        state) ${1}_state && echo on || { echo off; return 1; } ;;
        -h|--help|h|help) usage_stateful "$1" ;;
        *) usage_stateful "$1"; exit 2 ;;
    esac
}

snap() {
    local api_url dest="$1"
    api_url="http://$hostname:88/cgi-bin/CGIProxy.fcgi?&usr=${username}&pwd=${password}&cmd=snapPicture2"
    if [[ -n "$dest" ]]
    then
        curl -fqqs "$api_url" > "$dest"
    else
        echo "Missing destination file" >&2
        exit 2
    fi
}

[[ $# -eq 0 ]] && { usage; exit; }

# Construct config array
# declare -A foscam_hostnames foscam_usernames foscam_passwords
# for n in $(__extract_names)
# do
#     foscam_hostnames[$n]=$(__get_hostname "$n")
#     foscam_usernames[$n]=$(__get_username "$n")
#     foscam_passwords[$n]=$(__get_password "$n")
# done
#
# host=${foscam_hostnames[$1]}
# username=${foscam_usernames[$1]}
# password=${foscam_passwords[$1]}
# shift
# hostname=${foscam_hostnames[$1]}
# username=${foscam_usernames[$1]}
# password=${foscam_passwords[$1]}

cam_names=$(__extract_names)
if ! grep -q -w "$1" <<< "$cam_names"
then
    echo "No camera named $1 found. Available cameras: $(tr '\n' ' ' <<< $cam_names)"
    exit 3
fi

hostname=$(__get_hostname "$1")
username=$(__get_username "$1")
password=$(__get_password "$1")
shift

case "$1" in
    state) dev_state ;;
    ir|modect|sodect) do_stateful "$1" "$2" ;;
    s|snap) snap "$2" ;;
    -h) usage ;;
    *)
        usage
        exit 2
        ;;
esac
