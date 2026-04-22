#!/bin/bash

# Hospital Pricing App - Deployment Verification Script
# Tests the deployed application at: https://ohiohospital-pricing-app-1.onrender.com

APP_URL="https://ohiohospital-pricing-app-1.onrender.com"
TESTS_PASSED=0
TESTS_FAILED=0

echo "========================================"
echo "Hospital Pricing App - Deployment Tests"
echo "========================================"
echo "Testing: $APP_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -n "Testing: $description... "
    
    response=$(curl -s -w "\n%{http_code}" "$APP_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}OK${NC} (HTTP 200)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "  Response: $body" | head -c 100
        echo ""
    else
        echo -e "${RED}FAILED${NC} (HTTP $http_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "  Response: $body"
    fi
    echo ""
}

# Test 1: Homepage
echo "1. Testing Homepage..."
response=$(curl -s -w "\n%{http_code}" "$APP_URL/")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Homepage loads${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Homepage failed${NC} (HTTP $http_code)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 2: Health Check
echo "2. Testing Health Check Endpoint..."
response=$(curl -s "$APP_URL/api/health")
if echo "$response" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    procedures_count=$(echo "$response" | grep -o '"procedures_count":[0-9]*' | grep -o '[0-9]*')
    echo "  Procedures in database: $procedures_count"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "  Response: $response"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3: Search API
echo "3. Testing Search API..."
response=$(curl -s "$APP_URL/api/search?q=hospital")
if echo "$response" | grep -q '"results"'; then
    echo -e "${GREEN}✓ Search API works${NC}"
    count=$(echo "$response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1)
    echo "  Results found: $count"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Search API failed${NC}"
    echo "  Response: $response"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: Hospitals List
echo "4. Testing Hospitals List..."
response=$(curl -s "$APP_URL/api/hospitals")
if echo "$response" | grep -q '"hospitals"'; then
    echo -e "${GREEN}✓ Hospitals endpoint works${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Hospitals endpoint failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 5: Procedures List
echo "5. Testing Procedures List..."
response=$(curl -s "$APP_URL/api/procedures")
if echo "$response" | grep -q '"procedures"'; then
    echo -e "${GREEN}✓ Procedures endpoint works${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Procedures endpoint failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Summary
echo "========================================"
echo "Test Summary:"
echo "========================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo "Deployment is successful."
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo "Please review the failures above."
    exit 1
fi
