#!/usr/bin/env python3
"""
Simple Database Service - Minimal Working Version for Testing
"""

import time
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Database Service",
    description="Simple database service for testing",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

# Simple health check
@app.get("/health")
def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "service": "database-service",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Database Service is running",
        "version": "2.0.0",
        "schema_endpoints": {
            "clickhouse": "/api/v1/schemas/clickhouse",
            "postgresql": "/api/v1/schemas/postgresql"
        }
    }

# Schema endpoints
@app.get("/api/v1/schemas/clickhouse")
def get_clickhouse_schemas():
    """Get ClickHouse schemas"""
    try:
        from src.schemas.clickhouse.raw_data_schemas import ClickhouseRawDataSchemas
        tables = ClickhouseRawDataSchemas.get_all_tables()
        return {
            "status": "available",
            "schemas": list(tables.keys()),
            "total_tables": len(tables),
            "database_type": "ClickHouse"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "database_type": "ClickHouse"
        }

@app.get("/api/v1/schemas/postgresql") 
def get_postgresql_schemas():
    """Get PostgreSQL schemas"""
    try:
        from src.schemas.postgresql.user_auth_schemas import PostgresqlUserAuthSchemas
        tables = PostgresqlUserAuthSchemas.get_all_tables() 
        return {
            "status": "available", 
            "schemas": list(tables.keys()),
            "total_tables": len(tables),
            "database_type": "PostgreSQL"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e), 
            "database_type": "PostgreSQL"
        }

if __name__ == "__main__":
    print("🚀 Starting Simple Database Service on port 8008")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0", 
        port=8008,
        reload=False
    )