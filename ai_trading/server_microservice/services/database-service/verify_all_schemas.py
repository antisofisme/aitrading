#!/usr/bin/env python3
"""
Verify all database schemas across all database stacks
"""

import asyncio
import sys
from pathlib import Path

# Add src path to sys.path for proper imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.business.database_manager import DatabaseManager
import httpx


async def verify_all_schemas():
    """Verify all schemas across all database stacks"""
    print("🔍 Verifying ALL database schemas...")
    print("=" * 60)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ Database manager initialized")
        print()
        
        # 1. ClickHouse - Check all tables
        print("📊 CLICKHOUSE DATABASES & TABLES:")
        print("-" * 40)
        
        # Check default database tables
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Show all databases
            response = await client.get("http://localhost:8123/?query=SHOW+DATABASES", auth=("default", ""))
            databases = response.text.strip().split('\n')
            print(f"🗄️  Available databases: {', '.join(databases)}")
            
            # Check tables in default database
            response = await client.get("http://localhost:8123/?query=SHOW+TABLES+FROM+default", auth=("default", ""))
            default_tables = response.text.strip().split('\n') if response.text.strip() else []
            print(f"📋 Default database tables ({len(default_tables)}):")
            for i, table in enumerate(default_tables, 1):
                if table.strip():
                    print(f"  {i:2d}. {table}")
            
            # Check trading_data database if exists
            try:
                response = await client.get("http://localhost:8123/?query=SHOW+TABLES+FROM+trading_data", auth=("default", ""))
                if response.status_code == 200:
                    trading_tables = response.text.strip().split('\n') if response.text.strip() else []
                    print(f"📋 Trading_data database tables ({len(trading_tables)}):")
                    for i, table in enumerate(trading_tables, 1):
                        if table.strip():
                            print(f"  {i:2d}. {table}")
                else:
                    print("❌ trading_data database not accessible")
            except Exception as e:
                print(f"❌ trading_data database error: {e}")
        
        print()
        
        # 2. PostgreSQL - Check connection and basic info
        print("🐘 POSTGRESQL:")
        print("-" * 40)
        try:
            result = await db_manager.execute_postgresql_query(
                "SELECT current_database(), version()", 
                "postgres"
            )
            if result:
                print(f"✅ PostgreSQL connected: {result[0]}")
                
                # Check available databases
                db_result = await db_manager.execute_postgresql_query(
                    "SELECT datname FROM pg_database WHERE datistemplate = false",
                    "postgres"
                )
                databases = [row['datname'] for row in db_result]
                print(f"🗄️  Available databases: {', '.join(databases)}")
                
                # Try to connect to specific databases and check tables
                for db_name in ['ai_trading_auth', 'neliti_main']:
                    if db_name in databases:
                        try:
                            tables_result = await db_manager.execute_postgresql_query(
                                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
                                db_name
                            )
                            table_names = [row['tablename'] for row in tables_result]
                            print(f"📋 {db_name} tables ({len(table_names)}): {', '.join(table_names) if table_names else 'No tables'}")
                        except Exception as e:
                            print(f"❌ {db_name} error: {str(e)[:100]}")
            else:
                print("❌ PostgreSQL connection failed")
        except Exception as e:
            print(f"❌ PostgreSQL error: {e}")
        
        print()
        
        # 3. ArangoDB - Check connection
        print("🕸️  ARANGODB:")
        print("-" * 40)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8529/_api/version")
                if response.status_code == 200:
                    version_info = response.json()
                    print(f"✅ ArangoDB connected: {version_info.get('version', 'Unknown')}")
                    
                    # Try to get database list
                    try:
                        response = await client.get("http://localhost:8529/_api/database")
                        if response.status_code == 200:
                            databases = response.json().get('result', [])
                            print(f"🗄️  Databases: {', '.join(databases)}")
                        else:
                            print("⚠️  Could not list databases (may need authentication)")
                    except Exception as e:
                        print(f"⚠️  Database listing error: {str(e)[:50]}")
                else:
                    print(f"❌ ArangoDB connection failed: {response.status_code}")
        except Exception as e:
            print(f"❌ ArangoDB error: {e}")
        
        print()
        
        # 4. Weaviate - Check connection
        print("🔍 WEAVIATE:")
        print("-" * 40)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8080/v1/.well-known/ready")
                if response.status_code == 200:
                    print("✅ Weaviate connected and ready")
                    
                    # Try to get schema
                    response = await client.get("http://localhost:8080/v1/schema")
                    if response.status_code == 200:
                        schema = response.json()
                        classes = schema.get('classes', [])
                        class_names = [c.get('class', 'Unknown') for c in classes]
                        print(f"📋 Classes ({len(classes)}): {', '.join(class_names) if class_names else 'No classes'}")
                    else:
                        print("⚠️  Could not retrieve schema")
                else:
                    print(f"❌ Weaviate not ready: {response.status_code}")
        except Exception as e:
            print(f"❌ Weaviate error: {e}")
        
        print()
        
        # 5. DragonflyDB (Redis-compatible) - Check connection
        print("🐉 DRAGONFLYDB:")
        print("-" * 40)
        try:
            import redis.asyncio as redis
            client = redis.Redis(host='localhost', port=6379, socket_timeout=5)
            
            info = await client.info()
            if info:
                print(f"✅ DragonflyDB connected: {info.get('server_version', 'Unknown version')}")
                
                # Get some basic stats
                keyspace = await client.dbsize()
                print(f"📊 Keys in database: {keyspace}")
                
                # Try to get a sample of keys
                keys = await client.keys("*")
                if keys:
                    sample_keys = keys[:10]  # First 10 keys
                    print(f"🔑 Sample keys: {', '.join(k.decode() if isinstance(k, bytes) else str(k) for k in sample_keys)}")
                else:
                    print("📊 No keys found")
                    
            await client.close()
        except Exception as e:
            print(f"❌ DragonflyDB error: {e}")
        
        print()
        
        # 6. Redpanda (Kafka-compatible) - Check connection
        print("🐼 REDPANDA:")
        print("-" * 40)
        try:
            # Basic HTTP check for Redpanda Admin API
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:9644/v1/cluster/health_overview")
                if response.status_code == 200:
                    health = response.json()
                    print(f"✅ Redpanda connected: {health.get('cluster_health', 'Unknown')}")
                    
                    # Try to get topics
                    response = await client.get("http://localhost:9644/v1/topics")
                    if response.status_code == 200:
                        topics = response.json()
                        topic_names = [t.get('name', 'Unknown') for t in topics]
                        print(f"📋 Topics ({len(topics)}): {', '.join(topic_names) if topic_names else 'No topics'}")
                    else:
                        print("⚠️  Could not list topics")
                else:
                    print(f"❌ Redpanda health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Redpanda error: {e}")
        
        print()
        print("=" * 60)
        print("🎉 Schema verification completed!")
        
        # Cleanup
        await db_manager.shutdown()
        
    except Exception as e:
        print(f"❌ Error during schema verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("🏗️  ALL DATABASE STACKS SCHEMA VERIFICATION")
    asyncio.run(verify_all_schemas())