#!/bin/bash
# Polygon Historical Downloader Health Check
# Verifies all dependencies (ClickHouse, NATS, Central Hub) are ready

python3 /app/src/healthcheck.py || exit 1
