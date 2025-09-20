# Cloudflare WARP Setup Guide for Data Bridge Service

This guide shows how to set up Cloudflare WARP as an application-level proxy for the Dukascopy client, allowing you to bypass regional blocking without affecting your entire PC's internet connection.

## 🔑 Key Point: Application-Only Impact

**WARP will ONLY affect the Python application when configured as a proxy** - your PC's internet connection remains unchanged.

## 📋 Prerequisites

1. Windows 10/11 (WARP client required)
2. Cloudflare WARP key: `XrfV4782-W2X39u4G-h49e78ya`
3. Data bridge service running

## 🚀 Setup Steps

### Step 1: Install Cloudflare WARP

1. Download Cloudflare WARP from: https://1.1.1.1/
2. Install the application
3. **DO NOT** enable "WARP" mode in the GUI (this affects entire PC)

### Step 2: Configure WARP for Proxy Mode

1. **Open Command Prompt as Administrator**
2. **Navigate to WARP installation directory**:
   ```cmd
   cd "C:\Program Files\Cloudflare\Cloudflare WARP"
   ```

3. **Register your WARP key**:
   ```cmd
   warp-cli registration new
   warp-cli set-license XrfV4782-W2X39u4G-h49e78ya
   ```

4. **Enable proxy mode (APPLICATION-LEVEL ONLY)**:
   ```cmd
   warp-cli set-mode proxy
   warp-cli connect
   ```

5. **Verify proxy is running**:
   ```cmd
   warp-cli status
   ```
   You should see: `Status update: Connected` and `Mode: Proxy`

### Step 3: Configure Environment Variable

Add your WARP key to the data-bridge service environment:

```env
# In server_microservice/.env
CLOUDFLARE_WARP_KEY=XrfV4782-W2X39u4G-h49e78ya
```

### Step 4: Test WARP Integration

Run the test script to verify everything works:

```bash
cd server_microservice/services/data-bridge
python test_warp_integration.py
```

## 🔧 WARP Proxy Configuration

When WARP is in proxy mode, it exposes:
- **HTTP Proxy**: `http://127.0.0.1:40000`
- **SOCKS5 Proxy**: `socks5://127.0.0.1:40000`

The data bridge service will automatically detect and use the proxy when the WARP key is configured.

## 🌐 How It Works

1. **Application-Level**: Only HTTP requests from the Python application use WARP
2. **Selective Routing**: Dukascopy downloads route through Cloudflare's network
3. **Transparent Failover**: If WARP fails, automatically falls back to direct connection
4. **No System Impact**: Your browser, other apps, and Windows networking unchanged

## 📊 Verification Commands

### Check WARP Status
```cmd
warp-cli status
```

### Test Proxy Connectivity
```cmd
curl --proxy http://127.0.0.1:40000 http://httpbin.org/ip
```

### Check IP Address Through Proxy
```python
import requests
response = requests.get('http://httpbin.org/ip', proxies={'http': 'http://127.0.0.1:40000'})
print(response.json())
```

## 🛠️ Troubleshooting

### WARP Not Starting
```cmd
# Stop and restart WARP service
net stop "Cloudflare WARP"
net start "Cloudflare WARP"

# Or restart from CLI
warp-cli disconnect
warp-cli connect
```

### Proxy Not Accessible
```cmd
# Check if WARP is in proxy mode
warp-cli status

# Switch to proxy mode if needed
warp-cli set-mode proxy
warp-cli connect
```

### License Issues
```cmd
# Re-register license
warp-cli registration delete
warp-cli registration new
warp-cli set-license XrfV4782-W2X39u4G-h49e78ya
```

## 🔐 Security Notes

- WARP key is provided by user and stored in environment variables
- All traffic through WARP is encrypted
- No personal data is logged by Cloudflare in proxy mode
- Application-level proxy ensures minimal security surface

## 📈 Performance Benefits

- **Bypass Regional Blocks**: Access Dukascopy servers from any location
- **Improved Reliability**: Cloudflare's global network provides better routing
- **Automatic Failover**: Falls back to direct connection if WARP unavailable
- **No System Overhead**: Only affects specific application requests

## 🔄 Disable WARP

To disable WARP proxy (return to direct connection):

```cmd
warp-cli disconnect
```

Or remove the environment variable:
```env
# Remove or comment out
# CLOUDFLARE_WARP_KEY=XrfV4782-W2X39u4G-h49e78ya
```

## ⚠️ Important Notes

1. **Application-Only**: WARP proxy mode only affects the Python application, not your entire PC
2. **Fallback Mechanism**: If WARP fails, downloads automatically use direct connection
3. **No Always-On**: WARP is only used when explicitly configured in the application
4. **License Management**: Your WARP key enables the proxy functionality
5. **Performance**: WARP may improve or worsen speeds depending on your location

## 🎯 Expected Behavior

With WARP properly configured:

1. ✅ Dukascopy downloads use WARP proxy automatically
2. ✅ Your browser and other apps use direct connection
3. ✅ If WARP fails, downloads fall back to direct connection
4. ✅ No changes to Windows networking or system proxy settings
5. ✅ Regional blocks are bypassed transparently

This setup provides the best of both worlds: bypassing regional restrictions for the trading application while keeping the rest of your system unchanged.