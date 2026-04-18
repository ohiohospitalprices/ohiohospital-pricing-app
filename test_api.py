#!/usr/bin/env python3
"""
Test suite for Hospital Pricing API
Run this after starting app.py to verify functionality
"""

import requests
import json
from typing import Dict, Optional
import sys

BASE_URL = "http://localhost:5000"
TESTS_PASSED = 0
TESTS_FAILED = 0


def print_test(name: str):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)


def check_response(response: requests.Response, expected_status: int = 200) -> bool:
    """Check HTTP response status"""
    if response.status_code == expected_status:
        print(f"✓ Status {response.status_code}")
        return True
    else:
        print(f"✗ Expected {expected_status}, got {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False


def test_health():
    """Test health check endpoint"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if check_response(response):
            data = response.json()
            print(f"✓ Response: {json.dumps(data, indent=2)}")
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_search_basic():
    """Test basic search"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Search - Basic Query")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search?query=cardiac")
        if check_response(response):
            data = response.json()
            print(f"✓ Found {data.get('count', 0)} results")
            if data.get('results'):
                print(f"✓ First result: {data['results'][0]['procedure_name']}")
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_search_with_hospital():
    """Test search with hospital filter"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Search - With Hospital Filter")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search?query=surgery&hospital=riverside&limit=5")
        if check_response(response):
            data = response.json()
            print(f"✓ Found {data.get('count', 0)} results matching hospital")
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_search_short_query():
    """Test search with invalid short query"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Search - Invalid Query (Too Short)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search?query=a")
        if response.status_code == 400:
            print(f"✓ Correctly rejected short query")
            TESTS_PASSED += 1
        else:
            print(f"✗ Should return 400 for short query, got {response.status_code}")
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_comparison():
    """Test price comparison endpoint"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Price Comparison - By Procedure Code")
    
    try:
        # First, search to find a procedure code
        search_response = requests.get(f"{BASE_URL}/api/search?query=surgery&limit=1")
        
        if search_response.status_code != 200 or not search_response.json().get('results'):
            print("! Skipping: No procedures in database yet")
            return
        
        proc_code = search_response.json()['results'][0]['procedure_code']
        
        # Now compare
        response = requests.get(f"{BASE_URL}/api/compare?procedure={proc_code}")
        if check_response(response):
            data = response.json()
            proc_name = data['procedure']['name']
            avg_price = data['statistics']['average_price']
            hosp_count = data['statistics']['hospital_count']
            
            print(f"✓ Procedure: {proc_name}")
            print(f"✓ Average price: ${avg_price:,.2f}")
            print(f"✓ Hospitals with this procedure: {hosp_count}")
            
            if data.get('all_hospitals'):
                print(f"✓ Price range: ${data['statistics']['minimum_price']:,.2f} - ${data['statistics']['maximum_price']:,.2f}")
            
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_comparison_with_hospital():
    """Test comparison with hospital selection"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Price Comparison - With Hospital Selection")
    
    try:
        response = requests.get(f"{BASE_URL}/api/compare?procedure=cardiac&hospital=riverside")
        if check_response(response):
            data = response.json()
            selected = data.get('selected_hospital')
            if selected:
                print(f"✓ Selected hospital: {selected}")
                print(f"✓ Price at selected: ${data.get('selected_price', 0):,.2f}")
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_hospitals_list():
    """Test hospitals list endpoint"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("List Hospitals")
    
    try:
        response = requests.get(f"{BASE_URL}/api/hospitals")
        if check_response(response):
            data = response.json()
            count = data.get('count', 0)
            print(f"✓ Total hospitals: {count}")
            
            if data.get('hospitals') and len(data['hospitals']) > 0:
                print(f"✓ Sample hospitals:")
                for h in data['hospitals'][:3]:
                    print(f"  - {h['name']}")
            
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_statistics():
    """Test statistics endpoint"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Database Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if check_response(response):
            data = response.json()['statistics']
            print(f"✓ Total procedures: {data.get('total_procedures', 0):,}")
            print(f"✓ Total hospitals: {data.get('total_hospitals', 0)}")
            print(f"✓ Total pricing records: {data.get('total_pricing_records', 0):,}")
            print(f"✓ Last updated: {data.get('last_updated', 'N/A')}")
            TESTS_PASSED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_invalid_endpoint():
    """Test 404 error handling"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Error Handling - 404")
    
    try:
        response = requests.get(f"{BASE_URL}/api/nonexistent")
        if response.status_code == 404:
            print(f"✓ Correctly returned 404")
            TESTS_PASSED += 1
        else:
            print(f"✗ Expected 404, got {response.status_code}")
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def test_search_limit():
    """Test search with limit parameter"""
    global TESTS_PASSED, TESTS_FAILED
    print_test("Search - With Limit Parameter")
    
    try:
        response = requests.get(f"{BASE_URL}/api/search?query=surgery&limit=5")
        if check_response(response):
            data = response.json()
            results_count = len(data.get('results', []))
            if results_count <= 5:
                print(f"✓ Limit respected: {results_count} results (limit 5)")
                TESTS_PASSED += 1
            else:
                print(f"✗ Limit not respected: got {results_count} results")
                TESTS_FAILED += 1
        else:
            TESTS_FAILED += 1
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        TESTS_FAILED += 1


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("HOSPITAL PRICING API - TEST SUITE")
    print("="*60)
    print(f"Testing: {BASE_URL}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server!")
        print(f"  Make sure the app is running on {BASE_URL}")
        print("\n  Start the app with: python app.py")
        sys.exit(1)
    
    # Run tests
    test_health()
    test_search_basic()
    test_search_with_hospital()
    test_search_short_query()
    test_search_limit()
    test_hospitals_list()
    test_statistics()
    test_comparison()
    test_comparison_with_hospital()
    test_invalid_endpoint()
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"✓ Passed: {TESTS_PASSED}")
    print(f"✗ Failed: {TESTS_FAILED}")
    print(f"Total:  {TESTS_PASSED + TESTS_FAILED}")
    
    if TESTS_FAILED == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {TESTS_FAILED} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
