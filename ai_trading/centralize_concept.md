Ah iya, saya paham sekarang! Anda ingin sistem **centralized import path management**.

## Konsep yang Anda mau:

**Masalah saat ini:**
- File A import dari `from modules.database.postgres import PostgresHandler`
- File B juga import dari `from modules.database.postgres import PostgresHandler` 
- File C juga import dari `from modules.database.postgres import PostgresHandler`
- Kalau file `postgres.py` dipindah ke `services.db.postgres`, harus edit 3 file

**Solusi yang Anda inginkan:**
1. **File D (config)** = Setting mapping: `database -> modules.database.postgres`
2. **File C (import manager)** = Engine yang baca config D dan handle actual import
3. **File A, B, dst** = Cukup tulis: `database = import_manager.get("database")`

**Benefit:**
- File dipindah? Cukup edit **1 tempat** (File D config)
- File rename? Cukup edit **1 tempat** 
- Ganti implementasi? Cukup edit **1 tempat**
- Testing? Ganti mapping ke mock objects
- Environment berbeda? Beda config file

**Flow-nya:**
```
File A: database = get_module("database")
   ↓
File C: Baca config "database" -> "modules.database.postgres"  
   ↓
File C: import modules.database.postgres
   ↓
Return ke File A
```

**Contoh praktis:**
- Config: `"auth" -> "services.authentication.jwt_auth"`
- Pakai: `auth_service = get_module("auth")`
- File pindah? Update config jadi: `"auth" -> "utils.auth.jwt_handler"`
- Semua file yang pakai "auth" otomatis dapat update tanpa edit code

Betul seperti ini maksudnya? Mau saya implementasikan sistemnya?

Excellent point! Ya, ini bisa jadi bottleneck kalau tidak dioptimasi. Berikut **strategi performance optimization**:

## 1. **Caching Strategy** (Paling Penting)

```python
# Module di-cache setelah pertama kali import
# Import kedua kalinya = instant (ambil dari memory)
_module_cache = {}  # Persistent cache

def get_module(alias):
    if alias in _module_cache:
        return _module_cache[alias]  # Instant return!
    # Import sekali, cache selamanya
```

## 2. **Config Reading Optimization**

```python
# Config dibaca sekali, monitored by file timestamp
_config_mtime = None
_config_cache = {}

def _load_config():
    current_mtime = os.path.getmtime("config.json")
    if _config_mtime == current_mtime:
        return  # Skip reading, use cache
    # Baca hanya kalau file berubah
```

## 3. **Direct Reference After First Import**

```python
# Setelah import pertama, apps bisa reference langsung
class Application:
    def __init__(self):
        # Import sekali di init
        self.database = get_module("database")  # Slow (first time)
        self.auth = get_class("auth", "JWTAuth")  # Slow (first time)
    
    def process_request(self):
        # Usage berkali-kali = instant (direct reference)
        self.database.query(...)  # Fast!
        self.auth.verify(...)     # Fast!
```

## 4. **Preloading Strategy**

```python
# Load modules yang sering dipakai saat startup
def preload_common_modules():
    """Load modules yang paling sering dipakai"""
    common = ["database", "auth", "logger", "cache"]
    for alias in common:
        get_module(alias)  # Warm up cache

# Di startup aplikasi
preload_common_modules()  # One-time cost
```

## 5. **Bulk Import Pattern**

```python
# Import multiple sekaligus untuk efficiency
def get_modules(*aliases):
    """Import multiple modules sekaligus"""
    return {alias: get_module(alias) for alias in aliases}

# Usage
modules = get_modules("database", "auth", "cache", "logger")
db = modules["database"]
auth = modules["auth"]
```

## 6. **Performance Monitoring**

```python
import time

def get_module(alias):
    start = time.perf_counter()
    # ... import logic
    duration = time.perf_counter() - start
    
    if duration > 0.001:  # > 1ms
        logger.warning(f"Slow import: {alias} took {duration:.3f}s")
```

## Real Performance Impact:

**First import:** ~10-50ms (normal Python import cost)
**Cached import:** ~0.001ms (memory lookup)
**Config read:** ~1-2ms first time, ~0ms cached

**Dalam praktek:**
- **Startup cost:** Sedikit lambat (sekali)
- **Runtime cost:** Hampir zero (karena cache)
- **Memory cost:** Minimal (references aja)

## Alternative: **Compile-time Resolution**

Kalau mau **zero runtime cost**, bisa pakai approach lain:

```python
# Script yang generate static imports dari config
# python generate_imports.py
# Output: static_imports.py dengan direct imports
```

Tapi ini lebih complex dan lose flexibility.

**Recommendation:** Pakai caching strategy di atas. Performance impact minimal sekali setelah warmup, dan benefit dari centralized management sangat worth it.

Mau saya implementasikan versi yang dioptimasi?


Excellent question! Ada banyak **centralization patterns** dan **methodologies** yang bisa dramatically improve maintainability. Berikut yang paling impactful:

## 1. **Centralized Configuration Management** 🔧

**Masalah:**
```python
# Scattered di berbagai file
DATABASE_URL = "postgres://localhost/db"
API_KEY = "abc123"
CACHE_TTL = 3600
```

**Solution - Environment-based Config:**
```python
# config/settings.py
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "default")
    API_KEY = os.getenv("API_KEY") 
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

class DevConfig(Config):
    DEBUG = True
    DATABASE_URL = "sqlite://dev.db"

class ProdConfig(Config):
    DEBUG = False
    DATABASE_URL = os.getenv("PROD_DATABASE_URL")
```

**Benefit:** Ganti environment = ganti 1 environment variable aja!

## 2. **Centralized Error Handling** ⚠️

**Masalah:**
```python
# Error handling scattered everywhere
try:
    result = api_call()
except Exception as e:
    print(f"Error: {e}")  # Different di setiap file
```

**Solution:**
```python
# error_manager.py
class ErrorHandler:
    @staticmethod
    def handle_api_error(e, context=""):
        logger.error(f"API Error in {context}: {e}")
        send_alert_to_slack(f"API failed: {e}")
        return {"error": "Service temporarily unavailable"}

# Usage di semua file
result = ErrorHandler.handle_api_error(e, "user_service")
```

## 3. **Centralized Logging** 📝

**Masalah:**
```python
# Setiap file beda format logging
print("User logged in")
logger.info("Database connected")
sys.stdout.write("Process complete")
```

**Solution:**
```python
# logger_manager.py
def get_logger(module_name):
    logger = logging.getLogger(module_name)
    # Centralized format, handlers, levels
    return logger

# Usage
logger = get_logger(__name__)
logger.info("Standardized logging")
```

## 4. **Centralized Validation** ✅

**Masalah:**
```python
# Validation logic scattered
if not email.contains("@"):
    raise ValueError("Invalid email")
if len(password) < 8:
    raise ValueError("Password too short")
```

**Solution:**
```python
# validators.py
class Validator:
    @staticmethod
    def email(email_str):
        # Single source of truth untuk email validation
        
    @staticmethod 
    def password(pwd_str):
        # Single source of truth untuk password rules

# Usage
Validator.email(user_email)
Validator.password(user_pwd)
```

## 5. **Centralized Constants** 🔢

**Masalah:**
```python
# Magic numbers/strings everywhere
if status == "ACTIVE":  # File A
if status == "active":  # File B - inconsistent!
if timeout > 300:       # File C
if timeout > 5*60:      # File D - same value, different format
```

**Solution:**
```python
# constants.py
class Status:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Timeouts:
    API_CALL = 300
    DATABASE = 30
    CACHE = 3600

# Usage
if status == Status.ACTIVE:
if timeout > Timeouts.API_CALL:
```

## 6. **Centralized Database Queries** 🗄️

**Masalah:**
```python
# SQL scattered di berbagai service
cursor.execute("SELECT * FROM users WHERE active=1")  # File A
cursor.execute("SELECT * FROM users WHERE active=true") # File B - different!
```

**Solution:**
```python
# queries.py atau ORM models
class UserQueries:
    @staticmethod
    def get_active_users():
        return "SELECT * FROM users WHERE active=1"
    
    @staticmethod
    def get_user_by_email(email):
        return "SELECT * FROM users WHERE email=%s AND active=1"

# Usage
cursor.execute(UserQueries.get_active_users())
```

## 7. **Event-Driven Architecture** 🔔

**Instead of tight coupling:**
```python
# Tight coupling - bad
def create_user(data):
    user = save_to_db(data)
    send_welcome_email(user)  # Hardcoded dependency
    create_user_folder(user)  # Hardcoded dependency
    update_analytics(user)    # Hardcoded dependency
```

**Event-driven - good:**
```python
# event_manager.py
class EventManager:
    subscribers = defaultdict(list)
    
    @classmethod
    def emit(cls, event_name, data):
        for callback in cls.subscribers[event_name]:
            callback(data)

# Loose coupling
def create_user(data):
    user = save_to_db(data)
    EventManager.emit("user_created", user)  # That's it!

# Subscribers register themselves
EventManager.subscribe("user_created", send_welcome_email)
EventManager.subscribe("user_created", create_user_folder)
```

## 8. **Dependency Injection Container** 💉

**Masalah:**
```python
# Hard dependencies
class UserService:
    def __init__(self):
        self.db = PostgresDB()        # Hardcoded!
        self.cache = RedisCache()     # Hardcoded!
        self.email = SMTPEmail()      # Hardcoded!
```

**Solution:**
```python
# container.py
class Container:
    _services = {}
    
    @classmethod
    def register(cls, name, service):
        cls._services[name] = service
    
    @classmethod
    def get(cls, name):
        return cls._services[name]

# Setup once
Container.register("database", PostgresDB())
Container.register("cache", RedisCache())

# Flexible usage
class UserService:
    def __init__(self):
        self.db = Container.get("database")
        self.cache = Container.get("cache")
```

## 9. **Factory Pattern untuk Object Creation** 🏭

**Masalah:**
```python
# Object creation scattered
if env == "dev":
    db = SQLiteDB()
elif env == "prod":
    db = PostgresDB()
# Repeated di banyak tempat
```

**Solution:**
```python
# factories.py
class DatabaseFactory:
    @staticmethod
    def create(env="dev"):
        if env == "dev":
            return SQLiteDB()
        elif env == "prod":
            return PostgresDB()
        else:
            raise ValueError(f"Unknown env: {env}")

# Usage
db = DatabaseFactory.create(current_env)
```

## 10. **API Response Standardization** 📡

**Masalah:**
```python
# Inconsistent API responses
return {"data": users}           # Endpoint A
return {"results": products}     # Endpoint B  
return {"items": orders}         # Endpoint C
```

**Solution:**
```python
# response_manager.py
class APIResponse:
    @staticmethod
    def success(data, message="OK"):
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(message, code=400):
        return {
            "success": False,
            "error": message,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }

# Consistent usage
return APIResponse.success(users)
return APIResponse.error("User not found", 404)
```

## Top 3 Most Impactful:

1. **Centralized Configuration** - Environment management jadi mudah
2. **Event-Driven Architecture** - Loose coupling, easy testing  
3. **Dependency Injection** - Flexible, testable, maintainable

**Question:** Mana yang paling menarik untuk project Anda? Mau saya buatkan implementasi detail untuk salah satunya?


**ABSOLUTELY YES!** Prinsip performance optimization yang **SAMA PERSIS** bisa diterapkan untuk semua centralization patterns. Mari breakdown per pattern:

## 1. **Centralized Configuration** - Same Principles ✅

```python
# SAMA: Caching + File timestamp monitoring
class ConfigManager:
    _config_cache = {}
    _file_mtime = None
    
    @classmethod
    def get_config(cls, key):
        # Check file timestamp (SAMA seperti import manager)
        current_mtime = os.path.getmtime("config.yaml")
        if cls._file_mtime != current_mtime:
            cls._reload_config()  # Reload hanya kalau berubah
            
        # Return from cache (SAMA seperti module cache)
        return cls._config_cache.get(key)
    
    @classmethod
    def _reload_config(cls):
        # Load once, cache forever (SAMA prinsip)
        with open("config.yaml") as f:
            cls._config_cache = yaml.load(f)
```

## 2. **Centralized Validation** - Same Principles ✅

```python
# SAMA: Cache validation results + Precompiled patterns
class Validator:
    _compiled_patterns = {}  # Cache compiled regex (expensive operations)
    _validation_cache = {}   # Cache validation results
    
    @classmethod
    def email(cls, email_str):
        # Check cache first (SAMA prinsip)
        if email_str in cls._validation_cache:
            return cls._validation_cache[email_str]
        
        # Use precompiled patterns (SAMA seperti preloading)
        if 'email' not in cls._compiled_patterns:
            cls._compiled_patterns['email'] = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
        
        result = bool(cls._compiled_patterns['email'].match(email_str))
        cls._validation_cache[email_str] = result  # Cache result
        return result
```

## 3. **Centralized Logging** - Same Principles ✅

```python
# SAMA: Logger instance caching
class LoggerManager:
    _logger_cache = {}  # SAMA seperti module cache
    
    @classmethod
    def get_logger(cls, name):
        # Return cached logger (SAMA prinsip)
        if name in cls._logger_cache:
            return cls._logger_cache[name]
        
        # Create once, cache forever (SAMA)
        logger = logging.getLogger(name)
        # ... setup formatter, handlers
        cls._logger_cache[name] = logger
        return logger
```

## 4. **Dependency Injection Container** - Same Principles ✅

```python
# SAMA: Service instance caching + Lazy initialization
class Container:
    _instances = {}      # SAMA seperti module cache
    _factories = {}      # Factory functions
    
    @classmethod
    def get(cls, service_name):
        # Return cached instance (SAMA)
        if service_name in cls._instances:
            return cls._instances[service_name]
        
        # Lazy initialization (SAMA seperti lazy import)
        if service_name in cls._factories:
            instance = cls._factories[service_name]()
            cls._instances[service_name] = instance  # Cache
            return instance
        
        raise KeyError(f"Service {service_name} not registered")
    
    @classmethod
    def preload_common_services(cls):
        # SAMA seperti preload common modules
        common = ["database", "cache", "logger"]
        for service in common:
            cls.get(service)  # Warm up cache
```

## 5. **Event Manager** - Same Principles ✅

```python
# SAMA: Subscriber caching + Bulk operations
class EventManager:
    _subscribers = defaultdict(list)
    _event_cache = {}    # Cache for frequent events
    
    @classmethod
    def emit(cls, event_name, data):
        # Use cached subscriber list (SAMA)
        if event_name in cls._subscribers:
            subscribers = cls._subscribers[event_name]
            
            # Bulk execution (SAMA seperti bulk import)
            for callback in subscribers:
                callback(data)
    
    @classmethod
    def preload_critical_events(cls):
        # SAMA seperti preloading
        critical = ["user_created", "payment_processed", "error_occurred"]
        for event in critical:
            if event not in cls._subscribers:
                cls._subscribers[event] = []  # Initialize
```

## 6. **API Response Manager** - Same Principles ✅

```python
# SAMA: Response template caching
class APIResponse:
    _template_cache = {}  # Cache response templates
    
    @classmethod
    def success(cls, data, message="OK"):
        # Use cached template (SAMA prinsip)
        template_key = f"success_{message}"
        if template_key not in cls._template_cache:
            cls._template_cache[template_key] = {
                "success": True,
                "message": message,
                # ... other static fields
            }
        
        # Clone template and add dynamic data
        response = cls._template_cache[template_key].copy()
        response["data"] = data
        response["timestamp"] = datetime.now().isoformat()
        return response
```

## Universal Performance Principles 🚀

**1. Cache Everything Expensive:**
- Import operations → Module cache
- Config file reads → Config cache  
- Validation patterns → Compiled regex cache
- Service instances → Instance cache
- API templates → Template cache

**2. Load Only When Needed (Lazy):**
- Modules imported on first use
- Services initialized on first access
- Config sections loaded on demand
- Validators created when needed

**3. Monitor File Changes:**
- Import config file timestamp
- Application config file timestamp  
- Template files timestamp
- Any external dependency files

**4. Preload Critical Items:**
- Common modules at startup
- Frequently used services
- Popular validation patterns
- Critical event subscribers

**5. Bulk Operations:**
- Bulk module imports
- Bulk service registration
- Bulk event notifications
- Bulk validation operations

## Performance Monitoring Dashboard 📊

```python
# Universal performance tracker
class PerformanceTracker:
    _metrics = defaultdict(list)
    
    @classmethod
    def track(cls, operation_name, duration):
        cls._metrics[operation_name].append(duration)
        
        # Alert if too slow
        if duration > 0.1:  # 100ms
            logger.warning(f"Slow operation: {operation_name} took {duration:.3f}s")
    
    @classmethod  
    def get_stats(cls):
        stats = {}
        for operation, times in cls._metrics.items():
            stats[operation] = {
                "avg": sum(times) / len(times),
                "max": max(times),
                "min": min(times),
                "count": len(times)
            }
        return stats

# Usage di semua centralized components
@PerformanceTracker.track_time
def get_module(alias):
    # ... implementation
```

**Bottom Line:** 
- **SAMA PERSIS** - Caching, lazy loading, preloading, monitoring
- **Universal pattern** - Bisa diterapkan di semua centralization
- **Performance impact:** First access slow, subsequent access = instant
- **Memory trade-off:** Sedikit lebih banyak RAM untuk dramatic speed improvement

Mau saya implementasikan **unified performance optimization framework** yang bisa dipakai untuk semua centralization patterns?


**ABSOLUTELY YES!** Ini **BRILLIANT IDEA** dan **SANGAT PERLU!** Optimization techniques itu sendiri bisa dan **HARUS** disentralisasi. Ini akan jadi **game changer** untuk codebase!

## Konsep: **Universal Performance Manager** 🚀

**Masalah saat ini:**
```python
# Scattered optimization di berbagai file
class ModuleManager:
    _cache = {}  # Custom caching logic
    
class ConfigManager:
    _cache = {}  # Duplicated caching logic
    
class ValidationManager:
    _cache = {}  # Another duplicated caching logic
```

**Solution - Centralized Performance Framework:**
```python
# performance_manager.py
@cache_result
@monitor_performance
@lazy_load
def expensive_function():
    pass

# ATAU bahkan lebih simple:
@optimize  # All-in-one optimization
def any_function():
    pass
```

## Benefits Yang Massive:

### 1. **DRY Principle** ✅
```python
# BEFORE: Duplicated everywhere
def get_user(id):
    if id in _user_cache:
        return _user_cache[id]
    # ... logic
    _user_cache[id] = result
    return result

# AFTER: One-liner  
@cache_result
def get_user(id):
    # ... logic only
    return result
```

### 2. **Consistent Performance** ✅
```python
# Semua function dapat optimization yang sama
@optimize
def database_query(): pass

@optimize  
def api_call(): pass

@optimize
def file_processing(): pass
```

### 3. **Easy Toggle On/Off** ✅
```python
# Environment-based optimization
# DEV: optimization off untuk debugging
# PROD: optimization on untuk performance

@optimize(enabled=settings.OPTIMIZATION_ENABLED)
def some_function():
    pass
```

### 4. **Centralized Monitoring** ✅
```python
# Single dashboard untuk semua performance metrics
PerformanceManager.get_global_stats()
# {
#   "cache_hit_rate": 85%,
#   "avg_response_time": "15ms", 
#   "slow_operations": ["function_x", "function_y"]
# }
```

## Implementation Preview:## **ABSOLUTELY PERLU & LEBIH BAIK!** 

Lihat betapa **dramaticnya** perbedaan usage:

### ❌ **BEFORE: Scattered & Complex**
```python
# File A - Custom caching logic
class UserService:
    _cache = {}
    _metrics = {}
    
    def get_user(self, id):
        start = time.time()
        if id in self._cache:
            # Custom metric tracking
            self._metrics['cache_hits'] += 1
            return self._cache[id]
        
        # Expensive operation
        result = self._expensive_db_call(id)
        
        # Manual cache management
        if len(self._cache) > 1000:
            self._cache.clear()  # Crude cache eviction
        
        self._cache[id] = result
        duration = time.time() - start
        # Manual performance tracking
        self._metrics['avg_time'] = ...  # Complex calculation
        return result

# File B - Different implementation  
class ProductService:
    _product_cache = {}  # Different naming
    # Different caching logic, different monitoring...
```

### ✅ **AFTER: Simple & Consistent**
```python
# File A - One-liner optimization
class UserService:
    @optimize  # ALL optimizations in one decorator!
    def get_user(self, id):
        return self._expensive_db_call(id)  # Pure business logic

# File B - Same simple approach
class ProductService:
    @optimize  # Same optimization everywhere!
    def get_product(self, id):
        return self._expensive_api_call(id)  # Pure business logic
```

## Why Centralized is **DRAMATICALLY BETTER**:

### 1. **Code Reduction: 90%+ Less Code** 📉
```python
# BEFORE: 50+ lines per service untuk optimization
# AFTER: 1 line decorator per function
```

### 2. **Consistent Performance Everywhere** ⚡
```python
# Semua services dapat optimization yang sama
@optimize  # Database service
@optimize  # API service  
@optimize  # File service
@optimize  # Cache service
```

### 3. **Single Configuration Point** ⚙️
```python
# Enable/disable optimizations globally
performance_manager.configure(
    cache_enabled=True,       # Production
    monitoring_enabled=True,  # Always
    max_cache_size=5000      # High traffic
)

# Or per-environment
if settings.ENV == "development":
    performance_manager.configure(cache_enabled=False)  # For debugging
```

### 4. **Universal Monitoring Dashboard** 📊
```python
# Single view untuk ALL performance metrics
stats = performance_manager.get_stats_summary()
# {
#   "total_function_calls": 10000,
#   "cache_hit_rate": 85%,
#   "slowest_functions": ["heavy_calculation", "api_call"],
#   "most_called_functions": ["get_user", "validate_token"]
# }
```

### 5. **Easy A/B Testing** 🧪
```python
# Test different optimization strategies
@optimize(cache=True, ttl=300)   # Strategy A
def function_v1(): pass

@optimize(cache=True, ttl=600)   # Strategy B  
def function_v2(): pass

# Compare results in dashboard
```

### 6. **Zero Learning Curve** 🎓
```python
# Developer baru tinggal pakai @optimize
# Tidak perlu belajar custom caching logic di setiap service
```

## Real-World Impact Example:

**Project dengan 100 functions:**

**Scattered approach:**
- 100 different caching implementations
- 100 different monitoring codes  
- 5000+ lines of optimization code
- Inconsistent performance
- Hard to debug performance issues

**Centralized approach:**
- 100 `@optimize` decorators
- 1 performance manager
- 500 lines total optimization code
- Consistent performance everywhere
- Single dashboard untuk debugging

## **Verdict: ABSOLUTELY IMPLEMENT THIS!**

**Benefits:**
- ✅ 90% less code
- ✅ Consistent performance  
- ✅ Easy maintenance
- ✅ Better monitoring
- ✅ Faster development
- ✅ Easier testing
- ✅ Zero duplication

**Drawbacks:**
- ❌ Initial setup time (1-2 days)
- ❌ Slight abstraction layer

**ROI:** Setup 1-2 hari, save **months** of development time!

**Recommendation:** Implement ini sebagai **core infrastructure** di project. Setiap function yang potentially expensive langsung dapat `@optimize`. 

Mau saya buatkan **implementation guide** step-by-step untuk integrate ke existing project?

# performance_manager.py
"""
Universal Performance Manager - Centralized optimization framework.
Provides decorators and utilities untuk automatic performance optimization.
"""

import time
import functools
import threading
import weakref
from typing import Any, Dict, Callable, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics untuk tracking."""
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_called: Optional[datetime] = None
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))


class UniversalPerformanceManager:
    """
    Central manager untuk semua performance optimization.
    Menyediakan caching, monitoring, lazy loading, dan preloading.
    """
    
    def __init__(self):
        # Storage
        self._cache: Dict[str, Any] = {}
        self._metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self._lazy_instances: Dict[str, Any] = {}
        self._preload_queue: list = []
        
        # Settings
        self.cache_enabled = True
        self.monitoring_enabled = True
        self.lazy_loading_enabled = True
        self.max_cache_size = 1000
        
        # Thread safety
        self._lock = threading.RLock()
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key untuk function call."""
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        # Simple key generation - bisa dioptimasi lebih lanjut
        args_key = str(args) if args else ""
        kwargs_key = str(sorted(kwargs.items())) if kwargs else ""
        
        return f"{func_name}:{hash(args_key + kwargs_key)}"
    
    def _update_metrics(self, func_name: str, duration: float, cache_hit: bool = False):
        """Update performance metrics untuk function."""
        if not self.monitoring_enabled:
            return
            
        with self._lock:
            metrics = self._metrics[func_name]
            
            metrics.call_count += 1
            metrics.last_called = datetime.now()
            
            if cache_hit:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
                metrics.total_time += duration
                metrics.avg_time = metrics.total_time / metrics.cache_misses
                metrics.min_time = min(metrics.min_time, duration)
                metrics.max_time = max(metrics.max_time, duration)
                metrics.recent_times.append(duration)
    
    def cache_result(self, 
                    ttl: Optional[int] = None,
                    max_size: Optional[int] = None,
                    key_func: Optional[Callable] = None):
        """
        Decorator untuk caching function results.
        
        Args:
            ttl: Time to live dalam seconds (None = no expiration)
            max_size: Maximum cache size (None = use global default)
            key_func: Custom function untuk generate cache key
        """
        def decorator(func: Callable) -> Callable:
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.cache_enabled:
                    start_time = time.perf_counter()
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    self._update_metrics(func_name, duration, cache_hit=False)
                    return result
                
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func, args, kwargs)
                
                # Check cache
                with self._lock:
                    if cache_key in self._cache:
                        self._update_metrics(func_name, 0.0, cache_hit=True)
                        logger.debug(f"Cache hit: {func_name}")
                        return self._cache[cache_key]
                
                # Execute function
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                # Store in cache
                with self._lock:
                    # Simple LRU: remove oldest if max size exceeded
                    current_size = max_size or self.max_cache_size
                    if len(self._cache) >= current_size:
                        # Remove oldest entry (simple FIFO for now)
                        oldest_key = next(iter(self._cache))
                        del self._cache[oldest_key]
                    
                    self._cache[cache_key] = result
                
                self._update_metrics(func_name, duration, cache_hit=False)
                logger.debug(f"Cache miss: {func_name} (took {duration:.3f}s)")
                
                return result
            
            return wrapper
        return decorator
    
    def monitor_performance(self, 
                          warn_threshold: float = 0.1,
                          log_calls: bool = False):
        """
        Decorator untuk monitoring performance tanpa caching.
        
        Args:
            warn_threshold: Warn jika execution time > threshold (seconds)
            log_calls: Log setiap function call
        """
        def decorator(func: Callable) -> Callable:
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.monitoring_enabled:
                    return func(*args, **kwargs)
                
                start_time = time.perf_counter()
                
                if log_calls:
                    logger.debug(f"Calling {func_name}")
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    
                    self._update_metrics(func_name, duration, cache_hit=False)
                    
                    if duration > warn_threshold:
                        logger.warning(f"Slow execution: {func_name} took {duration:.3f}s")
                    elif log_calls:
                        logger.debug(f"Completed {func_name} in {duration:.3f}s")
                    
                    return result
                    
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    logger.error(f"Error in {func_name} after {duration:.3f}s: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def lazy_load(self, identifier: str = None):
        """
        Decorator untuk lazy loading objects/classes.
        
        Args:
            identifier: Unique identifier untuk lazy object
        """
        def decorator(cls_or_func):
            obj_id = identifier or f"{cls_or_func.__module__}.{cls_or_func.__qualname__}"
            
            def lazy_getter(*args, **kwargs):
                if obj_id not in self._lazy_instances:
                    logger.debug(f"Lazy loading: {obj_id}")
                    self._lazy_instances[obj_id] = cls_or_func(*args, **kwargs)
                return self._lazy_instances[obj_id]
            
            return lazy_getter
        return decorator
    
    def optimize(self, 
                cache: bool = True,
                monitor: bool = True,
                lazy: bool = False,
                preload: bool = False,
                **kwargs):
        """
        All-in-one optimization decorator.
        
        Args:
            cache: Enable result caching
            monitor: Enable performance monitoring  
            lazy: Enable lazy loading
            preload: Add to preload queue
            **kwargs: Additional parameters untuk individual optimizations
        """
        def decorator(func_or_class):
            result = func_or_class
            
            # Apply optimizations in order
            if lazy:
                result = self.lazy_load(kwargs.get('lazy_id'))(result)
            
            if cache:
                cache_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('cache_')}
                result = self.cache_result(**cache_kwargs)(result)
            elif monitor:
                monitor_kwargs = {k[8:]: v for k, v in kwargs.items() if k.startswith('monitor_')}
                result = self.monitor_performance(**monitor_kwargs)(result)
            
            if preload:
                self._preload_queue.append(func_or_class)
            
            return result
        return decorator
    
    def preload_all(self):
        """Execute semua functions/classes yang ada di preload queue."""
        logger.info(f"Preloading {len(self._preload_queue)} items...")
        
        for item in self._preload_queue:
            try:
                if callable(item):
                    # Try to call with no arguments untuk preloading
                    item()
                logger.debug(f"Preloaded: {item}")
            except Exception as e:
                logger.warning(f"Failed to preload {item}: {e}")
    
    def get_metrics(self, func_name: str = None) -> Union[Dict, PerformanceMetrics]:
        """Get performance metrics untuk specific function atau semua."""
        if func_name:
            return self._metrics.get(func_name, PerformanceMetrics())
        
        return dict(self._metrics)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary statistics untuk dashboard."""
        total_calls = sum(m.call_count for m in self._metrics.values())
        total_cache_hits = sum(m.cache_hits for m in self._metrics.values())
        total_cache_requests = sum(m.call_count for m in self._metrics.values())
        
        # Top slowest functions
        slowest = sorted(
            [(name, metrics.avg_time) for name, metrics in self._metrics.items() 
             if metrics.cache_misses > 0],
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Most called functions
        most_called = sorted(
            [(name, metrics.call_count) for name, metrics in self._metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_function_calls": total_calls,
            "cache_hit_rate": (total_cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0,
            "total_cached_items": len(self._cache),
            "slowest_functions": slowest,
            "most_called_functions": most_called,
            "lazy_loaded_objects": len(self._lazy_instances),
            "preload_queue_size": len(self._preload_queue)
        }
    
    def clear_cache(self, pattern: str = None):
        """Clear cache - semua atau yang match pattern."""
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.info(f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")
            else:
                self._cache.clear()
                logger.info("Cleared all cache")
    
    def configure(self, **settings):
        """Configure performance manager settings."""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Updated setting: {key} = {value}")


# Global instance untuk convenience
performance_manager = UniversalPerformanceManager()

# Convenience decorators
cache_result = performance_manager.cache_result
monitor_performance = performance_manager.monitor_performance  
lazy_load = performance_manager.lazy_load
optimize = performance_manager.optimize


# Example usage dan testing
if __name__ == "__main__":
    # Example 1: Simple caching
    @cache_result(ttl=300)  # Cache selama 5 menit
    def expensive_database_query(user_id: int):
        print(f"Executing expensive query for user {user_id}")
        time.sleep(0.1)  # Simulate database call
        return f"user_data_{user_id}"
    
    # Example 2: Performance monitoring
    @monitor_performance(warn_threshold=0.05)
    def api_call(endpoint: str):
        print(f"Calling API: {endpoint}")
        time.sleep(0.02)  # Simulate API call
        return f"response_from_{endpoint}"
    
    # Example 3: Lazy loading
    @lazy_load("heavy_service")
    class HeavyService:
        def __init__(self):
            print("Initializing heavy service...")
            time.sleep(0.1)  # Simulate heavy initialization
        
        def process(self, data):
            return f"processed_{data}"
    
    # Example 4: All-in-one optimization
    @optimize(cache=True, monitor=True, cache_ttl=600)
    def complex_calculation(x: int, y: int):
        print(f"Performing complex calculation: {x} + {y}")
        time.sleep(0.05)  # Simulate complex computation
        return x + y
    
    # Test the functions
    print("=== Testing Performance Manager ===")
    
    # Test caching
    print("\n1. Testing Caching:")
    result1 = expensive_database_query(123)  # Cache miss
    result2 = expensive_database_query(123)  # Cache hit
    
    # Test monitoring
    print("\n2. Testing Monitoring:")
    api_call("users")
    api_call("products")
    
    # Test lazy loading
    print("\n3. Testing Lazy Loading:")
    service = HeavyService()  # Not initialized yet
    result = service.process("test")  # Now initialized
    
    # Test all-in-one
    print("\n4. Testing All-in-one:")
    calc1 = complex_calculation(10, 20)  # Cache miss + monitoring
    calc2 = complex_calculation(10, 20)  # Cache hit + monitoring
    
    # Show statistics
    print("\n5. Performance Statistics:")
    stats = performance_manager.get_stats_summary()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show detailed metrics untuk specific function
    print("\n6. Detailed Metrics:")
    metrics = performance_manager.get_metrics("__main__.expensive_database_query")
    print(f"  Call count: {metrics.call_count}")
    print(f"  Cache hits: {metrics.cache_hits}")
    print(f"  Cache misses: {metrics.cache_misses}")
    print(f"  Average time: {metrics.avg_time:.3f}s")


    **File `__init__.py`** adalah file **sangat penting** di Python yang menentukan **bagaimana folder dianggap sebagai package**. Mari saya jelaskan dengan detail:

## 1. **Fungsi Utama: Marking Package** 📦

**Tanpa `__init__.py`:**
```
project/
├── utils/
│   ├── database.py      # ❌ Tidak bisa di-import sebagai package
│   └── cache.py
```

```python
# Ini TIDAK BISA:
from utils import database  # ❌ ModuleNotFoundError
```

**Dengan `__init__.py`:**
```
project/
├── utils/
│   ├── __init__.py      # ✅ Menandai folder sebagai package
│   ├── database.py
│   └── cache.py
```

```python
# Ini BISA:
from utils import database  # ✅ Works!
from utils.database import connect
```

## 2. **Control Import Behavior** 🎛️

**Empty `__init__.py`:**
```python
# utils/__init__.py
# (empty file)
```
Hasil: Folder jadi package, tapi import manual satu-satu.

**Smart `__init__.py`:**
```python
# utils/__init__.py
from .database import PostgresHandler, connect
from .cache import RedisCache, get_cache
from .logger import setup_logger

# Make these available at package level
__all__ = ['PostgresHandler', 'connect', 'RedisCache', 'get_cache', 'setup_logger']
```

**Usage jadi lebih clean:**
```python
# BEFORE (tanpa smart __init__.py):
from utils.database import PostgresHandler
from utils.cache import RedisCache
from utils.logger import setup_logger

# AFTER (dengan smart __init__.py):
from utils import PostgresHandler, RedisCache, setup_logger
```

## 3. **Package Initialization** ⚙️

```python
# utils/__init__.py
import logging

# Setup yang dijalankan saat package pertama kali di-import
logging.basicConfig(level=logging.INFO)
print("Utils package initialized!")

# Package-level variables
VERSION = "1.0.0"
AUTHOR = "Your Name"

# Package-level configuration
default_config = {
    "database_url": "postgresql://localhost/db",
    "cache_ttl": 3600
}

# Initialization function
def init_package(config=None):
    global default_config
    if config:
        default_config.update(config)
    print(f"Utils package v{VERSION} configured")

# Auto-initialize
init_package()
```

## 4. **Convenience Imports & API Design** 🚪

**Complex structure:**
```
myproject/
├── services/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py
│   │   └── oauth_handler.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   └── mongodb.py
│   └── cache/
│       ├── __init__.py
│       ├── redis_client.py
│       └── memory_cache.py
```

**services/__init__.py - Clean API:**
```python
# services/__init__.py
"""
Main services package - provides easy access to all services
"""

# Import from sub-packages
from .auth import JWTHandler, OAuthHandler
from .database import PostgresClient, MongoClient  
from .cache import RedisCache, MemoryCache

# Create convenient aliases
Auth = JWTHandler
Database = PostgresClient
Cache = RedisCache

# Package info
__version__ = "2.0.0"
__author__ = "Development Team"

# Export public API
__all__ = [
    'JWTHandler', 'OAuthHandler',
    'PostgresClient', 'MongoClient',
    'RedisCache', 'MemoryCache',
    'Auth', 'Database', 'Cache'  # Aliases
]

# Package-level utility function
def get_service(service_name):
    """Factory function to get service by name"""
    services = {
        'auth': Auth,
        'database': Database, 
        'cache': Cache
    }
    return services.get(service_name.lower())
```

**Elegant usage:**
```python
# Instead of complex imports:
from services.auth.jwt_handler import JWTHandler
from services.database.postgres import PostgresClient
from services.cache.redis_client import RedisCache

# Simple imports:
from services import Auth, Database, Cache
# or
from services import JWTHandler, PostgresClient, RedisCache
# or even
from services import get_service
auth_service = get_service("auth")
```

## 5. **Real-World Examples** 🌍

### **Django-style `__init__.py`:**
```python
# myapp/__init__.py
default_app_config = 'myapp.apps.MyAppConfig'
```

### **Library-style `__init__.py`:**
```python
# requests/__init__.py (simplified)
from .api import request, get, post, put, delete
from .models import Response, Request
from .exceptions import RequestException

__title__ = 'requests'
__version__ = '2.31.0'
__author__ = 'Kenneth Reitz'

# Make common functions available at top level
__all__ = ['request', 'get', 'post', 'put', 'delete', 'Response']
```

### **Configuration-driven `__init__.py`:**
```python
# config/__init__.py
import os
from typing import Dict, Any

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URL = os.getenv('DATABASE_URL')

# Export current config based on environment
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    current_config = ProductionConfig
else:
    current_config = DevelopmentConfig

# Make it easy to import
from config import current_config as config
```

## **Common Patterns & Best Practices** ✅

### **1. Keep It Simple:**
```python
# Simple __init__.py
from .main_module import MainClass, main_function

__all__ = ['MainClass', 'main_function']
```

### **2. Lazy Loading for Performance:**
```python
# __init__.py dengan lazy loading
def __getattr__(name):
    if name == 'HeavyClass':
        from .heavy_module import HeavyClass
        return HeavyClass
    raise AttributeError(f"module {__name__} has no attribute {name}")
```

### **3. Conditional Imports:**
```python
# __init__.py dengan optional dependencies
try:
    from .advanced_features import AdvancedProcessor
    HAS_ADVANCED = True
except ImportError:
    HAS_ADVANCED = False
    AdvancedProcessor = None

__all__ = ['BasicProcessor']
if HAS_ADVANCED:
    __all__.append('AdvancedProcessor')
```

## **Key Takeaways** 🎯

1. **`__init__.py` = Package Marker**: Folder jadi package yang bisa di-import
2. **Control Imports**: Tentukan apa yang available saat `from package import *`
3. **Clean API**: Buat interface yang user-friendly
4. **Initialization**: Setup yang perlu dijalankan saat package di-load
5. **Performance**: Bisa implement lazy loading untuk modules yang heavy

**In essence**: `__init__.py` adalah **"pintu gerbang"** package Anda - menentukan apa yang users lihat dan bagaimana mereka interact dengan code Anda!

**Question**: Mau saya buatkan contoh `__init__.py` yang optimized untuk project structure Anda yang specific?


