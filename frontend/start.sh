#!/bin/sh

# Default PORT to 8080 if not set (Cloud Run default)
if [ -z "$PORT" ]; then
  export PORT=8080
fi

# Ensure BACKEND_URL is set
if [ -z "$BACKEND_URL" ]; then
  echo "WARNING: BACKEND_URL is not set!"
fi

# Substitute env vars into nginx configuration template
envsubst '$PORT $BACKEND_URL' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start Nginx in foreground
echo "Starting Nginx on port $PORT proxying /api to $BACKEND_URL..."
exec nginx -g "daemon off;"
