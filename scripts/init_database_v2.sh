#!/bin/bash
# ============================================================================
# ChainGuardian AI - Database V2 Initialization Script
# ============================================================================
# Creates a new PostgreSQL database with tier-based 152-feature schema
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="chainguardian_v2"
DB_USER="chainguardian"
DB_PASSWORD="${CHAINGUARDIAN_DB_PASSWORD:-chainguardian123}"
SCHEMA_FILE="database/schema_v2_tiered.sql"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}ChainGuardian AI - Database V2 Initialization${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${RED}❌ Error: Schema file not found: $SCHEMA_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Database name: ${BLUE}$DB_NAME${NC}"
echo -e "  Database user: ${BLUE}$DB_USER${NC}"
echo -e "  Schema file:   ${BLUE}$SCHEMA_FILE${NC}"
echo ""

# Ask for confirmation
read -p "This will create a NEW database '$DB_NAME'. Continue? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Creating database user (if not exists)...${NC}"
sudo -u postgres psql -c "
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
            CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
            RAISE NOTICE 'User $DB_USER created';
        ELSE
            RAISE NOTICE 'User $DB_USER already exists';
        END IF;
    END
    \$\$;
" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Step 2: Dropping old database (if exists)...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Step 3: Creating new database...${NC}"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Step 4: Applying schema...${NC}"
sudo -u postgres psql -d $DB_NAME -f $SCHEMA_FILE 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Step 5: Granting permissions...${NC}"
sudo -u postgres psql -d $DB_NAME -c "
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;
" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Step 6: Verifying installation...${NC}"
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "
    SELECT
        'contracts' as table_name,
        COUNT(*) as row_count
    FROM contracts
    UNION ALL
    SELECT
        'contract_features',
        COUNT(*)
    FROM contract_features
    UNION ALL
    SELECT
        'vulnerability_labels',
        COUNT(*)
    FROM vulnerability_labels;
" 2>&1

echo ""
echo -e "${GREEN}Step 7: Checking schema...${NC}"
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "
    SELECT
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
"

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✅ Database V2 initialization complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Database Connection Info:${NC}"
echo -e "  Host:     ${BLUE}localhost${NC}"
echo -e "  Port:     ${BLUE}5432${NC}"
echo -e "  Database: ${BLUE}$DB_NAME${NC}"
echo -e "  User:     ${BLUE}$DB_USER${NC}"
echo -e "  Password: ${BLUE}[hidden]${NC}"
echo ""
echo -e "${YELLOW}To connect:${NC}"
echo -e "  ${BLUE}PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Update .env file with new database name"
echo -e "  2. Run extraction: ${BLUE}poetry run python scripts/build_database.py${NC}"
echo -e "  3. Export data: ${BLUE}poetry run python scripts/export_training_data.py${NC}"
echo ""
echo -e "${GREEN}Happy feature extracting! 🚀${NC}"
echo ""
