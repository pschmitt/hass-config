#!/usr/bin/env bash

DEST_HOST=gateway

# nasteanas.lan:8123
UCI_ORIG="$(ssh root@${DEST_HOST} uci get sslh.default.ssl)"

# Set redirection to nasteanas.lan:443
ssh "root@${DEST_HOST}" "uci set sslh.default.ssl=nasteanas.lan:443 && uci commit sslh && /etc/init.d/sslh restart"

# Request a new certificate
sudo certbot certonly --standalone \
    -d home.comreset.io \
    -d home-comreset-io.duckdns.org

# Revert redirection
ssh "root@${DEST_HOST}" "uci set sslh.default.ssl=${UCI_ORIG} && uci commit sslh && /etc/init.d/sslh restart"

# Generate a pfx for emby
sudo openssl pkcs12 -export -out ~emby/ssl/home.comreset.io.pfx \
    -inkey /etc/letsencrypt/live/home.comreset.io/privkey.pem \
    -in /etc/letsencrypt/live/home.comreset.io/cert.pem \
    -certfile /etc/letsencrypt/live/home.comreset.io/chain.pem
