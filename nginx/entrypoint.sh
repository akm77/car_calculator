#!/usr/bin/env bash
set -euo pipefail

DOMAIN=${DOMAIN:-}

if [[ -z "$DOMAIN" ]]; then
  echo "[nginx] ERROR: DOMAIN env variable is required" >&2
  exit 1
fi

TEMPLATES_DIR=/etc/nginx/templates
CONF_DIR=/etc/nginx/conf.d
CERT_LIVE_DIR=/etc/letsencrypt/live/$DOMAIN
DEFAULT_CONF=$CONF_DIR/default.conf

mkdir -p "$CONF_DIR"

if [[ -f "$CERT_LIVE_DIR/fullchain.pem" && -f "$CERT_LIVE_DIR/privkey.pem" ]]; then
  echo "[nginx] Using HTTPS configuration for $DOMAIN"
  export DOMAIN_PLACEHOLDER="$DOMAIN"
  envsubst < "$TEMPLATES_DIR/app_https.conf.template" > "$DEFAULT_CONF"
else
  echo "[nginx] Certs not found, using HTTP configuration for $DOMAIN"
  export DOMAIN_PLACEHOLDER="$DOMAIN"
  envsubst < "$TEMPLATES_DIR/app_http.conf.template" > "$DEFAULT_CONF"
fi

# Ensure webroot exists for ACME challenges
mkdir -p /var/www/certbot

# Run nginx in foreground
exec nginx -g 'daemon off;'

