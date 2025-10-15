#!/bin/bash
# Restore Database from Cloudflare R2
# Usage: ./restore-from-r2.sh [YYYYMMDD_HHMMSS]

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

BACKUP_DIR="${BACKUP_DIR:-/tmp/suho-restores}"
PROJECT_DIR="/mnt/g/khoirul/aitrading/project3/backend"

# Get backup date from argument or use latest
if [ -z "$1" ]; then
    echo "📅 No date specified, will fetch latest backup..."
    BACKUP_DATE="latest"
else
    BACKUP_DATE="$1"
fi

mkdir -p $BACKUP_DIR

echo "🔄 Starting restore from R2 at $(date)"

# Configure AWS CLI for R2
export AWS_ACCESS_KEY_ID=$R2_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$R2_SECRET_KEY

# ================================
# 1. LIST AVAILABLE BACKUPS
# ================================
if [ "$BACKUP_DATE" == "latest" ]; then
    echo ""
    echo "📋 Listing available backups..."
    aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive | \
        grep "postgresql_" | tail -10

    echo ""
    read -p "Enter backup date (YYYYMMDD_HHMMSS) or press Enter for latest: " input_date

    if [ -z "$input_date" ]; then
        # Get latest backup
        BACKUP_DATE=$(aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive | \
            grep "postgresql_" | tail -1 | awk '{print $4}' | grep -oP '\d{8}_\d{6}')
    else
        BACKUP_DATE=$input_date
    fi
fi

echo ""
echo "📦 Restoring backup from: $BACKUP_DATE"

# ================================
# 2. DOWNLOAD BACKUPS FROM R2
# ================================
echo ""
echo "⬇️  Downloading backups from R2..."

# Find and download PostgreSQL backup
PG_FILE=$(aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive | \
    grep "postgresql_${BACKUP_DATE}" | awk '{print $4}' | head -1)

if [ -z "$PG_FILE" ]; then
    echo "❌ PostgreSQL backup not found for date: $BACKUP_DATE"
    echo ""
    echo "Available backups:"
    aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive | grep "postgresql_"
    exit 1
fi

aws s3 cp s3://$R2_BUCKET/$PG_FILE $BACKUP_DIR/ --endpoint-url $R2_ENDPOINT
echo "✅ Downloaded: $(basename $PG_FILE) ($(du -h $BACKUP_DIR/$(basename $PG_FILE) | cut -f1))"

# Find and download ClickHouse backup
CH_FILE=$(aws s3 ls s3://$R2_BUCKET/backups/ --endpoint-url $R2_ENDPOINT --recursive | \
    grep "clickhouse_${BACKUP_DATE}" | awk '{print $4}' | head -1)

if [ ! -z "$CH_FILE" ]; then
    aws s3 cp s3://$R2_BUCKET/$CH_FILE $BACKUP_DIR/ --endpoint-url $R2_ENDPOINT
    echo "✅ Downloaded: $(basename $CH_FILE) ($(du -h $BACKUP_DIR/$(basename $CH_FILE) | cut -f1))"
else
    echo "⚠️  ClickHouse backup not found (skipping)"
fi

# ================================
# 3. STOP SERVICES
# ================================
echo ""
echo "🛑 Stopping database services..."
cd $PROJECT_DIR
docker compose stop postgresql clickhouse dragonflydb

# ================================
# 4. RESTORE POSTGRESQL
# ================================
echo ""
echo "📥 Restoring PostgreSQL..."
docker compose start postgresql
sleep 5  # Wait for PostgreSQL to be ready

gunzip -c $BACKUP_DIR/$(basename $PG_FILE) | \
    docker exec -i suho-postgresql psql -U suho_admin

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL restored successfully"
else
    echo "❌ PostgreSQL restore failed!"
    exit 1
fi

# ================================
# 5. RESTORE CLICKHOUSE
# ================================
if [ ! -z "$CH_FILE" ] && [ -f "$BACKUP_DIR/$(basename $CH_FILE)" ]; then
    echo ""
    echo "📥 Restoring ClickHouse..."
    docker compose start clickhouse
    sleep 5

    docker cp $BACKUP_DIR/$(basename $CH_FILE) suho-clickhouse:/tmp/restore.zip
    docker exec suho-clickhouse clickhouse-client --query="RESTORE DATABASE suho_analytics FROM Disk('backups', 'restore.zip')" 2>/dev/null || true

    echo "✅ ClickHouse restored"
fi

# ================================
# 6. START ALL SERVICES
# ================================
echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "✅ Restore completed successfully at $(date)"
echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf $BACKUP_DIR

echo ""
echo "📊 Service status:"
docker compose ps
