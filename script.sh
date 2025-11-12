#!/bin/bash

case "$1" in
  down)
    docker compose down
    ;;
  build)
    docker compose build web-frontend-server api-gateway-proxy-server
    ;;
  up)
    docker compose up -d web-frontend-server api-gateway-proxy-server
    ;;
  stop)
    docker compose stop
    ;;
  all)
    docker compose down
    docker compose build web-frontend-server api-gateway-proxy-server
    docker compose up -d web-frontend-server api-gateway-proxy-server
    docker compose stop
    ;;
  *)
    echo "Usage: $0 {down|build|up|stop|all}"
    ;;
esac
