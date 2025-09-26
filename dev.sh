#!/bin/bash

# Micro Weather Station Development Helper Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

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
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[DEV]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if docker-compose exists
check_compose() {
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        print_error "docker-compose is not installed."
        exit 1
    fi
}

# Start the development environment
start() {
    print_info "Starting Home Assistant development environment..."
    check_docker
    check_compose

    cd "$PROJECT_DIR"
    docker-compose up -d

    print_status "Home Assistant is starting up..."
    print_info "Access it at: http://localhost:8123"
    print_info "Check logs with: ./dev.sh logs"
}

# Stop the development environment
stop() {
    print_info "Stopping Home Assistant development environment..."
    cd "$PROJECT_DIR"
    docker-compose down
    print_status "Development environment stopped."
}

# Restart Home Assistant
restart() {
    print_info "Restarting Home Assistant..."
    cd "$PROJECT_DIR"
    docker-compose restart homeassistant
    print_status "Home Assistant restarted."
}

# Show logs
logs() {
    print_info "Showing Home Assistant logs (Ctrl+C to exit)..."
    cd "$PROJECT_DIR"
    docker-compose logs -f homeassistant
}

# Run tests
test() {
    print_info "Running tests..."
    cd "$PROJECT_DIR"

    if [ -d "test_env" ]; then
        ./test_env/bin/python -m pytest tests/ -v "$@"
    else
        print_error "Test environment not found. Run tests from the main directory."
        exit 1
    fi
}

# Clean up the environment
clean() {
    print_warning "This will remove all containers, volumes, and reset Home Assistant configuration."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up development environment..."
        cd "$PROJECT_DIR"
        docker-compose down -v
        rm -rf config/.storage config/.uuid config/secrets.yaml
        print_status "Environment cleaned. Run './dev.sh start' to recreate."
    fi
}

# Show help
help() {
    cat << EOF
Micro Weather Station Development Helper

USAGE:
    ./dev.sh [COMMAND]

COMMANDS:
    start     Start the development environment
    stop      Stop the development environment
    restart   Restart Home Assistant
    logs      Show Home Assistant logs
    test      Run the test suite
    clean     Clean up containers and volumes
    help      Show this help message

EXAMPLES:
    ./dev.sh start          # Start development environment
    ./dev.sh logs           # View logs
    ./dev.sh restart        # Restart after code changes
    ./dev.sh test           # Run tests
    ./dev.sh clean          # Reset everything

DEVELOPMENT WORKFLOW:
    1. ./dev.sh start       # Start environment
    2. Make code changes
    3. ./dev.sh restart     # Reload integration
    4. ./dev.sh logs        # Check for errors
    5. Test in browser at http://localhost:8123

EOF
}

# Main command handling
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    test)
        shift
        test "$@"
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        help
        exit 1
        ;;
esac
