"""
Central Hub SDK - Python Package Setup
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="central-hub-sdk",
    version="2.0.0",
    author="Suho Trading System",
    author_email="dev@suho-trading.com",
    description="Official Python SDK for Suho Central Hub - Multi-database integration with auto-initialization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/suho-trading/central-hub-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        # Database drivers
        "asyncpg>=0.29.0",                    # TimescaleDB (PostgreSQL)
        "clickhouse-connect>=0.6.8",          # ClickHouse
        "redis[hiredis]>=5.0.0",              # DragonflyDB (Redis-compatible)
        "python-arango>=7.9.0",               # ArangoDB
        "weaviate-client>=4.4.0",             # Weaviate
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
