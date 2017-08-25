#!/usr/bin/env bash

    cd "$(readlink -f "$(dirname "$0")")" || exit 9

usage() {
    echo "$(basename "$0") DASH_ID"
}

if [[ $# -eq 0 ]]
then
    usage
    exit 2
fi

DATA_FILE=../data/dash/${1}_press.count

if [[ -f "$DATA_FILE" ]]
then
    n=$(< "$DATA_FILE")
    echo $(( n + 1 )) > "$DATA_FILE"
else
    echo 1 > "$DATA_FILE"
fi

# cat "$DATA_FILE"
