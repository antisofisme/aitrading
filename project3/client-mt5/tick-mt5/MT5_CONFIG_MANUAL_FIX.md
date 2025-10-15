# MT5 Config Manual Fix - WebRequest Whitelist

## Problem
MT5 Options tidak bisa save settings karena permission issue.

## Solution: Edit Config File Manual

### Step 1: Find MT5 Data Folder

1. Open MT5
2. Go to: **File** → **Open Data Folder** (atau tekan `Ctrl+Shift+D`)
3. Folder akan terbuka di Windows Explorer
4. Close MT5

### Step 2: Edit Config File

Navigate to config folder dan edit file:

**Path:**
```
{MT5_DATA_FOLDER}\config\common.ini
```

Example full path:
```
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\{TERMINAL_ID}\config\common.ini
```

### Step 3: Add WebRequest Whitelist

Open `common.ini` with Notepad and find section `[WebRequest]`.

If section doesn't exist, add it at the end:

```ini
[WebRequest]
AllowDLL=true
Enabled=true
URL0=http://localhost
URL1=https://localhost
URL2=http://127.0.0.1
URL3=https://127.0.0.1
URL4=http://172.24.56.226
URL5=https://172.24.56.226
```

**IMPORTANT:**
- `AllowDLL=true` is critical for socket access!
- Add both `localhost` and `127.0.0.1`
- Add both HTTP and HTTPS variants

### Step 4: Save and Restart

1. Save `common.ini`
2. Make sure file is **NOT read-only** (Right-click → Properties → uncheck Read-only)
3. Start MT5
4. Attach EA and test

---

## Alternative: Disable UAC (Temporary)

If Windows UAC is blocking:

1. Press **Win + R**
2. Type: `msconfig`
3. Go to **Tools** tab
4. Select **Change UAC Settings**
5. Drag slider to **Never notify**
6. Restart computer
7. Try MT5 options again
8. **Remember to re-enable UAC after!**

---

## Verification

After config change, test by attaching EA:

```
Expected:
🔌 Connecting to WebSocket: localhost:8001/ws/ticks
✅ WebSocket connected successfully

If still fails:
❌ Failed to connect to localhost:8001
→ Check if AllowDLL=true in common.ini
→ Check if MT5 running as Administrator
```

---

## Why This Happens

Windows User Account Control (UAC) blocks MT5 from writing to config files in AppData folder when running as regular user.

**Solutions ranked by preference:**
1. ✅ **Run MT5 as Administrator** (simplest)
2. ✅ **Manual edit common.ini** (if admin not available)
3. ⚠️ Disable UAC (not recommended for production)

---

**Last Updated:** 2025-10-14
