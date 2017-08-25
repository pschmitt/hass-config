#!/usr/bin/env bash

export VIRSH_DEFAULT_CONNECT_URI=qemu:///system
DOMAIN="$1"

if ! virsh list --all 2>/dev/null | grep -q "$DOMAIN"
then
    echo "No domain named $DOMAIN found."
    exit 3
fi

is_running() {
    virsh list --all | grep -qe "${1}.*running"
}

case "$2" in
    restart)
        if is_running "$DOMAIN"
        then
            action=reboot
        else
            action=start
        fi
        ;;
    start)
        action=start
        ;;
    stop|shutdown|halt)
        action=shutdown
        ;;
esac

virsh "$action" "$DOMAIN"
