#!/bin/bash

case "$1" in
  down)
    docker compose down
    ;;
  down-all)
    docker compose down -v
    ;;
  build)
    docker compose build
    ;;
  up)
    docker compose up -d
    ;;
  stop)
    docker compose stop
    ;;
  start)
    docker compose build
    docker compose up -d
    clear
    ;;
  list)
    docker ps
    ;;
  *)
    echo "Usage: $0 {down|down-all|build|up|stop|list}"
    ;;
esac
