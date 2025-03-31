import asyncio
import time
import statistics
import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch
import uuid

from core.redis_client import cache_link, delete_cached_link

async def measure_request_time(client, url, **kwargs):
    """Measure request execution time in milliseconds"""
    start_time = time.time()
    response = await client.get(url, **kwargs)
    end_time = time.time()
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return response, execution_time

@pytest.mark.asyncio
async def test_redirect_performance_with_caching(client: AsyncClient):
    """Compare performance of redirects with and without caching"""
    # Create test links
    original_url = f"https://example.com/performance-test-{uuid.uuid4().hex}"
    response = await client.post(
        "/links/shorten", 
        json={"original_url": original_url}
    )
    
    assert response.status_code == status.HTTP_200_OK
    short_code = response.json()["short_code"]
    
    # Clear cache to start fresh
    await delete_cached_link(short_code)
    
    # Measure uncached performance
    uncached_times = []
    for _ in range(5):
        # Clear cache before each request
        await delete_cached_link(short_code)
        
        # Make request and measure time
        response, execution_time = await measure_request_time(
            client, f"/{short_code}", follow_redirects=False
        )
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        uncached_times.append(execution_time)
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)
    
    # Measure cached performance
    # First prime the cache
    await client.get(f"/{short_code}", follow_redirects=False)
    
    cached_times = []
    for _ in range(5):
        # Make request and measure time
        response, execution_time = await measure_request_time(
            client, f"/{short_code}", follow_redirects=False
        )
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        cached_times.append(execution_time)
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)
    
    # Calculate statistics
    avg_uncached = statistics.mean(uncached_times)
    avg_cached = statistics.mean(cached_times)
    
    med_uncached = statistics.median(uncached_times)
    med_cached = statistics.median(cached_times)
    
    # Print results
    print(f"\nRedirect Performance Results:")
    print(f"Uncached: avg={avg_uncached:.2f}ms, median={med_uncached:.2f}ms")
    print(f"Cached: avg={avg_cached:.2f}ms, median={med_cached:.2f}ms")
    print(f"Speed improvement: {((avg_uncached - avg_cached) / avg_uncached * 100):.2f}%")
    
    # Assert that cached is faster
    assert avg_cached < avg_uncached, "Cached redirects should be faster than uncached redirects"

@pytest.mark.asyncio
async def test_concurrent_redirect_performance(client: AsyncClient):
    """Test performance under concurrent load"""
    # Create test links
    original_url = f"https://example.com/concurrent-test-{uuid.uuid4().hex}"
    response = await client.post(
        "/links/shorten", 
        json={"original_url": original_url}
    )
    
    assert response.status_code == status.HTTP_200_OK
    short_code = response.json()["short_code"]
    
    # Clear cache to start fresh
    await delete_cached_link(short_code)
    
    # Function to make a single request
    async def make_redirect_request():
        start_time = time.time()
        response = await client.get(f"/{short_code}", follow_redirects=False)
        end_time = time.time()
        return (end_time - start_time) * 1000  # ms
    
    # Make concurrent requests (first batch uncached)
    concurrency = 10
    uncached_tasks = [make_redirect_request() for _ in range(concurrency)]
    uncached_times = await asyncio.gather(*uncached_tasks)
    
    # Wait a moment
    await asyncio.sleep(0.5)
    
    # Make concurrent requests (second batch should be cached)
    cached_tasks = [make_redirect_request() for _ in range(concurrency)]
    cached_times = await asyncio.gather(*cached_tasks)
    
    # Calculate statistics
    avg_uncached = statistics.mean(uncached_times)
    avg_cached = statistics.mean(cached_times)
    
    # Print results
    print(f"\nConcurrent Redirect Performance Results (concurrency={concurrency}):")
    print(f"Uncached: avg={avg_uncached:.2f}ms")
    print(f"Cached: avg={avg_cached:.2f}ms")
    print(f"Speed improvement: {((avg_uncached - avg_cached) / avg_uncached * 100):.2f}%")
    
    # Assert that cached is faster
    assert avg_cached < avg_uncached, "Cached concurrent redirects should be faster than uncached"

@pytest.mark.asyncio
@patch('core.redis_client.redis_client', None)  # Simulate Redis unavailable
async def test_performance_without_redis(client: AsyncClient):
    """Test performance when Redis is unavailable"""
    # Create test link
    original_url = f"https://example.com/no-redis-test-{uuid.uuid4().hex}"
    response = await client.post(
        "/links/shorten", 
        json={"original_url": original_url}
    )
    
    assert response.status_code == status.HTTP_200_OK
    short_code = response.json()["short_code"]
    
    # Measure performance with Redis unavailable
    times = []
    for _ in range(5):
        # Make request and measure time
        response, execution_time = await measure_request_time(
            client, f"/{short_code}", follow_redirects=False
        )
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        times.append(execution_time)
        
        # Small delay
        await asyncio.sleep(0.1)
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    med_time = statistics.median(times)
    
    # Print results
    print(f"\nPerformance Without Redis:")
    print(f"Average: {avg_time:.2f}ms")
    print(f"Median: {med_time:.2f}ms")
    
    # The test passes as long as requests complete successfully
    # We're just measuring performance without Redis