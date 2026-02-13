"""Quick test script for the API"""
import requests
import base64

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_db_stats():
    """Test database stats endpoint"""
    print("\n=== Testing Database Stats ===")
    response = requests.get(f"{BASE_URL}/api/db/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_simple_search():
    """Test simple search without documents"""
    print("\n=== Testing Simple Search ===")
    payload = {
        "query": "What is Python programming?",
        "search_mode": "local",
        "internal_mode": True
    }
    response = requests.post(f"{BASE_URL}/api/search", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    print(f"Sources: {len(result.get('sources', []))}")
    return response.status_code == 200

def test_search_with_document():
    """Test search with base64 document"""
    print("\n=== Testing Search with Base64 Document ===")
    
    # Create a sample document
    sample_text = """
    Python is a high-level, interpreted programming language.
    It was created by Guido van Rossum and first released in 1991.
    Python emphasizes code readability and simplicity.
    """
    
    # Encode to base64
    encoded = base64.b64encode(sample_text.encode()).decode()
    
    payload = {
        "query": "Tell me about Python",
        "documents": [
            {
                "filename": "python_info.txt",
                "content": encoded
            }
        ],
        "search_mode": "local",
        "internal_mode": False
    }
    
    response = requests.post(f"{BASE_URL}/api/search", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Sources: {len(result.get('sources', []))}")
    if result.get('summary'):
        print(f"Summary: {result['summary'][:200]}...")
    return response.status_code == 200

def test_document_upload():
    """Test document upload to database"""
    print("\n=== Testing Document Upload ===")
    
    sample_text = "This is a test document for the vector database."
    encoded = base64.b64encode(sample_text.encode()).decode()
    
    payload = {
        "documents": [
            {
                "filename": "test_doc.txt",
                "content": encoded
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/db/upload", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("AI Search API - Quick Test Suite")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the API is running: python -m uvicorn src.api:app --reload")
    
    try:
        # Run tests
        results = {
            "Health Check": test_health(),
            "Database Stats": test_db_stats(),
            "Simple Search": test_simple_search(),
            "Search with Document": test_search_with_document(),
            "Document Upload": test_document_upload()
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API")
        print("Make sure the API server is running:")
        print("  python -m uvicorn src.api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
