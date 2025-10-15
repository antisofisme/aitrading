# MT5 WebSocket Connection Fix

## Problem
```
❌ Failed to connect to localhost:8001
```

## Root Cause
**MT5 blocks all network socket connections by default!**

You MUST explicitly enable socket access in MT5 settings.

---

## ✅ SOLUTION: Enable MT5 Socket Permissions

### Step 1: Open MT5 Options
1. Open MetaTrader 5
2. Go to **Tools** → **Options** (or press `Ctrl + O`)

### Step 2: Enable Socket Access
1. Click **Expert Advisors** tab
2. Find section: **Allow DLL imports**
3. **✅ Check:**
   - [x] **Allow DLL imports**
   - [x] **Allow WebRequest for listed URL**

### Step 3: Add Allowed Hosts
In the "Allow WebRequest" section, click **Add** and add:

```
http://localhost
https://localhost
http://172.24.56.226
https://172.24.56.226
```

**IMPORTANT:** MT5 checks both HTTP and HTTPS, add both even though we use WebSocket!

### Step 4: Restart MT5
1. Close MT5 completely
2. Reopen MT5
3. Re-attach the EA to chart

---

## Alternative: Run via Terminal (Admin)

If above doesn't work, MT5 might need elevated privileges:

1. Close MT5
2. Right-click **MT5 Terminal icon**
3. Select **Run as Administrator**
4. Try connecting again

---

## Test Connection

After enabling permissions:

1. Attach **SuhoWebSocketStreamer** to any chart
2. Parameters:
   ```
   WebSocket URL: ws://localhost:8001/ws/ticks
   Broker Name: FBS
   Account ID: 101632934
   Use Async: false
   Ping Interval: 30
   Enable Logs: true
   ```

3. Expected output:
   ```
   🔌 Connecting to WebSocket: localhost:8001/ws/ticks
   ✅ WebSocket connected successfully
   📊 Stats: Sent=14 Errors=0 Queue=0 | Ticks/sec: 14
   ```

---

## Common Issues

### Issue 1: "Failed to create socket"
**Solution:** Enable **Allow DLL imports** in MT5 Options

### Issue 2: "Connection refused"
**Solution:** Check if API Gateway is running:
```bash
docker ps | grep api-gateway
```

### Issue 3: "Permission denied"
**Solution:** Run MT5 as Administrator

---

## Why This Happens

MT5 security model:
- **Default:** All network access BLOCKED
- **Reason:** Prevent malicious EAs from stealing data or executing unauthorized trades
- **Solution:** Explicitly whitelist hosts in MT5 Options

WebSocket uses raw TCP sockets (`SocketCreate()`, `SocketConnect()`), which require DLL-level permissions even though no actual DLL is used.

---

## Verification Steps

1. ✅ Docker port exposed: `0.0.0.0:8001`
2. ✅ API Gateway running: `suho-api-gateway`
3. ✅ WebSocket endpoint: `/ws/ticks`
4. ✅ URL parsing: `localhost:8001` → correct
5. ❌ **Socket connect: BLOCKED by MT5**

Fix step 5 by enabling permissions above!

---

**Last Updated:** 2025-10-14
**Status:** Permissions issue identified
