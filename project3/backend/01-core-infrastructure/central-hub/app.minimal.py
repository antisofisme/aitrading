#!/usr/bin/env python3
"""
Minimal Central Hub Service
"""

from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Central Hub", version="1.0.0")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "central-hub",
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {"message": "Central Hub Service Running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))
    uvicorn.run(app, host="0.0.0.0", port=port)