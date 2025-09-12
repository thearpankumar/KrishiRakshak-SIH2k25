#!/bin/bash

# Digital Krishi Officer API Test Runner using uv
# Usage: ./test.sh [options]

set -e

# Default values
URL="http://localhost:8000"
WAIT=false
TIMEOUT=120
VERBOSE=false

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_usage() {
    echo "Digital Krishi Officer API Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --url URL       Base URL for API (default: http://localhost:8000)"
    echo "  -w, --wait          Wait for service to be ready"
    echo "  -t, --timeout SEC   Timeout in seconds (default: 120)"
    echo "  -v, --verbose       Verbose output"
    echo "  -p, --pytest        Use pytest instead of direct execution"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Quick test run"
    echo "  $0 --wait --timeout 180        # Wait for container startup"
    echo "  $0 --url http://myapi:8000     # Test against different URL"
    echo "  $0 --pytest --verbose          # Run with pytest"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -w|--wait)
            WAIT=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--pytest)
            USE_PYTEST=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}🧪 Digital Krishi Officer API Test Runner${NC}"
echo -e "${YELLOW}🎯 Target URL: $URL${NC}"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Error: 'uv' is not installed or not in PATH${NC}"
    echo "Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📁 Working directory: $(pwd)${NC}"

if [[ "$USE_PYTEST" == "true" ]]; then
    echo -e "${YELLOW}🔬 Running tests with pytest...${NC}"
    
    if [[ "$VERBOSE" == "true" ]]; then
        uv run pytest tests/test_container_endpoints.py -v -s
    else
        uv run pytest tests/test_container_endpoints.py
    fi
    
else
    echo -e "${YELLOW}🚀 Running tests directly...${NC}"
    
    # Build command
    CMD="uv run python tests/run_tests.py --url $URL"
    
    if [[ "$WAIT" == "true" ]]; then
        CMD="$CMD --wait --timeout $TIMEOUT"
    fi
    
    echo -e "${YELLOW}⚡ Command: $CMD${NC}"
    echo ""
    
    # Execute the command
    eval $CMD
fi

RESULT=$?

if [[ $RESULT -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Some tests failed! (Exit code: $RESULT)${NC}"
fi

exit $RESULT