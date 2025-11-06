#!/bin/bash

# Backup script for production database
# Usage: ./backup-db.sh

set -e

BACKUP_DIR="/opt/easymeal/backups"
DB_PATH="/opt/easymeal/easymeal_reboot/data/meals.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/meals_${TIMESTAMP}.db"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Backup database
if [ -f "${DB_PATH}" ]; then
    cp "${DB_PATH}" "${BACKUP_FILE}"
    echo "✅ Database backed up to: ${BACKUP_FILE}"
    
    # Keep only last 10 backups
    ls -t ${BACKUP_DIR}/meals_*.db | tail -n +11 | xargs rm -f
    
    echo "📦 Backup complete. Latest backups:"
    ls -lh ${BACKUP_DIR}/meals_*.db | tail -5
else
    echo "⚠️  Database file not found at: ${DB_PATH}"
    exit 1
fi

