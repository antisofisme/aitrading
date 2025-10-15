#!/bin/bash
# Central Hub Health Check
# Verifies API is responding on port 7000

curl -f http://localhost:7000/health || exit 1
