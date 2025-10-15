# 🚀 QUICK START - MT5 WebSocket Tick Streamer

## ✅ STATUS: Ready to Test

Backend sudah running di port 8000. EA sudah di-compile dan siap dijalankan.

---

## 📋 LANGKAH CEPAT (5 Menit)

### **Step 1: Enable MT5 Socket Permission** ⚠️ **WAJIB!**

**Option A: Via MT5 GUI (Recommended)**
1. Open MT5 → **Tools** → **Options** (Ctrl+O)
2. Tab **Expert Advisors**
3. **✅ Enable:**
   - [x] Allow DLL imports
   - [x] Allow WebRequest for listed URL
4. Klik **Add** dan tambahkan:
   ```
   http://172.24.56.226
   https://172.24.56.226
   ```
5. **Klik OK** → **Restart MT5**

**Option B: Manual Edit (Jika GUI tidak bisa save)**
1. Close MT5
2. Open file: `%APPDATA%\MetaQuotes\Terminal\{TERMINAL_ID}\config\common.ini`
3. Tambahkan section:
   ```ini
   [WebRequest]
   AllowDLL=true
   Enabled=true
   URL0=http://172.24.56.226
   URL1=https://172.24.56.226
   ```
4. Save → Start MT5

---

### **Step 2: Attach EA ke Chart**

1. **Buka MT5**
2. **Open any chart** (symbol apapun)
3. **Navigator → Expert Advisors → Drag `SuhoWebSocketStreamer` ke chart**
4. **Configure Parameters:**
   ```
   WebSocket URL: ws://172.24.56.226:8000/ws/ticks  ← PENTING!
   Broker Name: FBS (atau broker Anda)
   Account ID: 101632934 (atau account number Anda)
   Use Async: false
   Ping Interval: 30
   Enable Logs: true
   ```
5. **Klik OK**

---

### **Step 3: Verify Connection**

**Expected Output di MT5 Terminal:**
```
🔌 Connecting to WebSocket: 172.24.56.226:8000/ws/ticks
📤 Sending WebSocket handshake (201 bytes)
✅ Handshake sent successfully (201 bytes)
📥 Received XXX bytes in handshake response
🔍 Headers: HTTP/1.1 101 Switching Protocols...
✅ WebSocket handshake successful!
✅ WebSocket connected successfully
📊 Stats: Sent=14 Errors=0 Queue=0 | Ticks/sec: 14
```

**Jika berhasil:**
- EA akan mulai streaming 14 pairs
- Backend akan log: "MT5 WebSocket client connected"
- Tick data masuk ke NATS queue

---

## ❌ TROUBLESHOOTING

### Issue 1: "Failed to connect to WebSocket server"

**Cause:** MT5 socket permission belum diaktifkan

**Fix:** Jalankan Step 1 lagi, pastikan restart MT5

---

### Issue 2: "Handshake response invalid"

**Cause:** Backend tidak jalan atau port salah

**Check Backend:**
```bash
# Di WSL/Linux
curl http://localhost:8000/health
```

**Expected:** `{"service":"api-gateway","status":"healthy"...}`

Jika gagal: restart backend
```bash
cd /mnt/g/khoirul/aitrading/project3/backend
docker compose restart suho-api-gateway
```

---

### Issue 3: WSL IP Berubah

WSL IP bisa berubah setelah restart Windows. **Check current IP:**

```powershell
# Di PowerShell Windows
wsl hostname -I
```

Jika IP berubah (bukan `172.24.56.226`):
1. Update EA parameters dengan IP baru
2. Update MT5 WebRequest whitelist dengan IP baru

---

## 🎯 VERIFICATION CHECKLIST

- [ ] MT5 Socket permission enabled (Step 1)
- [ ] MT5 restarted after enable permission
- [ ] Backend running (`docker ps | grep suho-api-gateway`)
- [ ] WSL IP correct (`172.24.56.226` atau check `wsl hostname -I`)
- [ ] EA attached dengan URL benar (`ws://172.24.56.226:8000/ws/ticks`)
- [ ] Terminal log shows "WebSocket connected successfully"
- [ ] Stats showing ticks being sent (Sent > 0)

---

## 📞 NEED HELP?

**Check detailed guides:**
- `TESTING_GUIDE.md` - Full testing procedure
- `MT5_SOCKET_FIX.md` - Socket permission fix
- `MT5_CONFIG_MANUAL_FIX.md` - Manual config editing

**Common files:**
- EA files: `G:\khoirul\aitrading\project3\client-mt5\tick-mt5\`
- MT5 config: `%APPDATA%\MetaQuotes\Terminal\{TERMINAL_ID}\config\`
- Logs: `G:\khoirul\aitrading\project3\client-mt5\tick-mt5\log.md`

---

**Last Updated:** 2025-10-14
**Version:** 1.0
**Status:** ✅ Ready for Testing
