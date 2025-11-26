# Database Migration Guide

This guide explains how to migrate from SQLite to PostgreSQL and photos from filesystem to MinIO.

## Prerequisites

1. Docker and Docker Compose installed
2. Existing SQLite database at `data/meals.db` (if migrating existing data)
3. Existing photos in `data/photos/` directory (if migrating existing photos)

## Migration Steps

### 1. Start Services

Start PostgreSQL and MinIO services:

```bash
docker-compose up -d postgres minio
```

Wait for services to be healthy (check with `docker-compose ps`).

### 2. Run Migration Script

Run the migration script to transfer data from SQLite to PostgreSQL and photos to MinIO:

```bash
docker-compose run --rm api python migrate_db.py
```

Or if you want to run it manually inside the container:

```bash
docker-compose exec api python migrate_db.py
```

### 3. Start Full Application

Start all services:

```bash
docker-compose up -d
```

### 4. Verify Migration

- Check PostgreSQL: `docker-compose exec postgres psql -U easymeal -d easymeal -c "SELECT COUNT(*) FROM users;"`
- Check MinIO console: http://localhost:9001 (login with MINIO_ROOT_USER/MINIO_ROOT_PASSWORD)
- Test API endpoints

## Notes

- The migration script is idempotent - it won't duplicate data if run multiple times
- Existing SQLite database and photos are not deleted - they remain as backup
- If no SQLite database exists, the script will just initialize an empty PostgreSQL database

## Troubleshooting

- **Connection errors**: Ensure PostgreSQL and MinIO are healthy before running migration
- **Photo migration fails**: Check that photos directory exists and is accessible
- **Duplicate key errors**: Data may already be migrated - check PostgreSQL first

