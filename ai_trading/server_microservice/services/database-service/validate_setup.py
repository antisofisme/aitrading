#!/usr/bin/env python3
"""
Validation script for database service setup
Checks dependencies, environment, and ClickHouse connectivity
"""

import os
import sys
import asyncio
import importlib

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} not supported. Need 3.8+")
        return False

def check_required_packages():
    """Check if required packages are installed"""
    required_packages = [
        'httpx', 'asyncio', 'fastapi', 'uvicorn', 
        'clickhouse_connect', 'asyncpg', 'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment_variables():
    """Check required environment variables"""
    env_vars = {
        'CLICKHOUSE_HOST': os.getenv('CLICKHOUSE_HOST', 'database-clickhouse'),
        'CLICKHOUSE_PORT': os.getenv('CLICKHOUSE_PORT', '8123'),
        'CLICKHOUSE_USER': os.getenv('CLICKHOUSE_USER', 'default'),
        'CLICKHOUSE_PASSWORD': os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')
    }
    
    print("📋 Environment Variables:")
    for key, value in env_vars.items():
        masked_value = "***" if 'password' in key.lower() else value
        print(f"   {key}: {masked_value}")
    
    return True

async def check_clickhouse_connectivity():
    """Test ClickHouse connectivity"""
    try:
        import httpx
        
        host = os.getenv('CLICKHOUSE_HOST', 'database-clickhouse')
        port = os.getenv('CLICKHOUSE_PORT', '8123')
        user = os.getenv('CLICKHOUSE_USER', 'default')
        password = os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse_password_2024')
        
        url = f"http://{host}:{port}"
        auth = (user, password) if password else None
        
        async with httpx.AsyncClient() as client:
            # Test basic connectivity
            response = await client.get(f"{url}/ping", auth=auth, timeout=10.0)
            if response.status_code == 200:
                print(f"✅ ClickHouse connectivity: {url}")
                
                # Test database creation
                response = await client.post(
                    url, 
                    params={'query': 'SHOW DATABASES'}, 
                    auth=auth,
                    timeout=10.0
                )
                if response.status_code == 200:
                    databases = response.text.strip().split('\n')
                    print(f"   Available databases: {databases}")
                    return True
                else:
                    print(f"❌ ClickHouse query test failed: HTTP {response.status_code}")
                    return False
            else:
                print(f"❌ ClickHouse connectivity failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ ClickHouse connectivity test failed: {e}")
        print(f"   Make sure ClickHouse is running at {host}:{port}")
        return False

def check_file_structure():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'src/business/database_manager.py',
        'src/business/connection_factory.py', 
        'src/api/database_endpoints.py',
        'src/schemas/clickhouse/raw_data_schemas.py',
        'requirements.txt'
    ]
    
    missing_files = []
    base_path = os.path.dirname(__file__)
    
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

async def main():
    """Run all validation checks"""
    print("🔍 Database Service Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages), 
        ("Environment Variables", check_environment_variables),
        ("File Structure", check_file_structure),
        ("ClickHouse Connectivity", check_clickhouse_connectivity)
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        print(f"\n📝 {check_name}:")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                success = await check_func()
            else:
                success = check_func()
                
            if success:
                passed += 1
                print(f"   Status: PASSED ✅")
            else:
                failed += 1
                print(f"   Status: FAILED ❌")
                
        except Exception as e:
            failed += 1
            print(f"   Status: ERROR ❌ - {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All checks passed! Database service is ready to run.")
        print("\n💡 Next steps:")
        print("   1. Start ClickHouse: docker-compose up -d database-clickhouse")
        print("   2. Start database service: python main.py")
        print("   3. Test tick insertion: python test_tick_insertion.py")
    else:
        print(f"⚠️  {failed} check(s) failed. Please fix the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)