# 📊 Batch Size Guide untuk Koneksi Terbatas

## 🎯 Rekomendasi Berdasarkan Test Connection Anda

Berdasarkan hasil test, koneksi Anda mengalami **"Connection reset by peer"** - ini menunjukkan **koneksi tidak stabil** atau ada **pembatasan jaringan**.

## 📋 Rekomendasi ULTRA CONSERVATIVE

### 🐌 Untuk Koneksi Bermasalah (Seperti Anda)

```python
# Pengaturan optimal untuk koneksi tidak stabil
BATCH_SIZE = 1 jam (1 file)
CONCURRENT = 1 (satu-satu saja)
DELAY = 5 detik (delay panjang)
TIMEOUT = 3 menit (timeout panjang)
RETRY = 1 kali (jangan terlalu banyak retry)
```

### 🕐 Waktu Optimal Download

1. **Terbaik**: 02:00-05:00 WIB (traffic internet minimal)
2. **Baik**: 22:00-01:00 WIB (malam hari)
3. **Hindari**: 07:00-09:00, 18:00-22:00 WIB (peak hours)

## 📈 Progressive Strategy (Naik Bertahap)

### Week 1: Testing Phase
- **Batch**: 1 jam (1 file)
- **Frequency**: Manual, saat koneksi stabil
- **Target**: Success rate > 70%

### Week 2: Scaling Phase (jika Week 1 berhasil)
- **Batch**: 3 jam (3 files)
- **Frequency**: 2x sehari (pagi & malam)
- **Target**: Success rate > 80%

### Week 3: Stable Phase (jika Week 2 berhasil)
- **Batch**: 6 jam (6 files)  
- **Frequency**: 1x sehari
- **Target**: Success rate > 85%

### Week 4+: Optimal Phase (jika Week 3 berhasil)
- **Batch**: 12-24 jam (12-24 files)
- **Frequency**: Daily/Weekly batch
- **Target**: Success rate > 90%

## 🛠️ Troubleshooting Connection Issues

### 1. "Connection reset by peer" 
**Penyebab**: Server menolak koneksi
**Solusi**:
- Gunakan VPN (try NordVPN, ExpressVPN)
- Ganti DNS ke 8.8.8.8 atau 1.1.1.1
- Coba dari jaringan berbeda (mobile hotspot)
- Download saat off-peak hours

### 2. Timeout Errors
**Penyebab**: Koneksi terlalu lambat
**Solusi**:
- Increase timeout ke 300 detik (5 menit)
- Reduce concurrent ke 1
- Increase delay ke 10 detik
- Close aplikasi lain yang pakai internet

### 3. Slow Download Speed
**Penyebab**: Bandwidth terbatas
**Solusi**:
- Download saat malam hari
- Pause streaming/video calls
- Use ethernet cable instead of WiFi
- Contact ISP untuk check line quality

## 🔧 Kode Implementation untuk Koneksi Anda

```python
# Gunakan pengaturan ini untuk koneksi tidak stabil
async def download_for_slow_connection():
    downloader = DataBridgeDukascopyDownloader()
    
    # Override pengaturan default untuk koneksi lambat
    downloader.session_timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
    downloader.max_concurrent_downloads = 1  # Satu per satu
    downloader.retry_attempts = 1  # Minimal retry
    downloader.delay_between_requests = 10.0  # 10 detik delay
    
    # Download 1 jam data saja
    result = await downloader.download_small_batch(
        pair="EURUSD",
        hours_back=1  # Hanya 1 jam
    )
    
    return result

# Jalankan saat off-peak hours
if datetime.now().hour in [2, 3, 4, 23, 0, 1]:
    result = asyncio.run(download_for_slow_connection())
```

## 📊 Expected Performance untuk Batch Sizes

### 1 Hour Batch (1 file)
- **Files**: 1
- **Size**: ~0.5-2 MB
- **Time**: 2-5 minutes
- **Success Rate**: 70-90%
- **Best for**: Testing connection

### 3 Hours Batch (3 files)  
- **Files**: 3
- **Size**: ~1.5-6 MB
- **Time**: 5-15 minutes
- **Success Rate**: 60-80%
- **Best for**: Small regular updates

### 6 Hours Batch (6 files)
- **Files**: 6
- **Size**: ~3-12 MB
- **Time**: 10-30 minutes
- **Success Rate**: 50-70%
- **Best for**: Daily collection

### 24 Hours Batch (24 files)
- **Files**: 24
- **Size**: ~12-48 MB
- **Time**: 40-120 minutes
- **Success Rate**: 30-50%
- **Best for**: Weekly bulk download

## ⚠️ Red Flags - Scale Back If You See:

- Success rate < 70%
- Individual file taking > 60 seconds
- Frequent "Connection reset" errors
- Download taking > 2x expected time
- Multiple timeout errors

## 💡 Quick Wins untuk Connection Issues

1. **Use Different Network**
   ```bash
   # Test dari mobile hotspot
   # Jika berhasil = masalah di WiFi/ISP
   ```

2. **Change DNS**
   ```bash
   # Windows Command Prompt (as Administrator):
   netsh interface ip set dns "Wi-Fi" static 8.8.8.8
   netsh interface ip add dns "Wi-Fi" 8.8.4.4 index=2
   ```

3. **Use VPN**
   ```bash
   # Try VPN dengan server di Singapura/Hong Kong
   # Dukascopy servers might have regional restrictions
   ```

4. **Schedule Downloads**
   ```python
   # Download otomatis saat off-peak
   import schedule
   schedule.every().day.at("03:00").do(download_small_batch)
   ```

## 📅 Weekly Schedule Recommendation

### Monday-Friday (Market Days)
- **03:00**: Download 1-3 hours data
- **15:00**: Check results, retry failures  
- **23:00**: Download 1-3 hours data (if morning failed)

### Saturday-Sunday (Market Closed)
- **Process downloaded data**
- **Plan next week's downloads**
- **Test connection improvements**

## 🎯 Success Metrics

Track these untuk optimize performance:
- **Success Rate**: Target > 80%
- **Average Speed**: Target > 50 KB/s per file
- **Error Rate**: Target < 20%
- **Consistency**: Same performance day-to-day

Remember: **Better to download 1 file successfully than fail on 10 files!**