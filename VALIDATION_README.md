# Archetype Validation Suite

This document describes the comprehensive validation test suite for the Python gRPC Service Archetype.

## Overview

The `validate_archetype.sh` script provides end-to-end validation of the archetype to ensure it meets all success criteria before release.

## Prerequisites

The following tools must be installed and available in your PATH:

- `archetect` - For generating services from the archetype
- `docker` - For container operations
- `docker-compose` - For orchestrating the service stack
- `uv` - For Python package management
- `curl` - For HTTP connectivity testing
- `nc` (netcat) - For port connectivity testing

## Usage

```bash
# Run the complete validation suite
./validate_archetype.sh
```

## What It Tests

### 1. **Archetype Generation**
- Generates a test service using `archetect`
- Verifies the generated directory structure
- Uses test values: `testorg/testsolution/testprefix/testsuffix`

### 2. **Template Variable Substitution**
- Runs the `validate_templates.py` script
- Ensures no hardcoded references remain
- Validates all template variables are properly substituted

### 3. **Package Management**
- Runs `uv sync` on all packages
- Tests dependency resolution
- Verifies all pyproject.toml files are valid

### 4. **Docker Infrastructure**
- Builds the complete Docker stack
- Starts all services (gRPC service, PostgreSQL, Prometheus, Grafana)
- Measures startup time against the 2-minute requirement

### 5. **Service Connectivity**
- Tests gRPC service port (50051)
- Tests management health endpoint (9011/health)
- Tests metrics endpoint (9011/metrics)
- Verifies gRPC metrics are exposed

### 6. **Monitoring Infrastructure**
- Tests Prometheus accessibility (9090)
- Tests Grafana accessibility (3000)
- Verifies monitoring stack integration

### 7. **Integration Tests**
- Runs the full integration test suite
- Verifies 100% test pass rate
- Tests gRPC connectivity and business logic

## Success Criteria

The validation suite verifies all PRD success criteria:

✅ **0 manual fixes required** - Template generates working service  
✅ **<2 minutes from generation to running service** - Timed end-to-end workflow  
✅ **100% integration test pass rate** - All tests must pass  
✅ **All 10 documented issues resolved** - Comprehensive validation coverage  

## Output

The script provides:
- Colored console output with clear pass/fail indicators
- Detailed timing measurements
- Comprehensive test summary
- Validation log for troubleshooting

### Example Output

```
========================================
Python gRPC Service Archetype Validation
========================================

✅ All prerequisites available
✅ Archetype generation successful
✅ Generated service directory exists
✅ Template validation passed - no hardcoded references found
✅ UV sync on all packages
✅ Docker build successful
✅ Docker stack started
✅ Service startup time within 2 minutes (45 seconds)
✅ gRPC service port accessible
✅ Management health endpoint accessible
✅ Metrics endpoint accessible and contains gRPC metrics
✅ Prometheus accessible
✅ Grafana accessible
✅ Integration tests passed
✅ End-to-end workflow within 2 minutes (87 seconds)

========================================
Validation Summary
========================================
Total tests: 14
Passed: 14
Failed: 0
Total validation time: 120 seconds
End-to-end workflow time: 87 seconds

🎉 All validation tests passed! Archetype is ready for release.
```

## Troubleshooting

If validation fails:

1. **Check the validation log** - Located in the temporary directory
2. **Verify prerequisites** - Ensure all required tools are installed
3. **Check Docker** - Ensure Docker daemon is running
4. **Review port conflicts** - Ensure ports 50051, 9011, 9090, 3000 are available
5. **Check disk space** - Docker builds require sufficient disk space

## Cleanup

The script automatically cleans up all temporary files and Docker containers on exit, even if validation fails.

## Integration with CI/CD

The script returns appropriate exit codes:
- `0` - All validations passed
- `1` - One or more validations failed

This makes it suitable for integration with CI/CD pipelines:

```bash
# In your CI/CD pipeline
./validate_archetype.sh || exit 1
``` 