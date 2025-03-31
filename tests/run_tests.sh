#!/usr/bin/env bash
set -e  # Exit on error

echo "===== Running URL Shortener API Tests ====="

# Ensure test database exists
echo "Creating test database if needed..."
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE urlshortener_test;" || true

# Run the tests with coverage
echo "Running tests with coverage..."
coverage run -m pytest

# Generate coverage report
echo "Generating coverage report..."
coverage report
coverage html

# Summarize results
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | tr -d '%')
echo ""
echo "===== Test Results ====="
echo "Coverage: ${COVERAGE}%"

if (( $(echo "$COVERAGE >= 90" | bc -l) )); then
    echo "✅ Coverage target met! (${COVERAGE}% >= 90%)"
else
    echo "❌ Coverage below target! (${COVERAGE}% < 90%)"
    exit 1
fi

echo ""
echo "Full HTML coverage report available at: htmlcov/index.html"
echo ""