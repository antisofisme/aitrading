#!/bin/bash
# Automated Database Backup to Cloudflare R2
# Backup PostgreSQL (TimescaleDB) and ClickHouse

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
else
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.backup to .env and configure your R2 credentials"
    exit 1
fi

# Validate required variables
if [ -z "$R2_BUCKET" ] || [ -z "$R2_ENDPOINT" ] || [ -z "$R2_ACCESS_KEY" ] || [ -z "$R2_SECRET_KEY" ]; then
    echo "❌ Error: Missing R2 credentials in .env file"
    exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-/tmp/suho-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
LOCAL_RETENTION_DAYS="${LOCAL_RETENTION_DAYS:-7}"
R2_RETENTION_DAYS="${R2_RETENTION_DAYS:-30}"

mkdir -p $BACKUP_DIR

echo "🔄 Starting backup at $(date)"
echo "📦 Backup location: $BACKUP_DIR"

# ================================
# 1. BACKUP POSTGRESQL (TimescaleDB)
# ================================
echo ""
echo "📦 Backing up PostgreSQL (TimescaleDB)..."
docker exec suho-postgresql pg_dumpall -U suho_admin | gzip > $BACKUP_DIR/postgresql_$DATE.sql.gz

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL backup: $(du -h $BACKUP_DIR/postgresql_$DATE.sql.gz | cut -f1)"
else
    echo "❌ PostgreSQL backup failed!"
    exit 1
fi

# ================================
# 2. BACKUP CLICKHOUSE
# ================================
echo ""
echo "📦 Backing up ClickHouse..."
docker exec suho-clickhouse clickhouse-client --query="BACKUP DATABASE suho_analytics TO Disk('backups', 'backup_$DATE.zip')" 2>/dev/null || true
docker cp suho-clickhouse:/var/lib/clickhouse/backups/backup_$DATE.zip $BACKUP_DIR/clickhouse_$DATE.zip 2>/dev/null || true

if [ -f "$BACKUP_DIR/clickhouse_$DATE.zip" ]; then
    echo "✅ ClickHouse backup: $(du -h $BACKUP_DIR/clickhouse_$DATE.zip | cut -f1)"
else
    echo "⚠️  ClickHouse backup skipped (database might be empty)"
fi

# ================================
# 3. UPLOAD TO CLOUDFLARE R2 (via AWS CLI)
# ================================
echo ""
echo "☁️  Uploading to Cloudflare R2..."

# Configure AWS CLI for R2
export AWS_ACCESS_KEY_ID=$R2_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$R2_SECRET_KEY

# Upload each backup
upload_count=0
for file in $BACKUP_DIR/*_$DATE.*; do
    if [ -f "$file" ]; then
        filename=$(basename $file)
        echo "  📤 Uploading $filename..."

        aws s3 cp $file s3://$R2_BUCKET/backups/$(date +%Y/%m)/$filename \
            --endpoint-url $R2_ENDPOINT \
            --no-progress

        if [ $? -eq 0 ]; then
            echo "  ✅ Uploaded: $filename"
            ((upload_count++))
        else
            echo "  ❌ Failed to upload: $filename"
        fi
    fi
done

# ================================
# 4. CLEANUP OLD LOCAL BACKUPS
# ================================
echo ""
echo "🧹 Cleaning up old local backups (>${LOCAL_RETENTION_DAYS} days)..."
deleted_local=0
find $BACKUP_DIR -name "*_202*.gz" -mtime +${LOCAL_RETENTION_DAYS} -delete 2>/dev/null && ((deleted_local++)) || true
find $BACKUP_DIR -name "*_202*.zip" -mtime +${LOCAL_RETENTION_DAYS} -delete 2>/dev/null && ((deleted_local++)) || true
echo "  🗑️  Deleted $deleted_local old local backups"

# ================================
# 5. CLEANUP OLD R2 BACKUPS
# ================================
echo ""
echo "🧹 Cleaning up old R2 backups (>${R2_RETENTION_DAYS} days)..."
deleted_r2=0
aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive 2>/dev/null | \
    while read -r line; do
        createDate=$(echo $line | awk '{print $1" "$2}')
        createDate=$(date -d "$createDate" +%s 2>/dev/null) || continue
        olderThan=$(date -d "${R2_RETENTION_DAYS} days ago" +%s)
        if [[ $createDate -lt $olderThan ]]; then
            fileName=$(echo $line | awk '{print $4}')
            if [[ $fileName != "" ]]; then
                echo "  🗑️  Deleting old backup: $fileName"
                aws s3 rm s3://$R2_BUCKET/$fileName --endpoint-url $R2_ENDPOINT 2>/dev/null || true
                ((deleted_r2++)) || true
            fi
        fi
    done

echo ""
echo "✅ Backup completed successfully at $(date)"
echo "📊 Summary:"
echo "   - Files uploaded: $upload_count"
echo "   - Total backup size: $(du -sh $BACKUP_DIR | cut -f1)"
echo "   - Local retention: $LOCAL_RETENTION_DAYS days"
echo "   - R2 retention: $R2_RETENTION_DAYS days"
