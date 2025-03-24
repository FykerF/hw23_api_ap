import asyncio
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"  # Your locally deployed app URL

def print_response(response, description):
    """Print formatted response details"""
    print(f"\n{'='*40}")
    print(f"{description} - Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*40}\n")

def test_api():
    """Test URL shortener API endpoints"""
    
    # Test 1: Register a user
    print("1. Creating a user")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response(response, "Register User")
    
    # Test 2: Login as the registered user
    print("2. Logging in")
    login_data = {
        "username": "test@example.com",  # We're using email for login
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print_response(response, "Login")
    
    try:
        access_token = response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
    except:
        print("Error getting access token. Using empty auth headers.")
        auth_headers = {}
    
    # Test 3: Create a short link (authenticated)
    print("3. Creating a short link (authenticated)")
    link_data = {
        "original_url": "https://example.com/very/long/url/that/needs/shortening",
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }
    response = requests.post(f"{BASE_URL}/links/shorten", json=link_data, headers=auth_headers)
    print_response(response, "Create Short Link")
    
    try:
        short_code = response.json()["short_code"]
        short_url = response.json()["short_url"]
        print(f"Generated short URL: {short_url}")
    except:
        short_code = "unknown"
        print("Error getting short code")
    
    # Test 4: Create a short link with custom alias
    print("4. Creating a short link with custom alias")
    link_data = {
        "original_url": "https://example.com/customized/url",
        "custom_alias": "mytest"
    }
    response = requests.post(f"{BASE_URL}/links/shorten", json=link_data, headers=auth_headers)
    print_response(response, "Create Short Link with Custom Alias")
    
    # Test 5: Get link information
    print(f"5. Getting link info for code: {short_code}")
    response = requests.get(f"{BASE_URL}/links/{short_code}", headers=auth_headers)
    print_response(response, "Get Link Info")
    
    # Test 6: Get link statistics
    print(f"6. Getting link statistics for code: {short_code}")
    response = requests.get(f"{BASE_URL}/links/{short_code}/stats", headers=auth_headers)
    print_response(response, "Get Link Statistics")
    
    # Test 7: Search for links
    print("7. Searching for links")
    response = requests.get(f"{BASE_URL}/links/search?original_url=example.com", headers=auth_headers)
    print_response(response, "Search Links")
    
    # Test 8: Follow a redirect
    print(f"8. Testing redirect for: {short_code}")
    response = requests.get(f"{BASE_URL}/{short_code}", allow_redirects=False)
    print_response(response, "Redirect")
    
    # Test 9: Update a link
    print(f"9. Updating link for code: {short_code}")
    update_data = {
        "original_url": "https://example.com/updated/url"
    }
    response = requests.put(f"{BASE_URL}/links/{short_code}", json=update_data, headers=auth_headers)
    print_response(response, "Update Link")
    
    # Test 10: Get link info after update
    print(f"10. Getting link info after update for code: {short_code}")
    response = requests.get(f"{BASE_URL}/links/{short_code}", headers=auth_headers)
    print_response(response, "Get Link Info After Update")
    
    # Test 11: Create anonymous link (no auth)
    print("11. Creating anonymous link")
    anon_link_data = {
        "original_url": "https://example.com/anonymous/link"
    }
    response = requests.post(f"{BASE_URL}/links/shorten", json=anon_link_data)
    print_response(response, "Create Anonymous Link")
    
    try:
        anon_short_code = response.json()["short_code"]
    except:
        anon_short_code = "unknown"
        
    # Test 12: Delete a link
    print(f"12. Deleting link with code: {short_code}")
    response = requests.delete(f"{BASE_URL}/links/{short_code}", headers=auth_headers)
    print_response(response, "Delete Link")
    
    # Test 13: Check that link was deleted
    print(f"13. Checking that link was deleted for code: {short_code}")
    response = requests.get(f"{BASE_URL}/links/{short_code}", headers=auth_headers)
    print_response(response, "Get Deleted Link")

if __name__ == "__main__":
    test_api()