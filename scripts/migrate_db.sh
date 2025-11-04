#!/bin/bash
# Database migration helper script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
COMMAND="upgrade"
TARGET="head"

# Help message
show_help() {
    echo "Database Migration Helper"
    echo ""
    echo "Usage: $0 [command] [target]"
    echo ""
    echo "Commands:"
    echo "  upgrade [target]  - Upgrade to target revision (default: head)"
    echo "  downgrade [target] - Downgrade to target revision"
    echo "  current          - Show current revision"
    echo "  history          - Show migration history"
    echo "  test             - Test migrations (up, down, up)"
    echo "  preview          - Preview SQL without running"
    echo ""
    echo "Examples:"
    echo "  $0                    # Upgrade to latest"
    echo "  $0 upgrade head       # Upgrade to latest"
    echo "  $0 downgrade -1       # Rollback one migration"
    echo "  $0 downgrade base     # Rollback all migrations"
    echo "  $0 test               # Test migration cycle"
    echo ""
}

# Check if DATABASE_URL is set
check_database() {
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}Warning: DATABASE_URL not set${NC}"
        echo "Using default: postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test"
        export DATABASE_URL="postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test"
    else
        echo -e "${GREEN}Using DATABASE_URL: ${DATABASE_URL}${NC}"
    fi
}

# Run migration command
run_migration() {
    local cmd=$1
    local target=$2

    echo -e "${GREEN}Running: alembic $cmd $target${NC}"
    uv run alembic $cmd $target
}

# Test migrations
test_migrations() {
    echo -e "${YELLOW}Testing migrations...${NC}"

    # Save current revision
    CURRENT_REV=$(uv run alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1)

    echo -e "${GREEN}Step 1: Upgrade to head${NC}"
    uv run alembic upgrade head

    echo -e "${GREEN}Step 2: Verify tables exist${NC}"
    if command -v psql &> /dev/null; then
        # Extract connection details from DATABASE_URL
        DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
        DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:\/]*\).*/\1/p')

        echo "Checking tables in database..."
        TABLES=$(PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
                 psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "\dt" 2>/dev/null | grep -E "agents|workflow_states|coordination_events" | wc -l)

        if [ "$TABLES" -ge 3 ]; then
            echo -e "${GREEN}✓ Tables verified${NC}"
        else
            echo -e "${RED}✗ Some tables missing${NC}"
        fi
    fi

    echo -e "${GREEN}Step 3: Downgrade to base${NC}"
    uv run alembic downgrade base

    echo -e "${GREEN}Step 4: Upgrade to head again${NC}"
    uv run alembic upgrade head

    echo -e "${GREEN}✓ Migration test completed successfully${NC}"

    # Restore original revision if it wasn't at head
    if [ ! -z "$CURRENT_REV" ] && [ "$CURRENT_REV" != "head" ]; then
        echo -e "${YELLOW}Restoring to original revision: $CURRENT_REV${NC}"
        uv run alembic downgrade $CURRENT_REV
    fi
}

# Main script
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Parse arguments
if [ $# -eq 0 ]; then
    COMMAND="upgrade"
    TARGET="head"
elif [ $# -eq 1 ]; then
    COMMAND=$1
    if [ "$COMMAND" = "current" ] || [ "$COMMAND" = "history" ] || [ "$COMMAND" = "test" ] || [ "$COMMAND" = "preview" ]; then
        TARGET=""
    else
        TARGET="head"
    fi
else
    COMMAND=$1
    TARGET=$2
fi

# Check database configuration
check_database

# Execute command
case $COMMAND in
    upgrade)
        run_migration "upgrade" "$TARGET"
        ;;
    downgrade)
        run_migration "downgrade" "$TARGET"
        ;;
    current)
        echo -e "${GREEN}Current revision:${NC}"
        uv run alembic current -v
        ;;
    history)
        echo -e "${GREEN}Migration history:${NC}"
        uv run alembic history -v
        ;;
    test)
        test_migrations
        ;;
    preview)
        echo -e "${GREEN}Preview SQL for upgrade to head:${NC}"
        uv run alembic upgrade head --sql
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
