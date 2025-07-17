#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_SERVICE_NAME="test-validation-service"
TEST_ORG="testorg"
TEST_SOLUTION="testsolution"
TEST_PREFIX="testprefix"
TEST_SUFFIX="testsuffix"
MAX_STARTUP_TIME=120 # 2 minutes in seconds
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="$(mktemp -d)"
VALIDATION_LOG="$TEMP_DIR/validation.log"

# Cleanup function
cleanup() {
    echo -e "${BLUE}Cleaning up...${NC}"
    if [ -d "$TEMP_DIR/$TEST_SERVICE_NAME" ]; then
        cd "$TEMP_DIR/$TEST_SERVICE_NAME"
        if [ -f "docker-compose.yml" ]; then
            docker-compose down --volumes --remove-orphans 2>/dev/null || true
        fi
    fi
    rm -rf "$TEMP_DIR"
}

# Trap cleanup on exit
trap cleanup EXIT

# Logging function
log() {
    echo -e "$1" | tee -a "$VALIDATION_LOG"
}

# Success/Failure tracking
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        log "${GREEN}✅ $2${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log "${RED}❌ $2${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log "${BLUE}Checking prerequisites...${NC}"
    
    local missing_deps=()
    
    if ! command_exists archetect; then
        missing_deps+=("archetect")
    fi
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists uv; then
        missing_deps+=("uv")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log "${RED}Missing required dependencies: ${missing_deps[*]}${NC}"
        log "${YELLOW}Please install the missing dependencies and try again.${NC}"
        exit 1
    fi
    
    test_result 0 "All prerequisites available"
}

# Generate test service from archetype
generate_test_service() {
    log "\n${BLUE}Generating test service from archetype...${NC}"
    
    cd "$TEMP_DIR"
    
    # Create answers file for test generation
    cat > test_answers.yaml << EOF
---
org-name: "$TEST_ORG"
solution-name: "$TEST_SOLUTION"
prefix-name: "$TEST_PREFIX"
suffix-name: "$TEST_SUFFIX"
EOF
    
    # Generate the service
    if archetect generate "$SCRIPT_DIR" "$TEST_SERVICE_NAME" --answers test_answers.yaml >> "$VALIDATION_LOG" 2>&1; then
        test_result 0 "Archetype generation successful"
    else
        test_result 1 "Archetype generation failed"
        return 1
    fi
    
    # Verify the generated structure
    if [ -d "$TEST_SERVICE_NAME" ]; then
        test_result 0 "Generated service directory exists"
    else
        test_result 1 "Generated service directory missing"
        return 1
    fi
}

# Run template validation
validate_template_substitution() {
    log "\n${BLUE}Validating template variable substitution...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    if [ -f "scripts/validate_templates.py" ]; then
        if python scripts/validate_templates.py >> "$VALIDATION_LOG" 2>&1; then
            test_result 0 "Template validation passed - no hardcoded references found"
        else
            test_result 1 "Template validation failed - hardcoded references detected"
            log "${YELLOW}Check validation log for details: $VALIDATION_LOG${NC}"
            return 1
        fi
    else
        test_result 1 "Template validation script not found"
        return 1
    fi
}

# Test UV sync on all packages
test_uv_sync() {
    log "\n${BLUE}Testing UV sync on all packages...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    local sync_failed=0
    
    # Find all pyproject.toml files and sync each package
    while IFS= read -r -d '' pyproject_file; do
        package_dir=$(dirname "$pyproject_file")
        package_name=$(basename "$package_dir")
        
        log "${YELLOW}Syncing package: $package_name${NC}"
        
        if (cd "$package_dir" && uv sync >> "$VALIDATION_LOG" 2>&1); then
            log "${GREEN}  ✅ $package_name sync successful${NC}"
        else
            log "${RED}  ❌ $package_name sync failed${NC}"
            sync_failed=1
        fi
    done < <(find . -name "pyproject.toml" -print0)
    
    test_result $sync_failed "UV sync on all packages"
}

# Test Docker build and startup
test_docker_stack() {
    log "\n${BLUE}Testing Docker stack build and startup...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    # Build the Docker stack
    if docker-compose build >> "$VALIDATION_LOG" 2>&1; then
        test_result 0 "Docker build successful"
    else
        test_result 1 "Docker build failed"
        return 1
    fi
    
    # Start the stack
    log "${YELLOW}Starting Docker stack...${NC}"
    if docker-compose up -d >> "$VALIDATION_LOG" 2>&1; then
        test_result 0 "Docker stack started"
    else
        test_result 1 "Docker stack failed to start"
        return 1
    fi
    
    # Wait for services to be ready and measure startup time
    local start_time=$(date +%s)
    local max_wait=60
    local waited=0
    
    log "${YELLOW}Waiting for services to be ready...${NC}"
    
    while [ $waited -lt $max_wait ]; do
        if docker-compose ps | grep -q "Up"; then
            local end_time=$(date +%s)
            local startup_time=$((end_time - start_time))
            log "${GREEN}Services ready in ${startup_time} seconds${NC}"
            
            if [ $startup_time -le $MAX_STARTUP_TIME ]; then
                test_result 0 "Service startup time within 2 minutes ($startup_time seconds)"
            else
                test_result 1 "Service startup time exceeded 2 minutes ($startup_time seconds)"
            fi
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done
    
    if [ $waited -ge $max_wait ]; then
        test_result 1 "Services failed to start within timeout"
        return 1
    fi
}

# Test service connectivity
test_service_connectivity() {
    log "\n${BLUE}Testing service connectivity...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    # Test gRPC service port
    if curl -s --connect-timeout 5 http://localhost:50051 >/dev/null 2>&1 || 
       nc -z localhost 50051 >/dev/null 2>&1; then
        test_result 0 "gRPC service port accessible"
    else
        test_result 1 "gRPC service port not accessible"
    fi
    
    # Test management port
    if curl -s --connect-timeout 5 http://localhost:9011/health >/dev/null 2>&1; then
        test_result 0 "Management health endpoint accessible"
    else
        test_result 1 "Management health endpoint not accessible"
    fi
    
    # Test metrics endpoint
    if curl -s --connect-timeout 5 http://localhost:9011/metrics | grep -q "grpc_" 2>/dev/null; then
        test_result 0 "Metrics endpoint accessible and contains gRPC metrics"
    else
        test_result 1 "Metrics endpoint not accessible or missing gRPC metrics"
    fi
}

# Test monitoring infrastructure
test_monitoring() {
    log "\n${BLUE}Testing monitoring infrastructure...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    # Test Prometheus
    if curl -s --connect-timeout 10 http://localhost:9090/-/healthy >/dev/null 2>&1; then
        test_result 0 "Prometheus accessible"
    else
        test_result 1 "Prometheus not accessible"
    fi
    
    # Test Grafana
    if curl -s --connect-timeout 10 http://localhost:3000/api/health | grep -q "ok" 2>/dev/null; then
        test_result 0 "Grafana accessible"
    else
        test_result 1 "Grafana not accessible"
    fi
}

# Run integration tests
run_integration_tests() {
    log "\n${BLUE}Running integration tests...${NC}"
    
    cd "$TEMP_DIR/$TEST_SERVICE_NAME"
    
    if [ -f "scripts/run-integration-tests.sh" ]; then
        # Make the script executable
        chmod +x scripts/run-integration-tests.sh
        
        if ./scripts/run-integration-tests.sh >> "$VALIDATION_LOG" 2>&1; then
            test_result 0 "Integration tests passed"
        else
            test_result 1 "Integration tests failed"
            return 1
        fi
    else
        test_result 1 "Integration test script not found"
        return 1
    fi
}

# Main validation workflow
main() {
    log "${BLUE}========================================${NC}"
    log "${BLUE}Python gRPC Service Archetype Validation${NC}"
    log "${BLUE}========================================${NC}"
    log "Validation log: $VALIDATION_LOG"
    log "Temp directory: $TEMP_DIR"
    
    local overall_start_time=$(date +%s)
    
    # Run all validation steps
    check_prerequisites || exit 1
    generate_test_service || exit 1
    validate_template_substitution || exit 1
    
    log "\n${BLUE}Starting end-to-end timing measurement...${NC}"
    local e2e_start_time=$(date +%s)
    
    test_uv_sync || exit 1
    test_docker_stack || exit 1
    test_service_connectivity || exit 1
    test_monitoring || exit 1
    run_integration_tests || exit 1
    
    local e2e_end_time=$(date +%s)
    local e2e_total_time=$((e2e_end_time - e2e_start_time))
    
    log "\n${BLUE}End-to-end time (sync + build + start + test): ${e2e_total_time} seconds${NC}"
    
    if [ $e2e_total_time -le $MAX_STARTUP_TIME ]; then
        test_result 0 "End-to-end workflow within 2 minutes ($e2e_total_time seconds)"
    else
        test_result 1 "End-to-end workflow exceeded 2 minutes ($e2e_total_time seconds)"
    fi
    
    local overall_end_time=$(date +%s)
    local total_time=$((overall_end_time - overall_start_time))
    
    # Final summary
    log "\n${BLUE}========================================${NC}"
    log "${BLUE}Validation Summary${NC}"
    log "${BLUE}========================================${NC}"
    log "Total tests: $((TESTS_PASSED + TESTS_FAILED))"
    log "${GREEN}Passed: $TESTS_PASSED${NC}"
    log "${RED}Failed: $TESTS_FAILED${NC}"
    log "Total validation time: $total_time seconds"
    log "End-to-end workflow time: $e2e_total_time seconds"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log "\n${GREEN}🎉 All validation tests passed! Archetype is ready for release.${NC}"
        return 0
    else
        log "\n${RED}❌ Validation failed. Please check the issues above.${NC}"
        log "${YELLOW}Validation log available at: $VALIDATION_LOG${NC}"
        return 1
    fi
}

# Run main function
main "$@" 