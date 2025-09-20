#!/bin/bash
# Deploy API Gateway Service
# Service-specific deployment script following CLAUDE.md Section 13

set -e

SERVICE_NAME="api-gateway"
DEFAULT_TIER="tier2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

usage() {
    echo "Usage: $0 [tier1|tier2] [--build-only] [--no-cache]"
    echo ""
    echo "Tiers:"
    echo "  tier1    - Core dependencies (Development)"
    echo "  tier2    - Service dependencies (Production Ready)"
    echo ""
    echo "Options:"
    echo "  --build-only    Build only, don't start containers"
    echo "  --no-cache      Build without Docker cache"
    echo ""
    echo "Example: $0 tier2"
}

check_requirements() {
    local tier=$1
    
    if [[ ! -f "requirements/tier1-core.txt" ]]; then
        print_error "Missing requirements/tier1-core.txt"
        exit 1
    fi
    
    if [[ "$tier" != "tier1" && ! -f "requirements/tier2-service.txt" ]]; then
        print_error "Missing requirements/tier2-service.txt"
        exit 1
    fi
}

check_wheels() {
    local tier=$1
    
    if [[ ! -d "wheels/$tier" ]]; then
        print_warning "No wheels found for $tier"
        print_status "Downloading wheels for $tier..."
        python scripts/download_wheels.py --tier "$tier"
    fi
}

deploy_service() {
    local tier=${1:-$DEFAULT_TIER}
    local build_only=${2:-false}
    local no_cache=${3:-false}
    
    print_status "Deploying $SERVICE_NAME service - $tier"
    
    # Check requirements
    check_requirements "$tier"
    
    # Check wheels
    check_wheels "$tier"
    
    # Build arguments
    local build_args="--build-arg TIER=$tier"
    if [[ "$no_cache" == "true" ]]; then
        build_args="$build_args --no-cache"
    fi
    
    # Build service
    print_status "Building $SERVICE_NAME:$tier..."
    if docker build $build_args -t "$SERVICE_NAME:$tier" -f Dockerfile --target "$tier" . ; then
        print_success "Build completed for $SERVICE_NAME:$tier"
    else
        print_error "Build failed for $SERVICE_NAME:$tier"
        exit 1
    fi
    
    # Start service if not build-only
    if [[ "$build_only" != "true" ]]; then
        print_status "Starting $SERVICE_NAME service..."
        
        # Stop existing container if running
        if docker ps -q -f name="$SERVICE_NAME" | grep -q .; then
            print_status "Stopping existing $SERVICE_NAME container..."
            docker stop "$SERVICE_NAME" || true
            docker rm "$SERVICE_NAME" || true
        fi
        
        # Start new container
        if docker run -d --name "$SERVICE_NAME" \
            -p 8001:8000 \
            -e SERVICE_TIER="$tier" \
            -e SERVICE_NAME="$SERVICE_NAME" \
            --restart unless-stopped \
            "$SERVICE_NAME:$tier"; then
            print_success "$SERVICE_NAME service started successfully"
            
            # Health check
            print_status "Waiting for service to be ready..."
            sleep 5
            
            if curl -f http://localhost:8001/health > /dev/null 2>&1; then
                print_success "$SERVICE_NAME service is healthy"
            else
                print_warning "$SERVICE_NAME service may not be ready yet"
            fi
        else
            print_error "Failed to start $SERVICE_NAME service"
            exit 1
        fi
    fi
}

# Parse arguments
TIER="$DEFAULT_TIER"
BUILD_ONLY=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        tier1|tier2)
            TIER="$1"
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Change to service directory
cd "$(dirname "$0")/.."

# Deploy
deploy_service "$TIER" "$BUILD_ONLY" "$NO_CACHE"

print_success "API Gateway deployment completed!"
print_status "Service available at: http://localhost:8001"