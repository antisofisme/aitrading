# Database Backup & Restore - Cloudflare R2

Simple manual backup solution for PostgreSQL (TimescaleDB) and ClickHouse databases using Cloudflare R2 object storage.

## 📋 Features

- ✅ Backup PostgreSQL (TimescaleDB) and ClickHouse
- ✅ Upload to Cloudflare R2 (S3-compatible storage)
- ✅ Automatic cleanup (local: 7 days, R2: 30 days)
- ✅ Manual restore with date selection
- ✅ Credentials stored securely in `.env` file

## 🚀 Quick Start

### 1. Setup Credentials

```bash
# Copy template and edit with your R2 credentials
cd /mnt/g/khoirul/aitrading/project3/backend/scripts/backup-database
cp .env.backup .env

# Edit .env with your actual credentials
nano .env
```

### 2. Make Scripts Executable

```bash
chmod +x backup-to-r2.sh restore-from-r2.sh
```

### 3. Run Manual Backup

```bash
# Run backup (PostgreSQL + ClickHouse → R2)
./backup-to-r2.sh
```

### 4. Restore from Backup

```bash
# Restore latest backup
./restore-from-r2.sh

# Or restore specific date
./restore-from-r2.sh 20250114_120000
```

---

## 📖 Detailed Setup

### Prerequisites

1. **Cloudflare R2 Account** (free tier: 10 GB storage)
2. **AWS CLI** installed for S3-compatible access
3. **Docker & Docker Compose** running

### Install AWS CLI (if not installed)

```bash
# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

### Get Cloudflare R2 Credentials

1. Login to Cloudflare Dashboard: https://dash.cloudflare.com
2. Go to **R2 Object Storage**
3. Create bucket: `suho-trading-backups`
4. Go to **Manage R2 API Tokens** → **Create API Token**
5. Copy these values to `.env` file:
   - Account ID
   - Access Key ID
   - Secret Access Key

---

## 📂 File Structure

```
scripts/backup-database/
├── .env.backup          # Template (DO NOT EDIT)
├── .env                 # Your actual credentials (gitignored)
├── backup-to-r2.sh      # Manual backup script
├── restore-from-r2.sh   # Manual restore script
└── README.md            # This file
```

---

## ⚙️ Configuration

Edit `.env` file to customize:

```bash
# R2 Configuration
R2_BUCKET=suho-trading-backups
R2_ACCOUNT_ID=your-account-id
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com

# R2 API Credentials
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key

# Retention Policy
LOCAL_RETENTION_DAYS=7   # Keep local backups for 7 days
R2_RETENTION_DAYS=30     # Keep R2 backups for 30 days
```

---

## 🔧 Usage Examples

### Backup Current Databases

```bash
./backup-to-r2.sh
```

**Output:**
```
🔄 Starting backup at Mon Jan 14 12:00:00 UTC 2025
📦 Backing up PostgreSQL (TimescaleDB)...
✅ PostgreSQL backup: 1.2G
📦 Backing up ClickHouse...
✅ ClickHouse backup: 450M
☁️  Uploading to Cloudflare R2...
  ✅ Uploaded: postgresql_20250114_120000.sql.gz
  ✅ Uploaded: clickhouse_20250114_120000.zip
✅ Backup completed successfully
```

### Restore Latest Backup

```bash
./restore-from-r2.sh
```

**Interactive prompt:**
```
📋 Listing available backups...
  2025/01/12 postgresql_20250112_060000.sql.gz
  2025/01/13 postgresql_20250113_120000.sql.gz
  2025/01/14 postgresql_20250114_120000.sql.gz

Enter backup date (YYYYMMDD_HHMMSS) or press Enter for latest:
```

### Restore Specific Date

```bash
./restore-from-r2.sh 20250114_120000
```

---

## 📊 Cloudflare R2 Pricing

**Free Tier (per month):**
- ✅ 10 GB storage
- ✅ 1 million Class A operations (uploads)
- ✅ 10 million Class B operations (downloads)
- ✅ **FREE egress bandwidth** (unlimited!)

**Paid Tier (after free tier):**
- Storage: **$0.015/GB/month** (~Rp 240/GB)
- Class A ops: $4.50 per million
- Class B ops: $0.36 per million
- Egress: **FREE** (AWS S3 charges $90/TB!)

**Example Cost for 50GB Backup:**
- 50 GB × $0.015 = **$0.75/month** (~Rp 12.000)
- Much cheaper than AWS S3 or Google Cloud Storage!

---

## 🛡️ Backup Strategy

### What Gets Backed Up

1. **PostgreSQL (TimescaleDB)** - All trading data:
   - Raw tick data
   - Aggregated OHLCV
   - Technical indicators
   - Trading signals

2. **ClickHouse** - Analytics data:
   - Time-series aggregations
   - Performance metrics
   - Query cache

### What DOESN'T Get Backed Up

- **DragonflyDB (Redis)** - Temporary cache, can be rebuilt
- **NATS/Kafka messages** - Streaming data, not persistent
- **Docker volumes** - Only database data backed up

### Retention Policy

- **Local backups**: 7 days (saves disk space)
- **R2 backups**: 30 days (long-term archive)
- **Cleanup**: Automatic, runs after each backup

---

## 🚨 When to Use

### After Docker Reinstall (Like Your Case)

```bash
# 1. Fresh Docker install
docker --version

# 2. Pull images and deploy
cd /mnt/g/khoirul/aitrading/project3/backend
docker compose up -d

# 3. Restore latest backup
cd scripts/backup-database
./restore-from-r2.sh

# 4. Verify services
docker compose ps
```

### Before Major Changes

```bash
# Backup before updating Docker Compose
./backup-to-r2.sh

# Update docker-compose.yml
# ...

# If something breaks, restore
./restore-from-r2.sh
```

### Regular Maintenance

```bash
# Weekly manual backup (optional)
./backup-to-r2.sh

# Or setup cron job:
# 0 */6 * * * /path/to/backup-to-r2.sh >> /var/log/suho-backup.log 2>&1
```

---

## 🐛 Troubleshooting

### Error: .env file not found

```bash
cp .env.backup .env
nano .env  # Fill in your credentials
```

### Error: PostgreSQL backup failed

```bash
# Check container is running
docker ps | grep postgresql

# Check logs
docker logs suho-postgresql
```

### Error: AWS CLI not found

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Error: Access Denied to R2

```bash
# Verify credentials in .env
cat .env | grep R2_

# Test AWS CLI connection
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
aws s3 ls --endpoint-url https://your-account.r2.cloudflarestorage.com
```

---

## 📝 Notes

- ✅ **Simple & Manual** - No automatic cron jobs, full control
- ✅ **Secure** - Credentials in `.env` (gitignored)
- ✅ **Cost-effective** - Cloudflare R2 free tier is generous
- ✅ **S3-compatible** - Easy to switch to AWS S3 if needed
- ✅ **Tested** - Works with TimescaleDB + ClickHouse

---

## 🔗 Resources

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [AWS CLI for R2](https://developers.cloudflare.com/r2/examples/aws-cli/)
- [PostgreSQL pg_dumpall](https://www.postgresql.org/docs/current/app-pg-dumpall.html)
- [ClickHouse BACKUP/RESTORE](https://clickhouse.com/docs/en/operations/backup)

---

**Need help?** Check Docker logs or contact the DevOps team.
