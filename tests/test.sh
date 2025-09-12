#!/bin/bash

# Comprehensive Digital Krishi Officer API Test Runner
# This script runs all test suites for the complete application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${BLUE}🧪 Digital Krishi Officer API - Comprehensive Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --pytest         Use pytest to run individual test modules"
    echo "  --comprehensive  Run comprehensive test suite (default)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run comprehensive test suite"
    echo "  $0 --pytest           # Run with pytest"
    echo ""
    echo "Test Suites Included:"
    echo "  ✅ Core Functionality (Auth, Chat, Profiles)"
    echo "  ✅ Image Analysis (Upload, AI Vision, Analysis)"
    echo "  ✅ Knowledge Repository (Q&A, Vector Search)"
    echo "  ✅ Community Features (Groups, Messages)"
    echo "  ✅ Location Services (Retailers, Geospatial)"
}

# Default mode
USE_PYTEST=false
USE_COMPREHENSIVE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pytest)
            USE_PYTEST=true
            USE_COMPREHENSIVE=false
            shift
            ;;
        --comprehensive)
            USE_COMPREHENSIVE=true
            USE_PYTEST=false
            shift
            ;;
        --help)
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

echo -e "${BLUE}🚀 Digital Krishi Officer API - Comprehensive Test Runner${NC}"
echo "=" * 60

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
echo -e "${YELLOW}🎯 Target API: http://localhost:8000${NC}"
echo ""

if [[ "$USE_PYTEST" == "true" ]]; then
    echo -e "${YELLOW}🔬 Running tests with pytest...${NC}"
    echo ""
    
    # Run each test module with pytest
    test_modules=(
        "tests/test_container_endpoints.py"
        "tests/test_analysis_endpoints.py"
        "tests/test_knowledge_endpoints.py"
        "tests/test_community_endpoints.py"
        "tests/test_location_endpoints.py"
    )
    
    for module in "${test_modules[@]}"; do
        echo -e "${BLUE}Running $module...${NC}"
        uv run pytest "$module" -v
        echo ""
    done
    
else
    echo -e "${YELLOW}🚀 Running comprehensive test suite...${NC}"
    echo ""
    
    # Run comprehensive test runner
    uv run python tests/run_all_tests.py
fi

RESULT=$?

if [[ $RESULT -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}✅ Your Digital Krishi Officer API is fully functional and ready for production!${NC}"
else
    echo ""
    echo -e "${RED}❌ SOME TESTS FAILED! (Exit code: $RESULT)${NC}"
    echo -e "${YELLOW}💡 Please review the test output above for details.${NC}"
fi

exit $RESULT