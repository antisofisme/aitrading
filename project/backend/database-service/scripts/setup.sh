#!/bin/bash

# Database Service Setup Script
# This script sets up the database service environment

set -e

echo "🚀 Setting up Database Service for AI Trading Platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version 18 or higher is required. Current version: $(node -v)"
    exit 1
fi

print_status "Node.js version: $(node -v) ✓"

# Check if PostgreSQL is available
if command -v psql &> /dev/null; then
    print_status "PostgreSQL client found ✓"
else
    print_warning "PostgreSQL client not found. Install postgresql-client for database operations."
fi

# Create necessary directories
print_header "Creating directory structure..."
mkdir -p logs
mkdir -p config
mkdir -p migrations/rollbacks
mkdir -p tests
mkdir -p scripts
print_status "Directories created ✓"

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f config/.env.example ]; then
        cp config/.env.example .env
        print_status "Environment file created from example ✓"
        print_warning "Please update .env file with your database credentials"
    else
        print_error "Environment example file not found"
    fi
else
    print_status "Environment file already exists ✓"
fi

# Install dependencies
print_header "Installing dependencies..."
npm install
print_status "Dependencies installed ✓"

# Check if Docker is available
if command -v docker &> /dev/null; then
    print_status "Docker found ✓"

    # Check if Docker Compose is available
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_status "Docker Compose found ✓"
        print_status "You can start the full stack with: docker-compose -f docker/docker-compose.yml up -d"
    else
        print_warning "Docker Compose not found. Install docker-compose for containerized deployment."
    fi
else
    print_warning "Docker not found. Install Docker for containerized deployment."
fi

# Create startup script
cat > start.sh << 'EOF'
#!/bin/bash

# Start Database Service
echo "Starting Database Service..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run migrations if database is available
if command -v psql &> /dev/null && [ ! -z "$DB_HOST" ]; then
    echo "Running database migrations..."
    npm run migrate || echo "Migration failed or no migrations to run"
fi

# Start the service
npm start
EOF

chmod +x start.sh

# Create development startup script
cat > start-dev.sh << 'EOF'
#!/bin/bash

# Start Database Service in Development Mode
echo "Starting Database Service in Development Mode..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start with nodemon for auto-restart
npm run dev
EOF

chmod +x start-dev.sh

# Create database setup script
cat > scripts/db-setup.sh << 'EOF'
#!/bin/bash

# Database Setup Script
echo "Setting up database..."

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Default values
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-aitrading}
DB_USER=${DB_USER:-postgres}

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; then
    echo "PostgreSQL is not running or not accessible"
    exit 1
fi

# Create database if it doesn't exist
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME 2>/dev/null || echo "Database $DB_NAME already exists"

# Run migrations
echo "Running migrations..."
npm run migrate

echo "Database setup complete!"
EOF

chmod +x scripts/db-setup.sh

# Create health check script
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash

# Health Check Script
PORT=${PORT:-8008}
HEALTH_URL="http://localhost:$PORT/health"

echo "Checking service health at $HEALTH_URL"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -eq 200 ]; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is unhealthy (HTTP $response)"
    exit 1
fi
EOF

chmod +x scripts/health-check.sh

print_status "Setup scripts created ✓"

print_header "Setup completed successfully! 🎉"
echo ""
print_status "Next steps:"
echo "  1. Update .env file with your database credentials"
echo "  2. Start PostgreSQL database"
echo "  3. Run: ./scripts/db-setup.sh (to set up database)"
echo "  4. Run: ./start-dev.sh (for development)"
echo "  5. Run: ./start.sh (for production)"
echo ""
print_status "Docker deployment:"
echo "  docker-compose -f docker/docker-compose.yml up -d"
echo ""
print_status "Health check:"
echo "  ./scripts/health-check.sh"
echo ""
print_status "Port: 8008"
print_status "Health endpoint: http://localhost:8008/health"