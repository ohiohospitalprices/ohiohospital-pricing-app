#!/usr/bin/env python3
"""
Test suite for Hospital Pricing Search API
Tests /api/search, /api/hospitals, and /api/pricing endpoints
Run: python test_search_api.py
"""

import requests
import json
import time
import sys
from typing import Dict, List

BASE_URL = "http://localhost:5000"
TESTS_PASSED = 0
TESTS_FAILED = 0
RESPONSE_TIMES = []


def print_header(text: str):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)


def test(name: str, condition: bool, details: str = ""):
    """Log test result"""
    global TESTS_PASSED, TESTS_FAILED
    
    status = "✓ PASS" if condition else "✗ FAIL"
    print(f"  {status}: {name}")
    if details:
        print(f"         {details}")
    
    if condition:
        TESTS_PASSED += 1
    else:
        TESTS_FAILED += 1
    
    return condition


class TestSearchAPI:
    """Test suite for Search API endpoint"""
    
    @staticmethod
    def run_all():
        print_header("SEARCH ENDPOINT TESTS (/api/search)")
        
        # Test 1: Basic search
        print("\n[Test 1] Basic procedure search")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=office")
            test("Status 200", response.status_code == 200)
            
            data = response.json()
            test("Has results", 'results' in data)
            test("Has count", 'count' in data, f"Found {data.get('count', 0)} results")
            test("Response time tracked", 'response_time_ms' in data, 
                 f"Response: {data.get('response_time_ms', 'N/A')}ms")
            test("Under 100ms", data.get('response_time_ms', 200) < 100, 
                 f"Actual: {data.get('response_time_ms', 'N/A')}ms")
            
            if data.get('results'):
                first = data['results'][0]
                test("Result has name", 'name' in first, f"Name: {first.get('name')}")
                test("Result has code", 'code' in first)
                test("Result has match_score", 'match_score' in first, 
                     f"Score: {first.get('match_score')}")
                RESPONSE_TIMES.append(data.get('response_time_ms', 0))
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 2: Fuzzy matching - typos
        print("\n[Test 2] Fuzzy matching (typos)")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=offic")  # typo: missing 'e'
            data = response.json()
            test("Typo tolerance", data.get('count', 0) > 0, 
                 f"Found {data.get('count', 0)} results despite typo")
            test("Response time OK", data.get('response_time_ms', 200) < 100)
            RESPONSE_TIMES.append(data.get('response_time_ms', 0))
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 3: Search with limit
        print("\n[Test 3] Search with limit parameter")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=endoscopy&limit=3")
            data = response.json()
            test("Limit respected", len(data.get('results', [])) <= 3, 
                 f"Got {len(data.get('results', []))} results (limit 3)")
            test("Faster with small limit", data.get('response_time_ms', 200) < 100)
            RESPONSE_TIMES.append(data.get('response_time_ms', 0))
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 4: Empty query
        print("\n[Test 4] Validation - empty query")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=")
            test("Returns error", response.status_code == 400, f"Status: {response.status_code}")
            test("Error message", 'error' in response.json())
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 5: Short query
        print("\n[Test 5] Validation - too short query")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=a")
            test("Returns error", response.status_code == 400, f"Status: {response.status_code}")
            test("Error message present", 'error' in response.json())
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 6: Case insensitive
        print("\n[Test 6] Case insensitive search")
        try:
            response1 = requests.get(f"{BASE_URL}/api/search?query=office")
            response2 = requests.get(f"{BASE_URL}/api/search?query=OFFICE")
            test("Same results regardless of case", 
                 response1.json()['count'] == response2.json()['count'])
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 7: Substring matching
        print("\n[Test 7] Substring matching (partial words)")
        try:
            response = requests.get(f"{BASE_URL}/api/search?query=knee")
            data = response.json()
            test("Finds substring matches", data.get('count', 0) > 0)
            # Check if results contain the query
            has_match = any(
                'knee' in r.get('name', '').lower() 
                for r in data.get('results', [])
            )
            test("Results contain query", has_match)
        except Exception as e:
            test("No exception", False, str(e))


class TestHospitalsAPI:
    """Test suite for Hospitals endpoint"""
    
    @staticmethod
    def run_all():
        print_header("HOSPITALS ENDPOINT TESTS (/api/hospitals)")
        
        # Test 1: Get all hospitals
        print("\n[Test 1] Retrieve all hospitals")
        try:
            response = requests.get(f"{BASE_URL}/api/hospitals")
            test("Status 200", response.status_code == 200)
            
            data = response.json()
            test("Has count", 'count' in data)
            test("Exactly 23 hospitals", data.get('count') == 23, 
                 f"Got {data.get('count')} hospitals")
            test("Has hospitals list", 'hospitals' in data)
            test("Response time tracked", 'response_time_ms' in data, 
                 f"Response: {data.get('response_time_ms', 'N/A')}ms")
            test("Very fast (<50ms)", data.get('response_time_ms', 100) < 50, 
                 f"Actual: {data.get('response_time_ms', 'N/A')}ms")
            RESPONSE_TIMES.append(data.get('response_time_ms', 0))
            
            if data.get('hospitals'):
                first = data['hospitals'][0]
                test("Hospital has id", 'id' in first)
                test("Hospital has name", 'name' in first, f"Name: {first.get('name')}")
                test("Hospital has system", 'system' in first, f"System: {first.get('system')}")
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 2: Hospital systems represented
        print("\n[Test 2] Hospital systems distribution")
        try:
            response = requests.get(f"{BASE_URL}/api/hospitals")
            data = response.json()
            
            hospitals = data.get('hospitals', [])
            systems = {}
            for h in hospitals:
                system = h.get('system')
                systems[system] = systems.get(system, 0) + 1
            
            test("OhioHealth present (16)", systems.get('OhioHealth') == 16,
                 f"Count: {systems.get('OhioHealth')}")
            test("Ohio State University present (2)", systems.get('Ohio State University') == 2,
                 f"Count: {systems.get('Ohio State University')}")
            test("Mount Carmel present (5)", systems.get('Mount Carmel') == 5,
                 f"Count: {systems.get('Mount Carmel')}")
        except Exception as e:
            test("No exception", False, str(e))


class TestPricingAPI:
    """Test suite for Pricing endpoint"""
    
    @staticmethod
    def run_all():
        print_header("PRICING ENDPOINT TESTS (/api/pricing)")
        
        # First, get hospitals and procedures for testing
        hospitals = None
        procedures = None
        
        try:
            hosp_response = requests.get(f"{BASE_URL}/api/hospitals")
            hospitals = hosp_response.json().get('hospitals', [])
            
            proc_response = requests.get(f"{BASE_URL}/api/search?query=office&limit=1")
            proc_data = proc_response.json().get('results', [])
            procedures = proc_data
        except Exception as e:
            test("Setup: Get hospitals and procedures", False, str(e))
            return
        
        if not hospitals or not procedures:
            test("Setup: Have test data", False, "Missing hospitals or procedures")
            return
        
        hosp_id = hospitals[0]['id']
        proc_name = procedures[0]['name']
        
        # Test 1: Basic pricing query
        print(f"\n[Test 1] Get pricing for {proc_name} at hospital {hosp_id}")
        try:
            response = requests.get(
                f"{BASE_URL}/api/pricing?procedure={proc_name}&hospital={hosp_id}"
            )
            test("Status 200", response.status_code == 200)
            
            data = response.json()
            test("Has procedure info", 'procedure' in data)
            test("Has selected_hospital", 'selected_hospital' in data)
            test("Has comparison data", 'comparison' in data)
            test("Response time tracked", 'response_time_ms' in data, 
                 f"Response: {data.get('response_time_ms', 'N/A')}ms")
            test("Under 100ms", data.get('response_time_ms', 200) < 100, 
                 f"Actual: {data.get('response_time_ms', 'N/A')}ms")
            RESPONSE_TIMES.append(data.get('response_time_ms', 0))
            
            # Check structure
            if 'selected_hospital' in data:
                sel = data['selected_hospital']
                test("Selected has name", 'name' in sel)
                test("Selected has price", 'price' in sel, f"Price: ${sel.get('price', 0):,.2f}")
            
            if 'comparison' in data:
                comp = data['comparison']
                test("Comparison has count", 'count' in comp, f"Count: {comp.get('count')}")
                test("Comparison has hospitals", 'hospitals' in comp)
                test("Comparison has statistics", 'statistics' in comp)
                
                if 'statistics' in comp:
                    stats = comp['statistics']
                    test("Stats has average_price", 'average_price' in stats, 
                         f"Avg: ${stats.get('average_price', 0):,.2f}")
                    test("Stats has min_price", 'min_price' in stats)
                    test("Stats has max_price", 'max_price' in stats)
                    test("Stats has price_rank", 'price_rank' in stats, 
                         f"Rank: {stats.get('price_rank')}")
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 2: Missing procedure parameter
        print("\n[Test 2] Validation - missing procedure")
        try:
            response = requests.get(f"{BASE_URL}/api/pricing?hospital={hosp_id}")
            test("Returns error", response.status_code == 400)
            test("Error message", 'error' in response.json())
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 3: Missing hospital parameter
        print("\n[Test 3] Validation - missing hospital")
        try:
            response = requests.get(f"{BASE_URL}/api/pricing?procedure={proc_name}")
            test("Returns error", response.status_code == 400)
            test("Error message", 'error' in response.json())
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 4: Invalid hospital ID
        print("\n[Test 4] Validation - invalid hospital ID")
        try:
            response = requests.get(f"{BASE_URL}/api/pricing?procedure={proc_name}&hospital=invalid")
            test("Returns error", response.status_code == 400)
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 5: Nonexistent hospital
        print("\n[Test 5] Validation - nonexistent hospital")
        try:
            response = requests.get(f"{BASE_URL}/api/pricing?procedure={proc_name}&hospital=99999")
            test("Returns 404", response.status_code == 404)
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 6: Fuzzy procedure matching in pricing
        print("\n[Test 6] Fuzzy matching for procedure in pricing")
        try:
            # Use a typo version of the procedure name
            typo_proc = proc_name[:-2] if len(proc_name) > 2 else proc_name
            response = requests.get(
                f"{BASE_URL}/api/pricing?procedure={typo_proc}&hospital={hosp_id}"
            )
            # Should either work or suggest alternatives
            test("Handles typo gracefully", 
                 response.status_code in [200, 404], 
                 f"Status: {response.status_code}")
        except Exception as e:
            test("No exception", False, str(e))
        
        # Test 7: Price comparison completeness
        print("\n[Test 7] Price comparison includes all hospitals")
        try:
            response = requests.get(
                f"{BASE_URL}/api/pricing?procedure={proc_name}&hospital={hosp_id}"
            )
            data = response.json()
            comparison_count = data.get('comparison', {}).get('count', 0)
            test("Comparison count > 0", comparison_count > 0, f"Count: {comparison_count}")
            test("Multiple hospitals in comparison", comparison_count > 1, 
                 f"Found {comparison_count} hospitals")
        except Exception as e:
            test("No exception", False, str(e))


class TestPerformance:
    """Performance tests"""
    
    @staticmethod
    def run_all():
        print_header("PERFORMANCE TESTS")
        
        print("\n[Test 1] Search performance - multiple queries")
        try:
            times = []
            queries = ["office", "mri", "surgery", "endoscopy", "knee"]
            
            for query in queries:
                start = time.time()
                response = requests.get(f"{BASE_URL}/api/search?query={query}")
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                
                test(f"  Query '{query}'", elapsed < 100, f"Time: {elapsed:.2f}ms")
            
            avg_time = sum(times) / len(times)
            test("Average response time", avg_time < 100, f"Average: {avg_time:.2f}ms")
        except Exception as e:
            test("No exception", False, str(e))
        
        print("\n[Test 2] Database consistency")
        try:
            # Get hospitals and procedures
            hosp_response = requests.get(f"{BASE_URL}/api/hospitals")
            hospitals = hosp_response.json().get('hospitals', [])
            
            proc_response = requests.get(f"{BASE_URL}/api/search?query=office")
            procedures = proc_response.json().get('results', [])
            
            # Try getting pricing for random combinations
            success_count = 0
            if hospitals and procedures:
                for i in range(min(3, len(hospitals))):
                    h_id = hospitals[i]['id']
                    p_name = procedures[0]['name']
                    
                    response = requests.get(
                        f"{BASE_URL}/api/pricing?procedure={p_name}&hospital={h_id}"
                    )
                    if response.status_code == 200:
                        success_count += 1
            
            test("Multiple pricing queries work", success_count > 0, f"Success: {success_count}")
        except Exception as e:
            test("No exception", False, str(e))


def main():
    print("\n" + "="*70)
    print("  HOSPITAL PRICING SEARCH API - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Testing: {BASE_URL}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = response.json()
        print(f"✓ Server is running: {data.get('service', 'hospital-pricing-api')}\n")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server!")
        print(f"  Make sure the app is running on {BASE_URL}")
        print("\n  Start with: python api_endpoints.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error checking server: {str(e)}")
        sys.exit(1)
    
    # Run test suites
    TestSearchAPI.run_all()
    TestHospitalsAPI.run_all()
    TestPricingAPI.run_all()
    TestPerformance.run_all()
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"\n  ✓ Passed: {TESTS_PASSED}")
    print(f"  ✗ Failed: {TESTS_FAILED}")
    print(f"  Total:  {TESTS_PASSED + TESTS_FAILED}")
    
    if RESPONSE_TIMES:
        avg_response = sum(RESPONSE_TIMES) / len(RESPONSE_TIMES)
        max_response = max(RESPONSE_TIMES)
        print(f"\n  Response Times:")
        print(f"    Average: {avg_response:.2f}ms")
        print(f"    Max:     {max_response:.2f}ms")
        print(f"    Target:  <100ms")
        print(f"    Status:  {'✓ ACHIEVED' if avg_response < 100 else '✗ NOT MET'}")
    
    print("\n" + "="*70)
    
    if TESTS_FAILED == 0:
        print("  🎉 ALL TESTS PASSED!")
        print("="*70 + "\n")
        return 0
    else:
        print(f"  ⚠️  {TESTS_FAILED} TEST(S) FAILED")
        print("="*70 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
