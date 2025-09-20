# MQL5 Economic Calendar Batch Scraper

## 🎯 **Overview**

Enhanced MQL5 Economic Calendar scraper dengan:
- ✅ **Configurable historical range** via `.env` variables
- ✅ **Batch processing** untuk efficient large-scale downloads
- ✅ **Empty date detection** dan automatic skipping
- ✅ **Weekend filtering** berdasarkan forex trading calendar
- ✅ **Retry mechanism** dengan configurable attempts
- ✅ **Trading signals** generation untuk economic events

## ⚙️ **Environment Configuration**

### **Required .env Variables:**

```bash
# MQL5 Economic Calendar Historical Download Configuration
MQL5_HISTORICAL_DAYS_BACK=30          # Berapa hari ke belakang untuk download
MQL5_BATCH_SIZE=7                     # Jumlah tanggal per batch
MQL5_BATCH_DELAY_SECONDS=5            # Delay antar batch (rate limiting)
MQL5_SKIP_EMPTY_DATES=true            # Skip tanggal tanpa events
MQL5_MAX_RETRIES_PER_DATE=3           # Max retry per tanggal gagal
MQL5_BROWSER_TIMEOUT_SECONDS=30       # Browser timeout

# Weekend Economic Events Handling
MQL5_INCLUDE_WEEKEND_EVENTS=false     # Include emergency weekend events
MQL5_WEEKEND_EVENT_TYPES=emergency,central_bank,geopolitical  # Types to look for on weekends
```

### **Configuration Examples:**

```bash
# Conservative (small range, slow processing)
MQL5_HISTORICAL_DAYS_BACK=7
MQL5_BATCH_SIZE=3
MQL5_BATCH_DELAY_SECONDS=10

# Aggressive (large range, fast processing)  
MQL5_HISTORICAL_DAYS_BACK=90
MQL5_BATCH_SIZE=14
MQL5_BATCH_DELAY_SECONDS=2

# Production (balanced)
MQL5_HISTORICAL_DAYS_BACK=30
MQL5_BATCH_SIZE=7
MQL5_BATCH_DELAY_SECONDS=5
```

## 🚀 **Usage Examples**

### **1. Single Date Download**

```python
from data_sources.mql5_scraper import get_mql5_widget_events

# Current date
results = await get_mql5_widget_events()

# Specific historical date
results = await get_mql5_widget_events(target_date="2024-08-09")
```

### **2. Batch Historical Download**

```python
from data_sources.mql5_scraper import get_mql5_batch_historical_events

# Using .env configuration (MQL5_HISTORICAL_DAYS_BACK)
results = await get_mql5_batch_historical_events()

# Custom range
results = await get_mql5_batch_historical_events(days_back=60)

# Full batch mode dengan control
results = await get_mql5_widget_events(batch_mode=True, days_back=30)
```

### **3. Command Line Testing**

```bash
# Test current date
python src/data_sources/mql5_scraper.py

# Test specific historical date
python src/data_sources/mql5_scraper.py 2024-08-09

# Test batch mode (default range from .env)
python src/data_sources/mql5_scraper.py --batch

# Test batch mode (custom range)
python src/data_sources/mql5_scraper.py --batch 14
```

## 📊 **Batch Processing Features**

### **Intelligent Weekend Handling**
```python
# Default: Skip all weekend dates (forex market closed)
# Optional: Include emergency/critical events only
# MQL5_INCLUDE_WEEKEND_EVENTS=false (default)
# MQL5_INCLUDE_WEEKEND_EVENTS=true (emergency events only)
```

### **Weekend Event Categories:**
- **Emergency Events**: Crisis response, emergency meetings, breaking news
- **Central Bank Events**: Fed emergency decisions, ECB crisis response  
- **Geopolitical Events**: G7/G20 summits, emergency elections, treaties

### **Empty Date Detection**
```python
# Detects dates with no economic events
# Configurable: skip atau include empty dates
# MQL5_SKIP_EMPTY_DATES=true/false
```

### **Smart Retry Mechanism**
```python
# Per-date retry dengan exponential backoff
# MQL5_MAX_RETRIES_PER_DATE=3
# 2 seconds delay between retries
```

### **Rate Limiting Protection**
```python
# Delay antar batch: MQL5_BATCH_DELAY_SECONDS
# Delay antar date: 1 second (fixed)
# Browser timeout: MQL5_BROWSER_TIMEOUT_SECONDS
```

## 📈 **Response Structure**

### **Single Date Response:**
```json
{
  "status": "success",
  "source": "MQL5 Widget", 
  "method": "widget_browser_automation",
  "events": [...],
  "historical_data_support": {
    "target_date": "2024-08-09",
    "date_filtering": "supported",
    "historical_range": "configurable via MQL5_HISTORICAL_DAYS_BACK",
    "date_format": "YYYY-MM-DD",
    "batch_processing": "available via batch_mode=True"
  },
  "summary": {
    "total_events": 15,
    "high_impact": 5,
    "trading_relevant": 8
  }
}
```

### **Batch Processing Response:**
```json
{
  "status": "completed",
  "source": "MQL5 Widget Batch Scraping",
  "method": "batch_browser_automation", 
  "configuration": {
    "days_back": 30,
    "batch_size": 7,
    "batch_delay_seconds": 5,
    "skip_empty_dates": true,
    "max_retries_per_date": 3,
    "include_weekend_events": true,
    "weekend_event_types": ["emergency", "central_bank", "geopolitical"]
  },
  "date_range": {
    "start_date": "2024-07-11",
    "end_date": "2024-08-10",
    "total_dates_attempted": 30,
    "successful_dates": 22,
    "empty_dates": 6,
    "failed_dates": 2
  },
  "events": [...], 
  "summary": {
    "total_events": 340,
    "high_impact": 95,
    "medium_impact": 145,
    "low_impact": 100,
    "weekend_events": 12,
    "regular_events": 328,
    "success_rate": 0.73
  },
  "processing_details": {
    "successful_dates": ["2024-08-09", "2024-08-08", ...],
    "empty_dates": "Skipped 6 empty dates", 
    "failed_dates": ["2024-07-15", "2024-07-20"],
    "total_batches": 5
  }
}
```

## 📅 **Weekend Economic Events Handling**

### **Overview:**
Most economic calendars tidak ada events Sabtu-Minggu karena:
- **Forex market** tutup weekend (24/5 operation)
- **Stock exchanges** tutup weekend 
- **Government agencies** tidak release data weekend

### **Exception: Emergency Events**
Namun kadang-kadang ada **emergency events** di weekend:
- **Central bank emergency meetings** (crisis response)
- **G7/G20 emergency summits** 
- **Geopolitical announcements** (elections, treaties)
- **Breaking economic news** (trade wars, sanctions)

### **Configuration Options:**

```bash
# Option 1: Skip all weekends (Default - Recommended untuk forex)
MQL5_INCLUDE_WEEKEND_EVENTS=false

# Option 2: Include emergency events only  
MQL5_INCLUDE_WEEKEND_EVENTS=true
MQL5_WEEKEND_EVENT_TYPES=emergency,central_bank,geopolitical

# Option 3: Include only central bank emergencies
MQL5_INCLUDE_WEEKEND_EVENTS=true
MQL5_WEEKEND_EVENT_TYPES=central_bank

# Option 4: Include all types
MQL5_INCLUDE_WEEKEND_EVENTS=true
MQL5_WEEKEND_EVENT_TYPES=emergency,central_bank,geopolitical
```

### **Weekend Event Detection:**

```python
# Emergency Keywords: 
"emergency", "urgent", "crisis", "breaking", "unscheduled"

# Central Bank Keywords:
"fed", "ecb", "boe", "boj", "central bank", "interest rate decision"

# Geopolitical Keywords: 
"election", "referendum", "summit", "g7", "g20", "meeting", "treaty"

# High Importance:
Any event with importance="HIGH" on weekends is considered emergency
```

### **Weekend Events in Response:**

```json
{
  "event_name": "Emergency Fed Meeting",
  "importance": "HIGH",
  "weekend_event_category": "emergency", 
  "weekend_special_processing": true,
  "currency_impact": "Bullish",
  "trading_signals": ["Emergency USD volatility expected"]
}
```

### **Use Cases:**

**Forex Trading (Recommended):**
```bash
MQL5_INCLUDE_WEEKEND_EVENTS=false  # Skip all weekends
```

**News/Research Platform:**
```bash  
MQL5_INCLUDE_WEEKEND_EVENTS=true   # Include emergency events
MQL5_WEEKEND_EVENT_TYPES=emergency,central_bank,geopolitical
```

**Central Bank Monitoring:**
```bash
MQL5_INCLUDE_WEEKEND_EVENTS=true   # Only central bank events
MQL5_WEEKEND_EVENT_TYPES=central_bank
```

## 🎯 **Trading Signals Integration**

### **Enhanced Event Processing:**
```python
# Each event includes:
{
  "event_name": "Non-Farm Payrolls (NFP)",
  "country": "United States",
  "currency": "USD", 
  "importance": "HIGH",
  "market_impact": "High",
  "trading_relevance_score": 0.85,
  "trading_signals": [
    "Bullish signal for USD",
    "High volatility expected in USD markets"
  ],
  "deviation_from_forecast": 15.2,
  "currency_impact": "Bullish"
}
```

## 🧪 **Testing**

### **Comprehensive Test Suite:**
```bash
# Run full test suite
python test_mql5_batch_scraper.py

# Tests include:
# - Environment configuration
# - Batch processing (small range)
# - Empty date detection  
# - Single vs batch comparison
```

### **Manual Testing:**
```bash
# Quick test dengan 7 hari
python -c "
import asyncio
from src.data_sources.mql5_scraper import get_mql5_batch_historical_events
result = asyncio.run(get_mql5_batch_historical_events(7))
print(f'Events: {len(result.get(\"events\", []))}')
print(f'Success rate: {result.get(\"summary\", {}).get(\"success_rate\", 0)*100:.1f}%')
"
```

## ⚡ **Performance Optimization**

### **Recommended Settings per Use Case:**

**Development/Testing:**
```bash
MQL5_HISTORICAL_DAYS_BACK=7
MQL5_BATCH_SIZE=3
MQL5_BATCH_DELAY_SECONDS=10
MQL5_SKIP_EMPTY_DATES=false  # To see all dates
```

**Production (Daily Updates):**
```bash
MQL5_HISTORICAL_DAYS_BACK=1
MQL5_BATCH_SIZE=1
MQL5_BATCH_DELAY_SECONDS=0
MQL5_SKIP_EMPTY_DATES=true
```

**Historical Backfill:**
```bash
MQL5_HISTORICAL_DAYS_BACK=90
MQL5_BATCH_SIZE=10
MQL5_BATCH_DELAY_SECONDS=3
MQL5_SKIP_EMPTY_DATES=true
```

## 🔍 **Monitoring & Debugging**

### **Log Analysis:**
- ✅ Successful dates logged with event counts
- 📭 Empty dates logged and handled according to config
- ❌ Failed dates logged with error details
- 📊 Batch progress tracking
- ⏱️ Performance timing per batch

### **Success Rate Monitoring:**
```python
# Monitor success rate dari response
success_rate = results['summary']['success_rate']
if success_rate < 0.7:
    # Consider adjusting batch size atau retry settings
    pass
```

## 🚦 **Error Handling**

### **Common Issues:**
1. **Browser timeout** → Increase `MQL5_BROWSER_TIMEOUT_SECONDS`
2. **Rate limiting** → Increase `MQL5_BATCH_DELAY_SECONDS`
3. **Low success rate** → Increase `MQL5_MAX_RETRIES_PER_DATE`
4. **Memory issues** → Decrease `MQL5_BATCH_SIZE`

### **Automatic Recovery:**
- Per-date retry dengan backoff
- Weekend automatic skipping
- Empty date handling
- Graceful browser cleanup

## 🎉 **Ready untuk Production!**

Fitur ini siap untuk:
- ✅ Daily economic calendar updates
- ✅ Historical data backfilling
- ✅ Automated batch processing
- ✅ Trading signal generation
- ✅ Database integration via data-bridge service