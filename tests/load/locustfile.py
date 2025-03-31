import random
import string
import time
from locust import HttpUser, task, between
from datetime import datetime, timedelta

class URLShortenerUser(HttpUser):
    """
    Locust load test for URL Shortener API
    
    Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
    """
    
    # Wait between 5-10 seconds between tasks
    wait_time = between(5, 10)
    
    def on_start(self):
        """Set up before starting tests"""
        self.short_codes = []
        self.auth_token = None
        
        # Register a test user
        username = f"loadtest_{random.randint(1000, 9999)}"
        email = f"{username}@example.com"
        
        response = self.client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "loadtest123"
            }
        )
        
        if response.status_code == 200:
            # Login to get auth token
            response = self.client.post(
                "/auth/login",
                data={
                    "username": email,
                    "password": "loadtest123"
                }
            )
            
            if response.status_code == 200:
                self.auth_token = response.json()["access_token"]
                self.auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
    
    def _generate_random_url(self):
        """Generate a random URL for testing"""
        path_length = random.randint(1, 5)
        path_segments = []
        
        for _ in range(path_length):
            segment_length = random.randint(3, 10)
            segment = ''.join(random.choices(string.ascii_lowercase, k=segment_length))
            path_segments.append(segment)
        
        path = '/'.join(path_segments)
        return f"https://example.com/{path}"
    
    @task(5)
    def create_short_link(self):
        """Create a new short link (higher weight)"""
        original_url = self._generate_random_url()
        
        # Randomly decide whether to use authentication
        headers = self.auth_headers if random.random() < 0.7 and self.auth_token else None
        
        # Randomly decide whether to include expiration and custom alias
        json_data = {"original_url": original_url}
        
        if random.random() < 0.3:
            # Add expiration date in 1-30 days
            days = random.randint(1, 30)
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            json_data["expires_at"] = expires_at
        
        if random.random() < 0.2 and headers:
            # Add custom alias (only for authenticated users)
            custom_alias = f"test-{random.randint(10000, 99999)}"
            json_data["custom_alias"] = custom_alias
        
        response = self.client.post("/links/shorten", json=json_data, headers=headers)
        
        if response.status_code == 200:
            # Store short code for later use
            short_code = response.json()["short_code"]
            self.short_codes.append(short_code)
            
            # Limit stored short codes to prevent unbounded growth
            if len(self.short_codes) > 100:
                self.short_codes = self.short_codes[-100:]
    
    @task(10)
    def access_short_link(self):
        """Access (redirect) a short link (highest weight)"""
        if not self.short_codes:
            return
        
        # Select a random short code
        short_code = random.choice(self.short_codes)
        
        # Access the short link
        self.client.get(f"/{short_code}", allow_redirects=False)
    
    @task(3)
    def get_link_info(self):
        """Get link information"""
        if not self.short_codes:
            return
        
        # Select a random short code
        short_code = random.choice(self.short_codes)
        
        # Get link info
        headers = self.auth_headers if random.random() < 0.5 and self.auth_token else None
        self.client.get(f"/links/{short_code}", headers=headers)
    
    @task(2)
    def get_link_stats(self):
        """Get link statistics"""
        if not self.short_codes:
            return
        
        # Select a random short code
        short_code = random.choice(self.short_codes)
        
        # Get link stats
        headers = self.auth_headers if self.auth_token else None
        self.client.get(f"/links/{short_code}/stats", headers=headers)
    
    @task(1)
    def search_links(self):
        """Search for links by original URL"""
        if not self.auth_token:
            return
            
        # Search with a random term
        search_term = random.choice(["example.com", "test", "random"])
        self.client.get(f"/links/search?original_url={search_term}", headers=self.auth_headers)
    
    @task(1)
    def update_link(self):
        """Update a link"""
        if not self.short_codes or not self.auth_token:
            return
            
        # Select a random short code
        short_code = random.choice(self.short_codes)
        
        # Update with new URL
        json_data = {"original_url": self._generate_random_url()}
        
        # Sometimes add expiration
        if random.random() < 0.5:
            days = random.randint(1, 30)
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
            json_data["expires_at"] = expires_at
            
        self.client.put(f"/links/{short_code}", json=json_data, headers=self.auth_headers)
    
    @task(1)
    def delete_link(self):
        """Delete a link"""
        if not self.short_codes or not self.auth_token:
            return
            
        # Select a random short code
        short_code = random.choice(self.short_codes)
        
        # Delete the link
        response = self.client.delete(f"/links/{short_code}", headers=self.auth_headers)
        
        # If successful, remove from our list
        if response.status_code == 200 and short_code in self.short_codes:
            self.short_codes.remove(short_code)