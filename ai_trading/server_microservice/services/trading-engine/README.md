# Trading Engine Service

## Overview
Core trading logic including technical analysis and signal generation.

## Responsibilities
- Technical analysis (RSI, MACD, etc)
- Signal generation
- Risk management
- Position management
- Trading strategy execution

## Dependencies
- TA-Lib for technical indicators
- NumPy, Pandas for data processing
- Basic ML libraries

## Resources
- CPU: 4 cores
- Memory: 4GB RAM
- Port: 8002

## API Endpoints
```
GET  /health           - Health check
POST /analyze          - Technical analysis
POST /signals          - Generate trading signals
GET  /indicators       - Available indicators
POST /risk-check       - Risk assessment
```