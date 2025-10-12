#!/bin/bash
# Data Bridge Health Check
# Verifies all dependencies (TimescaleDB, ClickHouse, NATS, Kafka) are ready

python3 /app/src/healthcheck.py || exit 1
