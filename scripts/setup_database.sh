#!/bin/bash

# Sarah AI Database Setup Script
# This script sets up the PostgreSQL database for Sarah AI

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Sarah AI Database Setup${NC}"
echo "========================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Loaded environment variables${NC}"
else
    echo -e "${YELLOW}⚠ No .env file found. Using defaults...${NC}"
    POSTGRES_HOST="localhost"
    POSTGRES_PORT="5432"
    POSTGRES_DB="sarah_ai_fresh"
    POSTGRES_USER="sarah_user"
    POSTGRES_PASSWORD="sarah_secure_2024"
fi

# Function to check if PostgreSQL is running
check_postgres() {
    if pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
        return 0
    else
        echo -e "${RED}✗ PostgreSQL is not running${NC}"
        return 1
    fi
}

# Function to check if database exists
database_exists() {
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -lqt | cut -d \| -f 1 | grep -qw $POSTGRES_DB
}

# Function to create database
create_database() {
    echo "Creating database $POSTGRES_DB..."
    
    # Try to create as superuser (postgres)
    sudo -u postgres psql <<EOF
CREATE DATABASE $POSTGRES_DB;
CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
\q
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database created successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Could not create database as superuser. It may already exist.${NC}"
    fi
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB < scripts/init_database.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Migrations completed successfully${NC}"
    else
        echo -e "${RED}✗ Migration failed${NC}"
        exit 1
    fi
}

# Main execution
echo ""
echo "Database Configuration:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo ""

# Check PostgreSQL
if ! check_postgres; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    sudo systemctl start postgresql
    sleep 2
    check_postgres || exit 1
fi

# Check if database exists
if database_exists; then
    echo -e "${GREEN}✓ Database $POSTGRES_DB already exists${NC}"
    echo -n "Do you want to run migrations anyway? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        run_migrations
    fi
else
    echo -e "${YELLOW}Database $POSTGRES_DB does not exist${NC}"
    create_database
    run_migrations
fi

# Test connection
echo ""
echo "Testing database connection..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database connection successful!${NC}"
    
    # Show table count
    TABLE_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo -e "${GREEN}✓ Database has $TABLE_COUNT tables${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Database setup complete!${NC}"
echo "You can now run the application with: python -m app.main"