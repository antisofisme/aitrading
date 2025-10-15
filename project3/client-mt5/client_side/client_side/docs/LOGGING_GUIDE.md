# MT5 Bridge Logging Guide

## 📋 **Log File Issue & Solution**

### 🔍 **Problem:**
- 2 log files created: `mt5_bridge.log` and `mt5_bridge_windows.log`
- Duplicate logging causing confusion
- Some log files may be corrupted or inaccessible

### 🔧 **Root Cause:**
Different scripts using different logging configurations:
- `hybrid_bridge.py` → `mt5_bridge.log` (using loguru)
- `run_bridge_windows.py` → `mt5_bridge_windows.log` (using standard logging)

### ✅ **Solution Applied:**
1. **Unified Logging**: All scripts now use `mt5_bridge.log`
2. **Consistent Format**: Same format across all scripts
3. **Cleanup Script**: Remove duplicate files

## 📄 **Single Log File: mt5_bridge.log**

All MT5 Bridge applications now log to: `mt5_bridge.log`

### 🧹 **Cleanup Duplicate Files**

**Windows:**
```bash
cleanup_logs.bat
```

**Linux/Python:**
```bash
python cleanup_logs.py
```

### 📊 **Log File Features:**
- **Rotation**: 5MB size limit
- **Retention**: Keep only current file
- **Format**: `YYYY-MM-DD HH:mm:ss | LEVEL | NAME | MESSAGE`
- **Encoding**: UTF-8
- **Mode**: Append

### 🔍 **Log Monitoring:**

**View live logs:**
```bash
tail -f mt5_bridge.log
```

**Filter by level:**
```bash
grep "ERROR" mt5_bridge.log
grep "SUCCESS" mt5_bridge.log
grep "WARNING" mt5_bridge.log
```

**Filter by component:**
```bash
grep "HybridBridge" mt5_bridge.log
grep "Redpanda" mt5_bridge.log
grep "WebSocket" mt5_bridge.log
```

## 🔧 **Log Levels:**
- **INFO**: General information
- **SUCCESS**: Successful operations
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **DEBUG**: Debug information

## 📝 **Log Entries Examples:**

```
2025-07-16 23:58:09 | INFO     | HybridBridge | 🚀 Starting Hybrid MT5 Bridge Application
2025-07-16 23:58:09 | SUCCESS  | HybridBridge | ✅ Successfully connected to MT5!
2025-07-16 23:58:09 | INFO     | HybridBridge | 📊 Server: FBS-Demo
2025-07-16 23:58:09 | INFO     | HybridBridge | 💰 Balance: 1005.94 USD
2025-07-16 23:58:09 | SUCCESS  | HybridBridge | ✅ Connected to Backend WebSocket
```

## 🎯 **Best Practices:**
1. **Single Log File**: Use only `mt5_bridge.log`
2. **Regular Cleanup**: Run cleanup script monthly
3. **Monitor Size**: Check log file size regularly
4. **Backup Important**: Save important logs before cleanup

## 🚨 **If Log File is Corrupted:**
1. Stop MT5 Bridge
2. Run `cleanup_logs.bat` (Windows) or `cleanup_logs.py` (Linux)
3. Restart MT5 Bridge
4. New clean log file will be created

## 📞 **Support:**
If logging issues persist, check:
- File permissions
- Disk space
- Antivirus blocking
- Running as administrator (Windows)