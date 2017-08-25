#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")" || exit 9

# Watch for Hue Dimmer Switch events
/srv/hass/scripts/zhue.sh swd &

# Start external HTTP API
/home/pschmitt/dev/golang/bin/shell2http \
    -port 8993 -form -show-errors -include-stderr \
    /ha/restart 'sudo systemctl daemon-reload; sudo systemctl restart hass' \
    /speakcast '/home/pschmitt/dev/chromecast/speakcast.sh $v_msg' \
    /dash/pressed '/srv/hass/extra/dash-count.sh $v_dash_id' \
    /shield/kodi 'adb connect 10.7.0.241; /home/pschmitt/dev/adb.sh/adb.sh app start kodi; adb disconnect 10.7.0.241' \
    /shield/wake 'adb connect 10.7.0.241; /home/pschmitt/dev/adb.sh/adb.sh wake; adb disconnect 10.7.0.241' \
    /shield/reboot 'adb connect 10.7.0.241; adb reboot' \
    /kvm/win81-gpu/restart '/srv/hass/scripts/kvm.sh win8.1-gpu restart' \
    /kvm/win81-gpu/start '/srv/hass/scripts/kvm.sh win8.1-gpu start' \
    /kvm/win81-gpu/stop '/srv/hass/scripts/kvm.sh win8.1-gpu shutdown'
