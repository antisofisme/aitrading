#!/bin/bash
# Tick Aggregator Health Check
# Verifies all dependencies (TimescaleDB, NATS, ClickHouse) are ready

python3 /app/src/healthcheck.py || exit 1
