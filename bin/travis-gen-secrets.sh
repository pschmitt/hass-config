#!/usr/bin/env bash

cd "$(readlink -f "$(dirname "$0")")"/../config || exit 9

sed -r 's/^([^#][^:]+):(.+)/\1: travis_secret/' secrets.yaml > travis_secrets.yaml
